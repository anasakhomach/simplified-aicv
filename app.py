"""Streamlit application for AI CV Generation.

This is the main entry point and UI controller. It serves as the gatekeeper
for st.session_state and orchestrates the entire workflow.
"""
# pylint: disable=logging-fstring-interpolation
# pylint: disable=line-too-long
# pylint: disable=wrong-import-position

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
# Add the project root to the Python path to allow absolute imports

import json
import logging
import base64
import streamlit as st
from state import AppState, get_initial_state
from graph import run_graph_step
from models import StructuredCV
from pydantic import BaseModel
from ui_components.render_experience import render_experience_review
from ui_components.render_projects import render_projects_review
from ui_components.render_summary import render_summary_review
from ui_components.render_qualifications import render_qualifications_review
from latex_generator import generate_latex_string
from latex_compiler import compile_latex_to_pdf


# Configure logging for Streamlit
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('C:\\Users\\Nitro\\aicvgen\\simplified\\app.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def render_pdf(pdf_bytes: bytes):
    """Renders a PDF file in the Streamlit app."""
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="AI CV Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
STATE_KEY = "app_state"
PERSISTENCE_KEY = "cv_generation_session"

# --- Workflow Progress Milestones ---
WORKFLOW_MILESTONES = {
    "input": 0,
    "job_description_parsed": 5,
    "cv_parsed": 10,
    "iterative_session_ready": 15,
    "source_sections_mapped": 20,
    "awaiting_qualifications_review": 30,
    "qualifications_approved": 35,
    "start_experience_tailoring": 40,
    "awaiting_experience_review": 50,
    "experience_tailoring_complete": 60,
    "start_projects_tailoring": 65,
    "awaiting_project_review": 75,
    "projects_tailoring_complete": 85,
    "start_summary_generation": 90,
    "awaiting_summary_review": 95,
    "summary_approved": 98,
    "start_cv_finalization": 99,
    "cv_finalized": 100,
}

def initialize_session_state() -> None:
    """Initialize session state with default AppState if not exists."""
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = get_initial_state()

def get_app_state() -> AppState:
    """Get current application state from session state.

    Returns:
        AppState: Current application state
    """
    if STATE_KEY not in st.session_state:
        logger.info("Initializing new application state")
        st.session_state[STATE_KEY] = get_initial_state()
    return st.session_state[STATE_KEY]

def update_app_state(new_state: AppState) -> None:
    """Update application state in session state.

    Args:
        new_state: Updated application state
    """
    logger.info(f"Updating application state. Current step: {new_state.get('current_step', 'unknown')}")
    st.session_state[STATE_KEY] = new_state

def pydantic_encoder(obj):
    """Custom JSON encoder for Pydantic models."""
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def save_session_to_json() -> None:
    """Save current session state to JSON for persistence."""
    try:
        state = get_app_state()
        # Use a custom default function for the encoder that handles Pydantic models
        with open(f"{PERSISTENCE_KEY}.json", "w") as f:
            json.dump(state, f, indent=2, default=pydantic_encoder)
        st.success("Session saved successfully!")
    except Exception as e:
        st.error(f"Failed to save session: {str(e)}")
        logger.error(f"Session saving failed: {e}")

def load_session_from_json() -> None:
    """Load session state from JSON file and reconstruct Pydantic models."""
    try:
        with open(f"{PERSISTENCE_KEY}.json", "r") as f:
            loaded_state = json.load(f)

        # --- Model Reconstruction ---
        # After loading, the CV objects are dicts. We must convert them back
        # into StructuredCV model instances for the generator to work.
        if loaded_state.get("source_cv"):
            loaded_state["source_cv"] = StructuredCV.model_validate(loaded_state["source_cv"])
            
        if loaded_state.get("tailored_cv"):
            loaded_state["tailored_cv"] = StructuredCV.model_validate(loaded_state["tailored_cv"])
            
        if loaded_state.get("final_cv"):
            loaded_state["final_cv"] = StructuredCV.model_validate(loaded_state["final_cv"])

        # Add any other Pydantic models here if they need reconstruction
        if loaded_state.get("job_description_data"):
            from models import JobDescriptionData
            loaded_state["job_description_data"] = JobDescriptionData.model_validate(loaded_state["job_description_data"])
        
        if loaded_state.get("section_map"):
            from models import SectionMap
            loaded_state["section_map"] = SectionMap.model_validate(loaded_state["section_map"])

        update_app_state(loaded_state)
        st.success("Session loaded and validated successfully!")
        st.rerun()
    except FileNotFoundError:
        st.warning("No saved session found.")
    except Exception as e:
        st.error(f"Failed to load and validate session: {str(e)}")
        logger.error(f"Session loading failed: {e}")
## Fisrt UI Rendering Of The Side-Bar Happen Here. ==================
def render_sidebar() -> None:
    """Render the sidebar with session management and progress."""
    with st.sidebar:
        st.header("🎯 Session Management")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Session", use_container_width=True):
                save_session_to_json()

        with col2:
            if st.button("📂 Load Session", use_container_width=True):
                load_session_from_json()

        if st.button("🔄 Reset Session", use_container_width=True):
            update_app_state(get_initial_state())
            st.rerun()

        st.divider()

        # Progress tracking
        st.header("📊 Progress")

        state = get_app_state()
        current_step = state.get("current_step", "input")

        # Get progress percentage from milestones, default to 0 if not found
        progress_percent = WORKFLOW_MILESTONES.get(current_step, 0)

        # Display progress bar (st.progress expects a value between 0.0 and 1.0)
        st.progress(progress_percent / 100)

        # Display current step name, formatted nicely
        st.markdown(f"**Current Step:** {current_step.replace('_', ' ').title()}")

        st.divider()  # Add a divider for visual separation

        # Error display
        if state.get("has_error"):
            st.error(f"Error: {state.get('error_message', 'Unknown error')}")
## End of Side-Bar Rendering. =======================================

## Input Section Rendering. =========================================
def render_input_section() -> None:
    """Render the input section for job description and CV."""
    st.header("📝 Input Your Information")
    st.markdown("**Step 1:** Provide both inputs below, then click the Generate button to start AI-powered CV tailoring.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Job Description")
        job_description = st.text_area(
            "Paste the job description here:",
            value=get_app_state().get("raw_job_description", ""),
            height=200,
            help="Copy and paste the complete job description from the job posting.",
            placeholder="Paste the full job description here...\n\nExample:\nWe are looking for a Senior Software Engineer with experience in Python, React, and cloud technologies..."
        )

        if job_description != get_app_state().get("raw_job_description", ""):
            logger.info(f"User updated job description. Length: {len(job_description)}")
            state = get_app_state()
            state["raw_job_description"] = job_description
            update_app_state(state)

    with col2:
        st.subheader("📄 Your Current CV")
        cv_text = st.text_area(
            "Paste your current CV text here:",
            value=get_app_state().get("raw_cv_text", ""),
            height=200,
            help="Copy and paste your current CV content in plain text format.",
            placeholder="Paste your CV content here...\n\nExample:\nJohn Doe\nSoftware Engineer\n\nExperience:\n- 5 years in web development\n- Python, JavaScript, React..."
        )

        if cv_text != get_app_state().get("raw_cv_text", ""):
            logger.info(f"User updated CV text. Length: {len(cv_text)}")
            state = get_app_state()
            state["raw_cv_text"] = cv_text
            update_app_state(state)
## End of Input Section Rendering. ==================================

def _start_initial_workflow(state: AppState) -> None:
    """Helper function to orchestrate initial workflow steps with granular UI feedback.

    This function breaks down the background processing into explicit steps:
    1. Parse job description
    2. Parse CV
    3. Setup iterative session
    4. Map source sections

    Each step gets its own spinner and progress update for responsive UI.
    """
    try:
        current_state = state

        # Step 1: Parse Job Description
        with st.spinner("📋 Parsing job description..."):
            logger.info("Starting job description parsing")
            current_state = run_graph_step(current_state)
            update_app_state(current_state)

        # Check for errors after JD parsing
        if current_state.get("error_message"):
            st.error(f"❌ Job description parsing failed: {current_state['error_message']}")
            return

        # Step 2: Parse CV
        with st.spinner("📄 Parsing CV content..."):
            logger.info("Starting CV parsing")
            current_state = run_graph_step(current_state)
            update_app_state(current_state)

        # Check for errors after CV parsing
        if current_state.get("error_message"):
            st.error(f"❌ CV parsing failed: {current_state['error_message']}")
            return

        # Step 3: Setup Iterative Session
        with st.spinner("⚙️ Setting up iterative session..."):
            logger.info("Starting iterative session setup")
            current_state = run_graph_step(current_state)
            update_app_state(current_state)

        # Check for errors after session setup
        if current_state.get("error_message"):
            st.error(f"❌ Session setup failed: {current_state['error_message']}")
            return

        # Step 4: Map Source Sections
        with st.spinner("🗺️ Mapping source sections..."):
            logger.info("Starting source section mapping")
            current_state = run_graph_step(current_state)
            update_app_state(current_state)

        # Check for errors after section mapping
        if current_state.get("error_message"):
            st.error(f"❌ Section mapping failed: {current_state['error_message']}")
            return

        logger.info("Initial workflow steps completed successfully")
        # Final rerun to refresh the UI with the completed initial steps
        st.rerun()

    except Exception as e:
        logger.error(f"Initial workflow failed: {str(e)}")
        st.error(f"❌ Initial processing failed: {str(e)}")


def render_workflow_controls() -> None:
    """Render workflow control buttons."""
    st.header("🚀 Generate Tailored CV")
    st.markdown("**Step 2:** Click the button below to start the AI-powered CV generation process.")

    state = get_app_state()
    # Check if we have required inputs
    has_inputs = bool(state.get("raw_job_description")) and bool(state.get("raw_cv_text"))

    logger.info(f"Workflow controls rendered. Has inputs: {has_inputs}")

    # Check if we're in any review state
    current_step = state.get("current_step", "")
    if "awaiting" in current_step:
        render_section_review_ui(current_step)
        return

    # Always show the generate button, but disable if inputs are missing
    button_disabled = not has_inputs
    button_help = "Provide both job description and CV text above to enable" if button_disabled else "Click to start AI-powered CV tailoring"

    if not has_inputs:
        st.warning("⚠️ Please provide both job description and CV text above to start generation.")

    # Generate CV button - always visible
    if st.button(
        "🎯 Generate Tailored CV",
        type="primary",
        use_container_width=True,
        disabled=button_disabled,
        help=button_help
    ):
        logger.info("User clicked Generate Tailored CV button")
        # Use the new granular workflow function
        _start_initial_workflow(state)

def render_approval_buttons(state: AppState, section_name: str, next_step: str) -> None:
    """Render approval buttons for a specific section."""
    # Review and feedback section
    st.divider()
    st.subheader("💬 Your Feedback")
    feedback = st.text_area(
        f"Please review the {section_name} above and provide feedback (optional for approval, required for revision):",
        value=state.get("human_feedback", ""),
        height=120,
        help="Provide specific feedback on what should be changed, added, or removed.",
        placeholder=f"Example: The {section_name} should emphasize more relevant skills. Please add specific technologies mentioned in the job description."
    )

    # Action buttons
    st.subheader("🎯 Choose Your Action")
    col1, col2 = st.columns(2)

    with col1:
        if st.button(f"✅ Approve {section_name.title()}", type="primary", use_container_width=True, help=f"Accept the generated {section_name} and proceed to the next step"):
            logger.info(f"User approved {section_name}")
            new_state = state.copy()
            new_state["human_feedback"] = feedback
            new_state["human_approved"] = True
            new_state["current_step"] = next_step

            try:
                # Run the next step immediately
                final_state = run_graph_step(new_state)
                update_app_state(final_state)
                st.success(f"✅ {section_name.title()} approved! Continuing...")
                st.rerun()
            except Exception as e:
                logger.error(f"Failed to continue workflow after approval: {str(e)}")
                st.error(f"❌ Failed to continue: {str(e)}")

    with col2:
        if st.button(f"🔄 Request {section_name.title()} Revision", use_container_width=True, help=f"Request changes to the generated {section_name}"):
            if feedback.strip():
                logger.info(f"User requested {section_name} revision with feedback: {feedback[:100]}...")
                # Update state with feedback and set step for regeneration
                new_state = state.copy()
                new_state["human_feedback"] = feedback
                new_state["human_approved"] = False

                # Set the appropriate step for regeneration based on section
                if section_name == "qualifications":
                    new_state["current_step"] = "cv_parsed"  # Go back to generate qualifications
                elif section_name == "summary":
                    new_state["current_step"] = "start_summary_generation"
                elif section_name == "experience":
                    new_state["current_step"] = "start_experience_tailoring"
                elif section_name == "projects":
                    new_state["current_step"] = "start_projects_tailoring"

                update_app_state(new_state)
                st.info(f"🔄 {section_name.title()} revision requested! Click 'Generate Tailored CV' to regenerate with your feedback.")
                st.rerun()
            else:
                logger.warning(f"User tried to request {section_name} revision without providing feedback")
                st.warning("⚠️ Please provide specific feedback before requesting revision.")


def render_section_review_ui(current_step: str) -> None:
    """Render the section-specific review interface."""
    state = get_app_state()

    # Determine which section is being reviewed
    if current_step == "awaiting_qualifications_review":
        render_qualifications_review(state, render_approval_buttons)
    elif current_step == "awaiting_experience_review":
        render_experience_review(state, update_app_state)
    elif current_step == "awaiting_project_review":
        render_projects_review(state, update_app_state)
    elif current_step == "awaiting_summary_review":
        render_summary_review(state, render_approval_buttons)
    else:
        st.error(f"Unknown review state: {current_step}")

# render_approval_buttons function moved to individual UI component files

def render_results_section(state: AppState, current_step: str) -> None:
    """Render the results and output section."""

    # Show final CV if available
    if state.get("final_cv"):
        st.header("🎉 Your Tailored CV")
        st.markdown("**Step 4:** Your CV has been successfully tailored! Review and download below.")

        # Display the final CV in a nice container
        with st.container():
            st.markdown("### 📄 Final CV Content")
            with st.expander("Click to view your complete tailored CV", expanded=True):
                final_cv = state["final_cv"]
                if isinstance(final_cv, StructuredCV):
                    # Render personal info at the top
                    if final_cv.personal_info:
                        st.header(final_cv.personal_info.get("name", ""))

                        # Display contact info in a single line
                        contact_parts = []
                        if final_cv.personal_info.get("email"):
                            contact_parts.append(final_cv.personal_info["email"])
                        if final_cv.personal_info.get("phone"):
                            contact_parts.append(final_cv.personal_info["phone"])
                        if final_cv.personal_info.get("linkedin"):
                            contact_parts.append(final_cv.personal_info["linkedin"])

                        if contact_parts:
                            contact_line = " | ".join(contact_parts)
                            st.markdown(f"**{contact_line}**")

                        st.divider()

                    # Render structured CV sections
                    for section in final_cv.sections:
                        if section.name == "Key Qualifications":
                            st.markdown(f"### {section.name}")
                            qualification_titles = [entry.title for entry in section.entries]
                            st.markdown("- " + "\n- ".join(qualification_titles))
                            st.markdown("---") # Add a separator
                        else:
                            # This is the existing generic rendering logic for other sections
                            st.markdown(f"### {section.name}")
                            for entry in section.entries:
                                if entry.title and entry.title.lower() != section.name.lower():
                                    st.markdown(f"**{entry.title}**")
                                if entry.subtitle:
                                    st.markdown(f"*{entry.subtitle}*")
                                if entry.date_range:
                                    st.markdown(f"_{entry.date_range}_")
                                for detail in entry.details:
                                    st.markdown(f"- {detail}")
                                if entry.tags:
                                    st.markdown(f"**Skills:** `{', '.join(entry.tags)}`")
                                st.markdown("---")
                        st.markdown("") # Add space between sections
                else:
                    st.markdown(str(final_cv))

        # Download options
        col1, col2 = st.columns(2)
        with col1:
            # Convert structured CV to text for download
            cv_text = ""
            if isinstance(state["final_cv"], StructuredCV):
                for section in state["final_cv"].sections:
                    cv_text += f"{section.name}\n"
                    cv_text += "=" * len(section.name) + "\n\n"
                    if section.name == "Key Qualifications":
                        # Handle Key Qualifications as a simple bulleted list
                        for entry in section.entries:
                            if entry.title:
                                cv_text += f"• {entry.title}\n"
                        cv_text += "\n"
                    else:
                        # Handle other sections with full entry details
                        for entry in section.entries:
                            if entry.title:
                                cv_text += f"{entry.title}\n"
                            if entry.subtitle:
                                cv_text += f"{entry.subtitle}\n"
                            if entry.date_range:
                                cv_text += f"{entry.date_range}\n"
                            for detail in entry.details:
                                cv_text += f"• {detail}\n"
                            if entry.tags:
                                cv_text += f"Skills: {', '.join(entry.tags)}\n"
                            cv_text += "\n"
                    cv_text += "\n"
            else:
                cv_text = str(state["final_cv"])

            st.download_button(
                label="📄 Download as Text File",
                data=cv_text,
                file_name="tailored_cv.txt",
                mime="text/plain",
                use_container_width=True,
                type="primary"
            )

        with col2:
            if st.button("🔄 Start New CV", use_container_width=True):
                update_app_state(get_initial_state())

        # LaTeX PDF Generation Section
        st.divider()
        st.subheader("📄 LaTeX PDF Version")

        if st.button("✨ Generate LaTeX PDF", use_container_width=True):
            with st.spinner("Generating and compiling LaTeX PDF... This may take a few moments and several retries."):
                from latex_graph import latex_generation_graph
                final_cv = state["final_cv"]
                initial_agent_state = {"cv_data": final_cv, "retries": 0}

                # Run the agent
                final_agent_state = latex_generation_graph.invoke(initial_agent_state)

                # Store and display the result
                state['final_pdf_bytes'] = final_agent_state.get('pdf_bytes')
                state['latex_error_log'] = final_agent_state.get('error_log')
                update_app_state(state)
                st.rerun()

        # After the button, check if a PDF or error exists and display it
        if state.get('final_pdf_bytes'):
            st.success("PDF Generated Successfully!")
            render_pdf(state['final_pdf_bytes'])
            st.download_button(
                label="⬇️ Download LaTeX PDF",
                data=state['final_pdf_bytes'],
                file_name="cv.pdf",
                mime="application/pdf"
            )
        elif state.get('latex_error_log'):
            st.error("Failed to generate PDF after multiple retries.")
            with st.expander("View Final Error Log"):
                st.code(state['latex_error_log'], language='log')

        return

    # Show intermediate results if any content has been generated
    cv_data = state.get("tailored_cv")
    has_content = cv_data and len(cv_data.sections) > 0

    if has_content:
        st.header("📋 Generated Content")
        st.markdown("**Progress:** AI is working on your CV. Generated sections will appear below.")

        # Display only the relevant section based on current_step
        if "qualifications" in current_step:
            # Find and display Key Qualifications
            qualifications_section = next((s for s in cv_data.sections if "qualifications" in s.name.lower()), None)
            if qualifications_section:
                st.markdown(f"### 🎯 {qualifications_section.name}")
                with st.expander(f"View {qualifications_section.name}", expanded=True):
                    for entry in qualifications_section.entries:
                        if entry.title:
                            st.markdown(f"• {entry.title}")
        elif "experience" in current_step:
            # Find and display Experience section
            experience_section = next((s for s in cv_data.sections if "experience" in s.name.lower()), None)
            if experience_section:
                st.markdown(f"### 🎯 {experience_section.name}")
                with st.expander(f"View {experience_section.name}", expanded=True):
                    for entry in experience_section.entries:
                        if entry.title:
                            st.markdown(f"**{entry.title}**")
                        if entry.subtitle:
                            st.markdown(f"*{entry.subtitle}*")
                        if entry.date_range:
                            st.markdown(f"📅 {entry.date_range}")
                        for detail in entry.details:
                            st.markdown(f"• {detail}")
                        if entry.tags:
                            st.markdown(f"🏷️ **Tags:** {', '.join(entry.tags)}")
                        st.markdown("---")
        elif "project" in current_step:
            # Find and display Projects section
            project_section = next((s for s in cv_data.sections if "project" in s.name.lower()), None)
            if project_section:
                st.markdown(f"### 🎯 {project_section.name}")
                with st.expander(f"View {project_section.name}", expanded=True):
                    for entry in project_section.entries:
                        if entry.title:
                            st.markdown(f"**{entry.title}**")
                        if entry.subtitle:
                            st.markdown(f"*{entry.subtitle}*")
                        if entry.date_range:
                            st.markdown(f"📅 {entry.date_range}")
                        for detail in entry.details:
                            st.markdown(f"• {detail}")
                        if entry.tags:
                            st.markdown(f"🏷️ **Tags:** {', '.join(entry.tags)}")
                        st.markdown("---")
        elif "summary" in current_step:
            # Find and display Executive Summary
            summary_section = next((s for s in cv_data.sections if "summary" in s.name.lower()), None)
            if summary_section:
                st.markdown(f"### 🎯 {summary_section.name}")
                with st.expander(f"View {summary_section.name}", expanded=True):
                    for entry in summary_section.entries:
                        if entry.title:
                            st.markdown(f"**{entry.title}**")
                        if entry.subtitle:
                            st.markdown(f"*{entry.subtitle}*")
                        if entry.date_range:
                            st.markdown(f"📅 {entry.date_range}")
                        for detail in entry.details:
                            st.markdown(f"• {detail}")
                        if entry.tags:
                            st.markdown(f"🏷️ **Tags:** {', '.join(entry.tags)}")
                        st.markdown("---")
        else:
            st.info("💡 Workflow in progress. Content will appear here as it's generated.")

        # The "Next" info message can remain
        if not state.get("human_review_required", False):
            st.info("💡 **Next:** Continue clicking 'Generate Tailored CV' to complete all sections.")

def main() -> None:
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()

    # App header
    st.title("🤖 AI CV Generator")
    st.markdown("Transform your CV to perfectly match any job description using AI.")

    # Render main sections
    render_sidebar()  # Sidebar is always visible

    # --- START OF ELEGANT LATEX TEST HARNESS ---
    # --- Removed as we finish testing the latex generation function.
    # --- END OF ELEGANT LATEX TEST HARNESS ---

    state = get_app_state()
    current_step = state.get("current_step", "input")

    if state.get("final_cv"):
        # Workflow complete: show only final results
        render_results_section(state, current_step)
    elif current_step == "input":
        # Initial state: show input fields and main generate button
        render_input_section()
        st.divider()
        render_workflow_controls()
        st.divider()
        render_results_section(state, current_step)
    else:
        # Workflow in progress (not input, not final): show workflow controls and relevant section
        render_workflow_controls()
        st.divider()
        render_results_section(state, current_step)

    # Debug section (only in development)
    if st.checkbox("🔧 Show Debug Info"):
        st.subheader("Debug: Current State")
        st.json(get_app_state())

if __name__ == "__main__":
    main()
