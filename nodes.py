"""Node functions for the CV generation workflow.

This module contains stateless node functions that orchestrate the workflow.
Following the constitutional rules, nodes take AppState as input and return
a Python dictionary as output. They must not have side effects.
"""
# pylint: disable=logging-fstring-interpolation
# pylint: disable=line-too-long

import logging
from typing import Dict, Any
from chains import (
    create_job_description_parsing_chain,
    create_cv_parsing_chain,
    create_key_qualifications_chain,
    create_executive_summary_chain,
    create_experience_tailoring_chain,
    create_projects_tailoring_chain,
    create_section_mapping_chain,
)
from state import AppState

# Configure logging
logger = logging.getLogger(__name__)


def parse_job_description_node(state: AppState) -> Dict[str, Any]:
    """Parse the raw job description into structured data."""
    logger.info("Starting job description parsing node")

    if "raw_job_description" not in state:
        logger.error("raw_job_description key not found in state")
        return {
            "error_message": "Failed to parse job description: raw_job_description key not found in state"
        }

    try:
        chain = create_job_description_parsing_chain()
        result = chain.invoke({"job_description": state["raw_job_description"]})

        logger.info(
            f"Job description parsing successful. Job title: {result.job_title}"
        )
        return {
            "job_description_data": result,
            "current_step": "job_description_parsed",
        }
    except Exception as e:
        logger.error(f"Job description parsing failed: {str(e)}")
        return {"error_message": f"Failed to parse job description: {str(e)}"}


def parse_cv_node(state: AppState) -> Dict[str, Any]:
    """Parse the raw CV text into structured format."""
    logger.info("Starting CV parsing node")

    if "raw_cv_text" not in state:
        logger.error("raw_cv_text key not found in state")
        return {
            "error_message": "Failed to parse CV: raw_cv_text key not found in state"
        }

    try:
        chain = create_cv_parsing_chain()
        result = chain.invoke({"cv_text": state["raw_cv_text"]})

        logger.info(
            f"CV parsing successful. Candidate: {result.personal_info['name'] if result.personal_info and 'name' in result.personal_info else 'Unknown'}"
        )
        return {"tailored_cv": result, "current_step": "cv_parsed"}
    except Exception as e:
        logger.error(f"CV parsing failed: {str(e)}")
        return {
            "error_message": f"CV parsing failed: {str(e)}. Please check the CV format and try again.",
            "human_review_required": True,
            "current_step": "cv_parsing_failed",
        }


def setup_iterative_session_node(state: AppState) -> Dict[str, Any]:
    """Setup the iterative session by initializing source_cv, tailored_cv, and experience_index.

    This node addresses the architectural flaw where source_cv was never created after
    parsing the initial CV. It deep copies structured_cv to source_cv, initializes
    tailored_cv and experience_index, and removes the original structured_cv key.
    """
    logger.info("Starting iterative session setup node")

    try:
        import copy

        if "tailored_cv" not in state:
            logger.error("tailored_cv key not found in state for session setup")
            return {"error_message": "Failed to setup iterative session: tailored_cv not found."}

        # Create the read-only backup from the initial tailored_cv
        source_cv = copy.deepcopy(state["tailored_cv"])
        experience_index = 0

        logger.info("Iterative session setup successful")
        return {
            "source_cv": source_cv,
            "experience_index": experience_index,
            "current_step": "iterative_session_ready",
        }
    except Exception as e:
        logger.error(f"Iterative session setup failed: {str(e)}")
        return {"error_message": f"Failed to setup iterative session: {str(e)}"}


def map_source_sections_node(state: AppState) -> dict:
    """Analyzes the source_cv to map concepts to section indices."""
    logger.info("Starting source section mapping node")
    try:
        import json

        source_cv = state.get("source_cv")
        if not source_cv:
            return {"error_message": "Source CV not found for section mapping."}

        # Convert the Pydantic model to a JSON string for the prompt
        source_cv_json = source_cv.model_dump_json(indent=2)

        chain = create_section_mapping_chain()
        section_map = chain.invoke({"source_cv_json": source_cv_json})

        logger.info(f"Section mapping successful: {section_map}")
        return {
            "section_map": section_map,
            "current_step": "source_sections_mapped"
        }
    except Exception as e:
        logger.error(f"Source section mapping failed: {str(e)}")
        return {"error_message": f"Source section mapping failed: {str(e)}"}


