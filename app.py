"""Streamlit application for AI CV Generation.

This is the main entry point and UI controller. It serves as the gatekeeper
for st.session_state and orchestrates the entire workflow.
"""
# pylint: disable=logging-fstring-interpolation
# pylint: disable=line-too-long

import json
import logging
import streamlit as st
from state import AppState, get_initial_state
from graph import run_graph_step
from models import StructuredCV

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

def save_session_to_json() -> None:
    """Save current session state to JSON for persistence."""
    try:
        state = get_app_state()
        with open(f"{PERSISTENCE_KEY}.json", "w") as f:
            json.dump(state, f, indent=2, default=str)
        st.success("Session saved successfully!")
    except Exception as e:
        st.error(f"Failed to save session: {str(e)}")

def load_session_from_json() -> None:
    """Load session state from JSON file."""
    try:
        with open(f"{PERSISTENCE_KEY}.json", "r") as f:
            loaded_state = json.load(f)
        update_app_state(loaded_state)
        st.success("Session loaded successfully!")
        st.rerun()
    except FileNotFoundError:
        st.warning("No saved session found.")
    except Exception as e:
        st.error(f"Failed to load session: {str(e)}")





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
        state = get_app_state()
        st.header("📊 Progress")

        def _has_section(state, section_type):
            """Check if tailored_cv has a section of the given type."""
            cv_data = state.get("tailored_cv")
            if not cv_data or not hasattr(cv_data, 'sections'):
                return False
            return any(section_type.lower() in section.name.lower() for section in cv_data.sections)

        progress_items = [
            ("Job Description Parsed", bool(state.get("job_description_data"))),
            ("CV Parsed", bool(state.get("tailored_cv"))),
            ("Qualifications Generated", _has_section(state, "qualifications")),
            ("Human Review Complete", not state.get("human_review_required", False)),
            ("Experience Tailored", _has_section(state, "experience")),
            ("Projects Tailored", _has_section(state, "project")),
            ("Executive Summary", _has_section(state, "summary")),
            ("CV Finalized", bool(state.get("final_cv")))
        ]

        for item, completed in progress_items:
            icon = "✅" if completed else "⏳"
            st.write(f"{icon} {item}")

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
        with st.spinner("🤖 AI is analyzing and tailoring your CV..."):
            try:
                logger.info("Starting CV generation workflow")
                # Run one step of the graph
                new_state = run_graph_step(state)
                update_app_state(new_state)
                logger.info("CV generation step completed successfully")
                st.rerun()
            except Exception as e:
                logger.error(f"CV generation failed: {str(e)}")
                st.error(f"❌ Processing failed: {str(e)}")

def render_section_review_ui(current_step: str) -> None:
    """Render the section-specific review interface."""
    state = get_app_state()

    # Determine which section is being reviewed
    if current_step == "awaiting_qualifications_review":
        render_qualifications_review(state)
    elif current_step == "awaiting_experience_review":
        render_experience_review(state)
    elif current_step == "awaiting_projects_review":
        render_projects_review(state)
    elif current_step == "awaiting_summary_review":
        render_summary_review(state)
    else:
        st.error(f"Unknown review state: {current_step}")

## for post MVP:
## we need to Move the  UI sections Rendering Helper Functions Outside the App.py. =======================================
## Create a new Directory called ui-helpers


## Create a new Python File and call render_summary.py
## Move the render_summary_review function to the render_summary.py file.
def render_summary_review(state: AppState) -> None:
    """Render review interface for executive summary."""
    st.header("📝 Review Executive Summary")
    st.markdown("**Step 4:** Review the AI-generated executive summary and choose to approve or request changes.")

    # Display executive summary from tailored_cv
    cv_data = state.get("tailored_cv")
    if cv_data:
        # Find the Executive Summary section
        summary_section = None
        for section in cv_data.sections:
            if "summary" in section.name.lower() or "executive" in section.name.lower():
                summary_section = section
                break

        if summary_section:
            st.subheader("📄 Generated Executive Summary")
            for entry in summary_section.entries:
                st.markdown(entry.title)
        else:
            st.warning("No executive summary section found in CV.")
    else:
        st.warning("No CV data available.")

    render_approval_buttons(state, "summary", "start_cv_finalization")


