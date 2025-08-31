import logging
import streamlit as st
from typing import Callable
from state import AppState
from graph import run_graph_step

logger = logging.getLogger(__name__)


def render_projects_review(state: AppState, update_app_state: Callable[[AppState], None]) -> None:
    """Render review interface for one-by-one project tailoring."""
    st.header("🚀 Review Project Entry")

    # Get current progress
    project_index = state.get("project_index", 0)
    source_cv = state.get("source_cv")
    tailored_cv = state.get("tailored_cv")

    if not source_cv or not hasattr(source_cv, 'sections'):
        st.error("No source CV data available for review.")
        return

    # Find source project entries
    source_project_entries = []
    for section in source_cv.sections:
        if "project" in section.name.lower():
            source_project_entries.extend(section.entries)

    if not source_project_entries:
        st.warning("No project entries found in source CV.")
        return

    total_entries = len(source_project_entries)

    if project_index >= total_entries:
        st.error(f"Invalid project index: {project_index} >= {total_entries}")
        return

    # Show progress
    st.markdown(f"**Progress:** Entry {project_index + 1} of {total_entries}")
    progress_bar = st.progress((project_index + 1) / total_entries)

    # Get current entry being reviewed
    current_entry = source_project_entries[project_index]

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
                st.markdown(f"🏷️ **Technologies:** {', '.join(current_entry.tags)}")

    with col2:
        st.subheader("🎯 Tailored Entry")
        with st.container():
            # Find the tailored entry for this project
            tailored_entry = None
            if tailored_cv and hasattr(tailored_cv, 'sections'):
                for section in tailored_cv.sections:
                    if "project" in section.name.lower():
                        if project_index < len(section.entries):
                            tailored_entry = section.entries[project_index]
                            break

            if tailored_entry:
                st.markdown(f"**{tailored_entry.title}**")
                if tailored_entry.subtitle:
                    st.markdown(f"*{tailored_entry.subtitle}*")
                if tailored_entry.date_range:
                    st.markdown(f"📅 {tailored_entry.date_range}")
                for detail in tailored_entry.details:
                    st.markdown(f"• {detail}")
                if tailored_entry.tags:
                    st.markdown(f"🏷️ **Technologies:** {', '.join(tailored_entry.tags)}")
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
        placeholder="Example: This project should emphasize cloud technologies more. Please add specific AWS services mentioned in the job description."
    )

    # Action buttons
    st.subheader("🎯 Choose Your Action")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Approve Entry", type="primary", use_container_width=True, help="Accept this tailored entry and move to the next one"):
            logger.info(f"User approved project entry {project_index + 1}")
            new_state = state.copy()
            new_state["human_feedback"] = feedback
            new_state["human_approved"] = True

            # Increment project_index after user approval
            new_state["project_index"] = project_index + 1

            if project_index + 1 >= total_entries:
                # All entries processed, move to summary
                new_state["current_step"] = "projects_tailoring_complete"
            else:
                # Continue with next entry
                new_state["current_step"] = "continue_projects_tailoring"

            try:
                # Run the next step immediately
                final_state = run_graph_step(new_state)
                update_app_state(final_state)

                if project_index + 1 >= total_entries:
                    st.success("✅ All project entries approved! Continuing to summary...")
                else:
                    st.success(f"✅ Entry {project_index + 1} approved! Continuing to entry {project_index + 2}...")
                st.rerun()
            except Exception as e:
                logger.error(f"Failed to continue workflow after approval: {str(e)}")
                st.error(f"❌ Failed to continue: {str(e)}")

    with col2:
        if st.button("🔄 Revise Entry", use_container_width=True, help="Request changes to this specific entry"):
            if feedback.strip():
                logger.info(f"User requested revision for project entry {project_index + 1}")
                # Store feedback and regenerate this specific entry
                new_state = state.copy()
                new_state["human_feedback"] = feedback
                new_state["human_approved"] = False
                new_state["current_step"] = "continue_projects_tailoring"  # Regenerate current entry

                update_app_state(new_state)
                st.info(f"🔄 Entry {project_index + 1} revision requested! Click 'Generate Tailored CV' to regenerate with your feedback.")
                st.rerun()
            else:
                st.warning("⚠️ Please provide specific feedback before requesting revision.")

    with col3:
        if st.button("⏭️ Skip Entry", use_container_width=True, help="Keep original entry and move to the next one"):
            logger.info(f"User skipped project entry {project_index + 1}")
            new_state = state.copy()
            new_state["human_approved"] = True  # Semantically, skipping is a form of approval of the original
            new_state["user_intent"] = "skip"

            # Increment project_index after user action
            new_state["project_index"] = project_index + 1

            if project_index + 1 >= total_entries:
                new_state["current_step"] = "projects_tailoring_complete"
            else:
                new_state["current_step"] = "continue_projects_tailoring"

            try:
                # Run the next step immediately
                final_state = run_graph_step(new_state)
                update_app_state(final_state)

                if project_index + 1 >= total_entries:
                    st.success("✅ All project entries processed! Continuing to summary...")
                else:
                    st.success(f"⏭️ Entry {project_index + 1} skipped! Continuing to entry {project_index + 2}...")
                st.rerun()
            except Exception as e:
                logger.error(f"Failed to continue workflow after approval: {str(e)}")
                st.error(f"❌ Failed to continue: {str(e)}")