def generate_key_qualifications_node(state: AppState) -> Dict[str, Any]:
    """Generate key qualifications and add them directly to the tailored_cv as a new section.

    This implements the living document pattern where tailored_cv is progressively enriched.
    Handles regeneration when human_approved=False.
    """
    logger.info("Starting key qualifications generation node")
    try:
        # Check if required data exists
        job_data = state.get("job_description_data")
        cv_data = state.get("tailored_cv")  # Use tailored_cv instead of structured_cv

        if not job_data or not cv_data:
            logger.error(
                f"Missing required data. Job data: {job_data is not None}, CV data: {cv_data is not None}"
            )
            return {
                "error_message": "Missing parsed job description or CV data. Please ensure both inputs are provided and parsed successfully."
            }

        # If this is a regeneration (human_approved=False), remove existing qualifications
        if state.get("human_approved") == False:
            logger.info("Regenerating qualifications based on user feedback")
            cv_data = cv_data.model_copy(deep=True)
            cv_data.sections = [s for s in cv_data.sections if "qualifications" not in s.name.lower()]

        # Extract skills from CV sections (looking for skills/technologies in entries)
        current_skills = []
        for section in cv_data.sections:
            for entry in section.entries:
                current_skills.extend(entry.tags)

        # Prepare job requirements from the new model structure
        required_skills = [
            skill.name for skill in job_data.technical_skills if skill.is_required
        ]
        preferred_skills = [
            skill.name for skill in job_data.technical_skills if not skill.is_required
        ]

        job_requirements = {
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "key_responsibilities": job_data.key_responsibilities,
        }

        chain = create_key_qualifications_chain()

        # Include human feedback if this is a regeneration
        chain_input = {
            "job_requirements": str(job_requirements),
            "current_skills": str(current_skills),
        }

        if state.get("human_approved") == False and state.get("human_feedback"):
            chain_input["human_feedback"] = state["human_feedback"]
            logger.info(f"Including human feedback in regeneration: {state['human_feedback'][:100]}...")

        result = chain.invoke(chain_input)

        # LIVING DOCUMENT PATTERN: Add qualifications directly to tailored_cv
        from models import Section, CVEntry

        # Create CVEntry objects for each qualification
        qualification_entries = [
            CVEntry(
                title=qualification, subtitle=None, date_range=None, details=[], tags=[]
            )
            for qualification in result.qualifications
        ]

        # Create new Key Qualifications section
        qualifications_section = Section(
            name="Key Qualifications", entries=qualification_entries
        )

        # Create updated CV with the new section at the beginning
        updated_cv = cv_data.model_copy(deep=True)
        updated_cv.sections.insert(0, qualifications_section)

        logger.info(
            f"Key qualifications generation successful. Added {len(result.qualifications)} qualifications to tailored_cv"
        )

        return {
            "tailored_cv": updated_cv,  # Update tailored_cv instead of structured_cv
            "current_step": "awaiting_qualifications_review",
            "human_approved": None,  # Clear the approval flag
            "human_feedback": None,  # Clear the feedback
        }
    except Exception as e:
        logger.error(f"Key qualifications generation failed: {str(e)}")
        return {"error_message": f"Failed to generate key qualifications: {str(e)}"}


def request_human_review_node(state: AppState) -> Dict[str, Any]:
    """Request human review of generated key qualifications."""
    # Get qualifications from tailored_cv
    cv_data = state.get("tailored_cv")
    qualifications_content = ""
    if cv_data:
        for section in cv_data.sections:
            if "qualifications" in section.name.lower():
                qualifications_content = "\n".join(
                    [f"• {entry.title}" for entry in section.entries]
                )
                break
    if qualifications_content:
        review_content = qualifications_content
    else:
        review_content = "No qualifications generated yet."

    return {
        "human_review_required": True,
        "human_feedback": review_content,
        "current_step": "awaiting_human_review",
    }