## Create a new Python File and call render_qualifications.py
## Move the render_qualifications_review function to the render_qualifications.py file.
def render_qualifications_review(state: AppState) -> None:
    """Render review interface for key qualifications."""
    st.header("📋 Review Key Qualifications")
    st.markdown("**Step 3:** Review the AI-generated key qualifications and choose to approve or request changes.")

    # Display generated qualifications from tailored_cv
    cv_data = state.get("tailored_cv")
    if cv_data:
        # Find the Key Qualifications section
        qualifications_section = None
        for section in cv_data.sections:
            if "qualifications" in section.name.lower():                # we need a better way to search for the section.
                qualifications_section = section
                break

        if qualifications_section:
            st.subheader("🎯 Generated Key Qualifications")
            for i, entry in enumerate(qualifications_section.entries, 1):       # we need a better way to display the generated key qualifications.
                st.markdown(f"• {entry.title}")
        else:
            st.warning("No qualifications section found in CV.")
    else:
        st.warning("No CV data available.")

    render_approval_buttons(state, "qualifications", "start_experience_tailoring")

## Create a new Python File and call render_experience.py
## Move the render_experience_review function to the render_experience.py file.
def render_experience_review(state: AppState) -> None:
    """Render review interface for one-by-one experience tailoring."""
    st.header("💼 Review Experience Entry")

    # Get current progress
    item_index = state.get("item_index", 0)
    source_cv = state.get("source_cv")
    tailored_cv = state.get("tailored_cv")

    if not source_cv or not hasattr(source_cv, 'sections'):
        st.error("No source CV data available for review.")
        return

    # Find source experience entries
    source_experience_entries = []
    for section in source_cv.sections:
        if "experience" in section.name.lower() or "work" in section.name.lower():
            source_experience_entries.extend(section.entries)

    if not source_experience_entries:
        st.warning("No experience entries found in source CV.")
        return

    total_entries = len(source_experience_entries)

    if item_index >= total_entries:
        st.error(f"Invalid item index: {item_index} >= {total_entries}")
        return

    # Show progress
    st.markdown(f"**Progress:** Entry {item_index + 1} of {total_entries}")
    progress_bar = st.progress((item_index + 1) / total_entries)

    # Get current entry being reviewed
    current_entry = source_experience_entries[item_index]

    # Display original vs tailored
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Original Entry")
        with st.container():
            st.markdown(f"**{current_entry.title}**")
            if current_entry.subtitle:
                st.markdown(f"*{current_entry.subtitle}*")
            if current_entry.date_range:
                st.markdown(f"📅 {current_entry.date_range}")
            for detail in current_entry.details:
                st.markdown(f"• {detail}")
            if current_entry.tags:
                st.markdown(f"🏷️ **Skills:** {', '.join(current_entry.tags)}")

    with col2:
        st.subheader("🎯 AI-Tailored Entry")
        # Get the corresponding tailored entry
        tailored_entry = None
        if tailored_cv and hasattr(tailored_cv, 'sections'):
            for section in tailored_cv.sections:
                if "experience" in section.name.lower() or "work" in section.name.lower():
                    if len(section.entries) > item_index:
                        tailored_entry = section.entries[item_index]
                        break

        if tailored_entry:
            with st.container():
                st.markdown(f"**{tailored_entry.title}**")
                if tailored_entry.subtitle:
                    st.markdown(f"*{tailored_entry.subtitle}*")
                if tailored_entry.date_range:
                    st.markdown(f"📅 {tailored_entry.date_range}")
                for detail in tailored_entry.details:
                    st.markdown(f"• {detail}")
                if tailored_entry.tags:
                    st.markdown(f"🏷️ **Skills:** {', '.join(tailored_entry.tags)}")
        else:
            st.warning("Tailored entry not available yet.")

    # Feedback section
    st.divider()
    st.subheader("💬 Your Feedback")
    feedback = st.text_area(
        "Provide feedback for this specific entry (optional for approval, required for revision):",
        value="",
        height=100,
        help="Provide specific feedback on what should be changed, added, or removed for this entry.",
        placeholder="Example: This entry should emphasize cloud technologies more. Please add specific AWS services mentioned in the job description."
    )

    # Action buttons
    st.subheader("🎯 Choose Your Action")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Approve Entry", type="primary", use_container_width=True, help="Accept this tailored entry and move to the next one"):
            logger.info(f"User approved experience entry {item_index + 1}")
            new_state = state.copy()
            new_state["human_feedback"] = feedback
            new_state["human_approved"] = True

            # Increment item_index after user approval (conceptual fix #3)
            new_state["item_index"] = item_index + 1

            if item_index + 1 >= total_entries:
                # All entries processed, move to projects
                new_state["current_step"] = "experience_tailoring_complete"
            else:
                # Continue with next entry
                new_state["current_step"] = "continue_experience_tailoring"

            try:
                # Run the next step immediately
                final_state = run_graph_step(new_state)
                update_app_state(final_state)

                if item_index + 1 >= total_entries:
                    st.success("✅ All experience entries approved! Continuing to projects...")
                else:
                    st.success(f"✅ Entry {item_index + 1} approved! Continuing to entry {item_index + 2}...")
                st.rerun()
            except Exception as e:
                logger.error(f"Failed to continue workflow after approval: {str(e)}")
                st.error(f"❌ Failed to continue: {str(e)}")

    with col2:
        if st.button("🔄 Revise Entry", use_container_width=True, help="Request changes to this specific entry"):
            if feedback.strip():
                logger.info(f"User requested revision for experience entry {item_index + 1}")
                # Store feedback and regenerate this specific entry
                new_state = state.copy()
                new_state["human_feedback"] = feedback
                new_state["human_approved"] = False
                new_state["current_step"] = "continue_experience_tailoring"  # Regenerate current entry

                update_app_state(new_state)
                st.info(f"🔄 Entry {item_index + 1} revision requested! Click 'Generate Tailored CV' to regenerate with your feedback.")
                st.rerun()
            else:
                st.warning("⚠️ Please provide specific feedback before requesting revision.")

    with col3:
        if st.button("⏭️ Skip Entry", use_container_width=True, help="Keep original entry and move to the next one"):
            logger.info(f"User skipped experience entry {item_index + 1}")
            new_state = state.copy()
            new_state["human_approved"] = True  # Semantically, skipping is a form of approval of the original
            new_state["user_intent"] = "skip"

            # Increment item_index after user action
            new_state["item_index"] = item_index + 1

            if item_index + 1 >= total_entries:
                new_state["current_step"] = "experience_tailoring_complete"
            else:
                new_state["current_step"] = "continue_experience_tailoring"

            try:
                # Run the next step immediately
                final_state = run_graph_step(new_state)
                update_app_state(final_state)

                if item_index + 1 >= total_entries:
                    st.success("✅ All experience entries processed! Continuing to projects...")
                else:
                    st.success(f"⏭️ Entry {item_index + 1} skipped! Continuing to entry {item_index + 2}...")
                st.rerun()
            except Exception as e:
                logger.error(f"Failed to continue workflow after approval: {str(e)}")
                st.error(f"❌ Failed to continue: {str(e)}")


