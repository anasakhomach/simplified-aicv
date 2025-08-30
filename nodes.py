"""Node functions for the CV generation workflow.

This module contains stateless node functions that orchestrate the workflow.
Following the constitutional rules, nodes take AppState as input and return
a Python dictionary as output. They must not have side effects.
"""

import logging
from typing import Dict, Any
from chains import (
    create_job_description_parsing_chain,
    create_cv_parsing_chain,
    create_key_qualifications_chain,
    create_executive_summary_chain,
    create_experience_tailoring_chain,
    create_projects_tailoring_chain
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
        
        logger.info(f"Job description parsing successful. Job title: {result.job_title}")
        return {
            "job_description_data": result,
            "current_step": "job_description_parsed"
        }
    except Exception as e:
        logger.error(f"Job description parsing failed: {str(e)}")
        return {
            "error_message": f"Failed to parse job description: {str(e)}"
        }


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
        
        logger.info(f"CV parsing successful. Candidate: {result.personal_info.get('full_name', 'Unknown')}")
        return {
            "structured_cv": result,
            "current_step": "cv_parsed"
        }
    except Exception as e:
        logger.error(f"CV parsing failed: {str(e)}")
        return {
            "error_message": f"CV parsing failed: {str(e)}. Please check the CV format and try again.",
            "human_review_required": True,
            "current_step": "cv_parsing_failed"
        }


def generate_key_qualifications_node(state: AppState) -> Dict[str, Any]:
    """Generate key qualifications and add them directly to the structured_cv as a new section.
    
    This implements the living document pattern where structured_cv is progressively enriched.
    """
    logger.info("Starting key qualifications generation node")
    try:
        # Check if required data exists
        job_data = state.get("job_description_data")
        cv_data = state.get("structured_cv")
        
        if not job_data or not cv_data:
            logger.error(f"Missing required data. Job data: {job_data is not None}, CV data: {cv_data is not None}")
            return {
                "error_message": "Missing parsed job description or CV data. Please ensure both inputs are provided and parsed successfully."
            }
        
        # Extract skills from CV sections (looking for skills/technologies in entries)
        current_skills = []
        for section in cv_data.sections:
            for entry in section.entries:
                current_skills.extend(entry.tags)
        
        # Prepare job requirements from the new model structure
        required_skills = [skill.name for skill in job_data.technical_skills if skill.is_required]
        preferred_skills = [skill.name for skill in job_data.technical_skills if not skill.is_required]
        
        job_requirements = {
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "key_responsibilities": job_data.key_responsibilities
        }
        
        chain = create_key_qualifications_chain()
        result = chain.invoke({
            "job_requirements": str(job_requirements),
            "current_skills": str(current_skills)
        })
        
        # LIVING DOCUMENT PATTERN: Add qualifications directly to structured_cv
        from models import Section, CVEntry
        
        # Create CVEntry objects for each qualification
        qualification_entries = [
            CVEntry(
                title=qualification,
                subtitle=None,
                date_range=None,
                details=[],
                tags=[]
            )
            for qualification in result.qualifications
        ]
        
        # Create new Key Qualifications section
        qualifications_section = Section(
            name="Key Qualifications",
            entries=qualification_entries
        )
        
        # Create updated CV with the new section at the beginning
        updated_cv = cv_data.model_copy(deep=True)
        updated_cv.sections.insert(0, qualifications_section)
        
        logger.info(f"Key qualifications generation successful. Added {len(result.qualifications)} qualifications to structured_cv")
        
        return {
            "structured_cv": updated_cv,
            "current_step": "awaiting_qualifications_review"
        }
    except Exception as e:
        logger.error(f"Key qualifications generation failed: {str(e)}")
        return {
            "error_message": f"Failed to generate key qualifications: {str(e)}"
        }


def request_human_review_node(state: AppState) -> Dict[str, Any]:
    """Request human review of generated key qualifications."""
    # Get qualifications from structured_cv
    cv_data = state.get("structured_cv")
    qualifications_content = ""
    if cv_data:
        for section in cv_data.sections:
            if "qualifications" in section.name.lower():
                qualifications_content = "\n".join([f"• {entry.title}" for entry in section.entries])
                break
    if qualifications_content:
        review_content = qualifications_content
    else:
        review_content = "No qualifications generated yet."
    
    return {
        "human_review_required": True,
        "human_feedback": review_content,
        "current_step": "awaiting_human_review"
    }


def generate_executive_summary_node(state: AppState) -> Dict[str, Any]:
    """Generate executive summary using the complete enriched CV and add it directly to structured_cv.
    
    This is the final step in the living document pattern, using the fully enriched CV
    (qualifications + tailored experience + tailored projects) to generate the summary.
    """
    logger.info("Starting executive summary generation node")
    try:
        job_data = state["job_description_data"]
        cv_data = state["structured_cv"]
        
        # Use the complete enriched CV as context - no need to extract separately
        # The CV now contains all the tailored content from previous steps
        complete_cv_context = {
            "sections": [{
                "title": section.name,
                "entries": [{
                    "title": entry.title,
                    "subtitle": entry.subtitle,
                    "details": entry.details,
                    "tags": entry.tags
                } for entry in section.entries]
            } for section in cv_data.sections]
        }
        
        chain = create_executive_summary_chain()
        result = chain.invoke({
            "job_description": state["raw_job_description"],
            "enriched_cv": str(complete_cv_context)  # Pass the complete enriched CV
        })
        
        # LIVING DOCUMENT PATTERN: Add executive summary directly to structured_cv
        from models import Section, CVEntry
        
        # Create executive summary section
        summary_entry = CVEntry(
            title="Executive Summary",
            subtitle=None,
            date_range=None,
            details=[result.summary],  # Store summary as a detail
            tags=[]
        )
        
        summary_section = Section(
            name="Executive Summary",
            entries=[summary_entry]
        )
        
        # Create final CV with summary at the very beginning
        final_cv = cv_data.model_copy(deep=True)
        final_cv.sections.insert(0, summary_section)
        
        logger.info(f"Executive summary generation successful. Summary length: {len(result.summary)} characters. Added to structured_cv.")
        return {
            "structured_cv": final_cv,
            "current_step": "awaiting_summary_review"
        }
    except Exception as e:
        logger.error(f"Executive summary generation failed: {str(e)}")
        return {
            "error_message": f"Failed to generate executive summary: {str(e)}",
            "current_step": "summary_generation_failed"
        }


def tailor_experience_node(state: AppState) -> Dict[str, Any]:
    """Tailor work experience entries using enriched CV context and modify structured_cv in place.
    
    This implements the living document pattern where the enriched CV (now containing qualifications)
    is used as context for better experience tailoring.
    """
    logger.info("Starting experience tailoring node")
    
    try:
        cv_data = state["structured_cv"]
        
        # Extract qualifications from the enriched CV for context
        qualifications_context = []
        for section in cv_data.sections:
            if "qualifications" in section.name.lower():
                qualifications_context = [entry.title for entry in section.entries]
                break
        
        # Extract current experience from CV sections using exact name matching
        current_experience = []
        experience_section_indices = []
        for i, section in enumerate(cv_data.sections):
            if section.name == "Experience":
                experience_section_indices.append(i)
                for entry in section.entries:
                    current_experience.append({
                        "title": entry.title,
                        "subtitle": entry.subtitle,
                        "details": entry.details,
                        "tags": entry.tags
                    })
        
        chain = create_experience_tailoring_chain()
        result = chain.invoke({
            "job_description": state["raw_job_description"],
            "current_experience": str(current_experience),
            "key_qualifications": str(qualifications_context)  # Pass qualifications as context
        })
        
        # LIVING DOCUMENT PATTERN: Update experience sections in structured_cv
        from models import CVEntry
        
        updated_cv = cv_data.model_copy(deep=True)
        
        # Replace experience sections with tailored versions
        tailored_section_idx = 0
        for section_idx in experience_section_indices:
            if tailored_section_idx < len(result.tailored_sections):
                tailored_section = result.tailored_sections[tailored_section_idx]
                
                # Update the section with tailored entries (Section object already has proper CVEntry objects)
                updated_cv.sections[section_idx].entries = tailored_section.entries
                tailored_section_idx += 1
        
        logger.info(f"Experience tailoring successful. Updated {len(experience_section_indices)} experience sections in structured_cv")
        return {
            "structured_cv": updated_cv,
            "current_step": "awaiting_experience_review"
        }
    except Exception as e:
        logger.error(f"Experience tailoring failed: {str(e)}")
        return {
            "error_message": f"Failed to tailor experience: {str(e)}",
            "current_step": "experience_tailoring_failed"
        }


def tailor_projects_node(state: AppState) -> Dict[str, Any]:
    """Tailor projects using fully enriched CV context and modify structured_cv in place.
    
    This implements the living document pattern where the fully enriched CV 
    (qualifications + tailored experience) is used as context for better project tailoring.
    """
    logger.info("Starting projects tailoring node")
    
    if "job_description_data" not in state or "structured_cv" not in state:
        logger.error("Required data not found in state for projects tailoring")
        return {
            "error_message": "Failed to tailor projects: missing job description or CV data"
        }
    
    try:
        cv_data = state["structured_cv"]
        
        # Extract qualifications and experience context from enriched CV
        qualifications_context = []
        experience_context = []
        
        for section in cv_data.sections:
            if "qualifications" in section.name.lower():
                qualifications_context = [entry.title for entry in section.entries]
            elif section.name == "Experience":
                for entry in section.entries:
                    experience_context.append(f"{entry.title} - {', '.join(entry.details[:2])}")
        
        # Extract current projects from CV data using exact name matching
        current_projects = []
        project_section_indices = []
        for i, section in enumerate(cv_data.sections):
            if section.name == "Projects":
                project_section_indices.append(i)
                for entry in section.entries:
                    current_projects.append({
                        "title": entry.title,
                        "subtitle": entry.subtitle,
                        "details": entry.details,
                        "tags": entry.tags
                    })
        
        if not current_projects:
            logger.warning("No projects section found in CV")
            return {
                "structured_cv": cv_data,
                "current_step": "projects_tailored"
            }
        
        chain = create_projects_tailoring_chain()
        result = chain.invoke({
            "job_description": str(state["job_description_data"]),
            "current_projects": str(current_projects),
            "key_qualifications": str(qualifications_context),
            "tailored_experience": str(experience_context)
        })
        
        # LIVING DOCUMENT PATTERN: Update project sections in structured_cv
        from models import CVEntry
        
        updated_cv = cv_data.model_copy(deep=True)
        
        # Replace project sections with tailored versions
        tailored_section_idx = 0
        for section_idx in project_section_indices:
            if tailored_section_idx < len(result.tailored_sections):
                tailored_section = result.tailored_sections[tailored_section_idx]
                
                # Update the section with tailored entries (Section object already has proper CVEntry objects)
                updated_cv.sections[section_idx].entries = tailored_section.entries
                tailored_section_idx += 1
        
        logger.info(f"Projects tailoring successful. Updated {len(project_section_indices)} project sections in structured_cv")
        return {
            "structured_cv": updated_cv,
            "current_step": "awaiting_projects_review"
        }
    except Exception as e:
        logger.error(f"Projects tailoring failed: {str(e)}")
        return {
            "error_message": f"Failed to tailor projects: {str(e)}",
            "current_step": "projects_tailoring_failed"
        }


def finalize_cv_node(state: AppState) -> Dict[str, Any]:
    """Finalize the CV generation process.
    
    LIVING DOCUMENT PATTERN: The structured_cv is already complete with:
    - Executive Summary (added by generate_executive_summary_node)
    - Key Qualifications (added by generate_key_qualifications_node)
    - Tailored Experience (updated by tailor_experience_node)
    - Tailored Projects (updated by tailor_projects_node)
    """
    logger.info("Starting CV finalization node")
    try:
        # The structured_cv is already the complete, enriched document
        final_cv = state["structured_cv"]
        
        logger.info("CV finalization successful - structured_cv is complete")
        return {
            "final_cv": final_cv,
            "current_step": "cv_finalized",
            "workflow_complete": True
        }
    except Exception as e:
        logger.error(f"CV finalization failed: {str(e)}")
        return {
            "error_message": f"Failed to finalize CV: {str(e)}",
            "current_step": "cv_finalization_failed"
        }