def tailor_experience_node(state: AppState) -> Dict[str, Any]:
    """Tailor one work experience entry at a time using iterative processing.

    This implements the new iterative workflow where we process one experience entry
    at a time, allowing for granular control and review.
    """
    logger.info("Starting iterative experience tailoring node")

    try:
        # Initialize workbench if this is the first run
        if state["source_cv"] is None:
            state["source_cv"] = state["tailored_cv"]
            state["tailored_cv"] = state["tailored_cv"].model_copy(deep=True)
            # Clear experience entries in tailored_cv to build them iteratively
            for section in state["tailored_cv"].sections:
                if section.name == "Experience":
                    section.entries = []

        # Extract qualifications from the enriched CV for context
        qualifications_context = []
        for section in state["source_cv"].sections:
            if "qualifications" in section.name.lower():
                qualifications_context = [entry.title for entry in section.entries]
                break

        # Find the experience section in source CV
        source_experience_entries = []
        for section in state["source_cv"].sections:
            if section.name == "Experience":
                source_experience_entries = section.entries
                break

        # Check if we have more entries to process
        current_index = state["experience_index"]
        if current_index >= len(source_experience_entries):
            logger.info("All experience entries have been processed")
            return {
                "tailored_cv": state["tailored_cv"],
                "current_step": "experience_tailoring_complete",
            }

        # Get the current entry to process
        current_entry = source_experience_entries[current_index]

        # Check if user wants to skip this entry (keep original)
        if state.get("user_intent") == "skip":
            logger.info(f"User chose to skip entry {current_index + 1}, keeping original")
            tailored_entry = current_entry  # Use original entry as-is
        else:
            # Tailor the current entry
            chain = create_experience_tailoring_chain()
            result = chain.invoke(
                {
                    "job_description": state["raw_job_description"],
                    "current_entry": {
                        "title": current_entry.title,
                        "subtitle": current_entry.subtitle,
                        "date_range": current_entry.date_range,
                        "details": current_entry.details,
                        "tags": current_entry.tags,
                    },
                    "key_qualifications": str(qualifications_context),
                }
            )
            tailored_entry = result.tailored_entry

        # Functional approach: Create new StructuredCV with updated Experience section

        # Find existing Experience section or create new one
        experience_section = None
        other_sections = []

        for section in state["tailored_cv"].sections:
            if section.name == "Experience":
                experience_section = section
            else:
                other_sections.append(section)

        # Create new Experience section with the tailored entry added
        from models import Section, StructuredCV

        if experience_section is None:
            # No existing Experience section - create new one
            new_experience_section = Section(
                name="Experience", entries=[tailored_entry]
            )
        else:
            # Check if this is a revision (entry already exists at current index)
            if current_index < len(experience_section.entries):
                # This is a revision - replace the existing entry
                new_entries = experience_section.entries.copy()
                new_entries[current_index] = tailored_entry
                logger.info(f"Replacing existing entry at index {current_index} during revision")
            else:
                # This is first-time generation - append the new entry
                new_entries = experience_section.entries + [tailored_entry]
                logger.info(f"Appending new entry at index {current_index}")

            new_experience_section = Section(name="Experience", entries=new_entries)

        # Create new StructuredCV with updated sections
        new_sections = other_sections + [new_experience_section]
        new_tailored_cv = StructuredCV(
            personal_info=state["tailored_cv"].personal_info, sections=new_sections
        )

        logger.info(
            f"Experience entry {current_index + 1} processed successfully: {tailored_entry.title}"
        )
        return {
            "tailored_cv": new_tailored_cv,
            "current_step": "experience_entry_tailored",
            "user_intent": None,  # Clear the user intent flag
        }
    except Exception as e:
        logger.error(f"Experience tailoring failed: {str(e)}")
        return {
            "error_message": f"Failed to tailor experience entry: {str(e)}",
            "current_step": "experience_tailoring_failed",
        }


def should_continue_experience_node(state: AppState) -> Dict[str, Any]:
    """Decision node to determine if we should continue processing experience entries.

    This node checks if there are more experience entries to process and routes
    the workflow accordingly.
    """
    logger.info("Checking if more experience entries need processing")

    try:
        # Get source experience entries count
        source_experience_count = 0
        if state["source_cv"] is not None:
            for section in state["source_cv"].sections:
                if section.name == "Experience":
                    source_experience_count = len(section.entries)
                    break

        current_index = state["experience_index"]

        if current_index < source_experience_count:
            logger.info(
                f"More experience entries to process: {current_index}/{source_experience_count}"
            )
            return {
                "current_step": "awaiting_experience_review",
                "experience_index": current_index  # Explicitly pass the index back
            }
        else:
            logger.info("All experience entries processed, experience tailoring complete")
            return {
                "tailored_cv": state["tailored_cv"],
                "current_step": "experience_tailoring_complete",
                "project_index": 0,  # Initialize project_index for next phase
                "experience_index": current_index  # Explicitly pass the final index
            }
    except Exception as e:
        logger.error(f"Experience tailoring failed: {str(e)}")
        return {
            "error_message": f"Failed to tailor experience: {str(e)}",
            "current_step": "experience_tailoring_failed",
        }