## Create a new Python File and call render_projects.py
## Move the render_projects_review function to the render_projects.py file.
def render_projects_review(state: AppState) -> None:
    """Render review interface for projects tailoring."""
    st.header("🚀 Review Tailored Projects")
    st.markdown("**Step 6:** Review the AI-tailored projects section and choose to approve or request changes.")

    # Display tailored projects from tailored_cv
    cv_data = state.get("tailored_cv")
    if cv_data:
        # Find the Projects section(s)
        project_sections = []
        for section in cv_data.sections:
            if "project" in section.name.lower():
                project_sections.append(section)

        if project_sections:
            st.subheader("🎯 Tailored Projects Section")
            for section in project_sections:
                st.markdown(f"**{section.name}**")
                for entry in section.entries:
                    st.markdown(f"**{entry.title}**")
                    if entry.subtitle:
                        st.markdown(f"*{entry.subtitle}*")
                    if entry.date_range:
                        st.markdown(f"📅 {entry.date_range}")
                    for detail in entry.details:
                        st.markdown(f"• {detail}")
                    if entry.tags:
                        st.markdown(f"🏷️ **Technologies:** {', '.join(entry.tags)}")
                    st.markdown("---")
        else:
            st.warning("No projects section found in CV.")
    else:
        st.warning("No CV data available.")

    render_approval_buttons(state, "projects", "start_summary_generation")


## we alse need to render the static sections fron the source cv. =======================================

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

def render_results_section() -> None:
    """Render the results and output section."""
    state = get_app_state()

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
                    # Render structured CV
                    for section in final_cv.sections:
                        st.markdown(f"### {section.name}")
                        for entry in section.entries:
                            if entry.title:
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
                st.rerun()

        return

    # Show intermediate results if any content has been generated
    cv_data = state.get("tailored_cv")
    has_content = cv_data and len(cv_data.sections) > 0

    if has_content:
        st.header("📋 Generated Content")
        st.markdown("**Progress:** AI is working on your CV. Generated sections will appear below.")

        # Show all sections from tailored_cv
        for section in cv_data.sections:
            with st.container():
                st.markdown(f"### 🎯 {section.name}")
                with st.expander(f"View {section.name}", expanded=True):
                    for entry in section.entries:
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

        # Show next steps
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
    render_sidebar()
    render_input_section()

    st.divider()

    render_workflow_controls()

    st.divider()

    render_results_section()

    # Debug section (only in development)
    if st.checkbox("🔧 Show Debug Info"):
        st.subheader("Debug: Current State")
        st.json(get_app_state())

if __name__ == "__main__":
    main()
