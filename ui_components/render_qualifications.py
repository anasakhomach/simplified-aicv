"""UI component for rendering qualifications review interface."""

import logging
import streamlit as st
from state import AppState
from typing import Callable

logger = logging.getLogger(__name__)


def render_qualifications_review(state: AppState, render_approval_buttons: Callable) -> None:
    """Render review interface for key qualifications."""
    st.header("📋 Review Key Qualifications")
    st.markdown("**Step 3:** Review the AI-generated key qualifications and choose to approve or request changes.")

    # Create side-by-side layout
    col1, col2 = st.columns(2)

    # Left column: Generated qualifications
    with col1:
        st.subheader("🎯 Generated Key Qualifications")
        cv_data = state.get("tailored_cv")
        if cv_data:
            # Find the Key Qualifications section
            qualifications_section = None
            for section in cv_data.sections:
                if "qualifications" in section.name.lower():
                    qualifications_section = section
                    break

            if qualifications_section:
                # Collect all qualification titles into a list
                qualification_titles = [entry.title for entry in qualifications_section.entries]
                # Display them as a single markdown bulleted list
                st.markdown("- " + "\n- ".join(qualification_titles))
            else:
                st.warning("No qualifications section found in CV.")
        else:
            st.warning("No CV data available.")

    # Right column: Original skills/qualifications using section map
    with col2:
        st.subheader("📄 Original Skills/Qualifications")
        source_data = state.get("source_cv")
        section_map = state.get("section_map")
        original_qualifications_section = None

        if source_data and section_map and section_map.qualifications_source_index is not None:
            try:
                qualifications_index = section_map.qualifications_source_index
                original_qualifications_section = source_data.sections[qualifications_index]
            except IndexError:
                st.warning("Original qualifications section index out of bounds.")

        if original_qualifications_section:
            for entry in original_qualifications_section.entries:
                for detail in entry.details:
                    st.markdown(detail)
        else:
            st.warning("No original skills/qualifications section could be identified in the source CV.")

    render_approval_buttons(state, "qualifications", "start_experience_tailoring")