def tailor_project_entry_node(state: AppState) -> Dict[str, Any]:
    """Tailor one project entry at a time using iterative processing.

    This implements the new iterative workflow where we process one project entry
    at a time, allowing for granular control and review.
    """
    logger.info("Starting iterative project tailoring node")

    try:
        # Initialize workbench if this is the first run
        if state["source_cv"] is None:
            state["source_cv"] = state["tailored_cv"]
            state["tailored_cv"] = state["tailored_cv"].model_copy(deep=True)
            # Clear project entries in tailored_cv to build them iteratively
            for section in state["tailored_cv"].sections:
                if section.name == "Projects":
                    section.entries = []

        # Extract qualifications from the enriched CV for context
        qualifications_context = []
        for section in state["source_cv"].sections:
            if "qualifications" in section.name.lower():
                qualifications_context = [entry.title for entry in section.entries]
                break

        # Find the projects section in source CV
        source_project_entries = []
        for section in state["source_cv"].sections:
            if section.name == "Projects":
                source_project_entries = section.entries
                break

        # Check if we have more entries to process
        current_index = state.get("project_index", 0)
        if current_index >= len(source_project_entries):
            logger.info("All project entries have been processed")
            return {
                "tailored_cv": state["tailored_cv"],
                "current_step": "projects_tailoring_complete",
            }

        # Get the current entry to process
        current_entry = source_project_entries[current_index]

        # Check if user wants to skip this entry (keep original)
        if state.get("user_intent") == "skip":
            logger.info(f"User chose to skip entry {current_index + 1}, keeping original")
            tailored_entry = current_entry  # Use original entry as-is
        else:
            # Tailor the current entry
            chain = create_projects_tailoring_chain()
            result = chain.invoke(
                {
                    "job_description": state["raw_job_description"],
                    "current_entry": {
                        "title": current_entry.title,
                        "subtitle": current_entry.subtitle,
                        "date_range": current_entry.date_range,
                        "details": current_entry.details,
                        "tags": current_entry.tags,
                    },
                    "key_qualifications": str(qualifications_context),
                }
            )
            tailored_entry = result.tailored_entry

        # Functional approach: Create new StructuredCV with updated Projects section

        # Find existing Projects section or create new one
        projects_section = None
        other_sections = []

        for section in state["tailored_cv"].sections:
            if section.name == "Projects":
                projects_section = section
            else:
                other_sections.append(section)

        # Create new Projects section with the tailored entry added
        from models import Section, StructuredCV

        if projects_section is None:
            # No existing Projects section - create new one
            new_projects_section = Section(
                name="Projects", entries=[tailored_entry]
            )
        else:
            # Check if this is a revision (entry already exists at current index)
            if current_index < len(projects_section.entries):
                # This is a revision - replace the existing entry
                new_entries = projects_section.entries.copy()
                new_entries[current_index] = tailored_entry
                logger.info(f"Replacing existing entry at index {current_index} during revision")
            else:
                # This is first-time generation - append the new entry
                new_entries = projects_section.entries + [tailored_entry]
                logger.info(f"Appending new entry at index {current_index}")

            new_projects_section = Section(name="Projects", entries=new_entries)

        # Create new StructuredCV with updated sections
        new_sections = other_sections + [new_projects_section]
        new_tailored_cv = StructuredCV(
            personal_info=state["tailored_cv"].personal_info, sections=new_sections
        )

        logger.info(
            f"Project entry {current_index + 1} processed successfully: {tailored_entry.title}"
        )
        return {
            "tailored_cv": new_tailored_cv,
            "current_step": "project_entry_tailored",
            "user_intent": None,  # Clear the user intent flag
        }
    except Exception as e:
        logger.error(f"Project tailoring failed: {str(e)}")
        return {
            "error_message": f"Failed to tailor project entry: {str(e)}",
            "current_step": "project_tailoring_failed",
        }


def should_continue_projects_node(state: AppState) -> Dict[str, Any]:
    """Decision node to determine if we should continue processing project entries.

    This node checks if there are more project entries to process and routes
    the workflow accordingly.
    """
    logger.info("Checking if more project entries need processing")

    try:
        # Get source project entries count
        source_project_count = 0
        if state["source_cv"] is not None:
            for section in state["source_cv"].sections:
                if section.name == "Projects":
                    source_project_count = len(section.entries)
                    break

        current_index = state.get("project_index", 0)

        if current_index < source_project_count:
            logger.info(
                f"More project entries to process: {current_index}/{source_project_count}"
            )
            return {
                "current_step": "awaiting_project_review",
                "project_index": current_index,
            }
        else:
            logger.info("All project entries processed, projects tailoring complete")
            return {
                "tailored_cv": state["tailored_cv"],
                "current_step": "start_summary_generation",
            }
    except Exception as e:
        logger.error(f"Project tailoring failed: {str(e)}")
        return {
            "error_message": f"Failed to tailor projects: {str(e)}",
            "current_step": "project_tailoring_failed",
        }


def generate_executive_summary_node(state: AppState) -> Dict[str, Any]:
    """Generate executive summary using the complete enriched CV and add it directly to tailored_cv.

    This is the final step in the living document pattern, using the fully enriched CV
    (qualifications + tailored experience + tailored projects) to generate the summary.
    Handles regeneration when human_approved=False.
    """
    logger.info("Starting executive summary generation node")
    try:
        job_data = state["job_description_data"]
        cv_data = state["tailored_cv"]

        # If this is a regeneration (human_approved=False), remove existing summary
        if state.get("human_approved") == False:
            logger.info("Regenerating executive summary based on user feedback")
            cv_data = cv_data.model_copy(deep=True)
            cv_data.sections = [s for s in cv_data.sections if "summary" not in s.name.lower()]

        # Use the complete enriched CV as context - no need to extract separately
        # The CV now contains all the tailored content from previous steps
        complete_cv_context = {
            "sections": [
                {
                    "title": section.name,
                    "entries": [
                        {
                            "title": entry.title,
                            "subtitle": entry.subtitle,
                            "details": entry.details,
                            "tags": entry.tags,
                        }
                        for entry in section.entries
                    ],
                }
                for section in cv_data.sections
            ]
        }

        chain = create_executive_summary_chain()

        # Include human feedback if this is a regeneration
        chain_input = {
            "job_description": state["raw_job_description"],
            "enriched_cv": str(complete_cv_context),  # Pass the complete enriched CV
        }

        if state.get("human_approved") == False and state.get("human_feedback"):
            chain_input["human_feedback"] = state["human_feedback"]
            logger.info(f"Including human feedback in summary regeneration: {state['human_feedback'][:100]}...")

        result = chain.invoke(chain_input)

        # LIVING DOCUMENT PATTERN: Add executive summary directly to tailored_cv
        from models import Section, CVEntry

        # Create executive summary section
        summary_entry = CVEntry(
            title="Executive Summary",
            subtitle=None,
            date_range=None,
            details=[result.summary],  # Store summary as a detail
            tags=[],
        )

        summary_section = Section(name="Executive Summary", entries=[summary_entry])

        # Create final CV with summary at the very beginning
        final_cv = cv_data.model_copy(deep=True)
        final_cv.sections.insert(0, summary_section)

        logger.info(
            f"Executive summary generation successful. Summary length: {len(result.summary)} characters. Added to tailored_cv."
        )
        return {
            "tailored_cv": final_cv,
            "current_step": "awaiting_summary_review",
            "human_approved": None,  # Clear the approval flag
            "human_feedback": None,  # Clear the feedback
        }
    except Exception as e:
        logger.error(f"Executive summary generation failed: {str(e)}")
        return {
            "error_message": f"Failed to generate executive summary: {str(e)}",
            "current_step": "summary_generation_failed",
        }


def finalize_cv_node(state: AppState) -> Dict[str, Any]:
    """Finalize the CV generation process.

    LIVING DOCUMENT PATTERN: The tailored_cv is already complete with:
    - Executive Summary (added by generate_executive_summary_node)
    - Key Qualifications (added by generate_key_qualifications_node)
    - Tailored Experience (updated by tailor_experience_node)
    - Tailored Projects (updated by tailor_project_entry_node)
    """
    logger.info("Starting CV finalization node")
    try:
        # The tailored_cv is already the complete, enriched document
        final_cv = state["tailored_cv"]

        logger.info("CV finalization successful - tailored_cv is complete")
        return {
            "final_cv": final_cv,
            "current_step": "cv_finalized",
            "workflow_complete": True,
        }
    except Exception as e:
        logger.error(f"CV finalization failed: {str(e)}")
        return {
            "error_message": f"Failed to finalize CV: {str(e)}",
            "current_step": "cv_finalization_failed",
        }
