"""UI component for rendering summary review interface."""

import logging
import streamlit as st
from state import AppState
from typing import Callable

logger = logging.getLogger(__name__)


def render_summary_review(state: AppState, render_approval_buttons: Callable) -> None:
    """Render review interface for executive summary."""
    st.header("📝 Review Executive Summary")
    st.markdown("**Step 2:** Review the AI-generated executive summary and choose to approve or request changes.")

    # Create side-by-side layout
    col1, col2 = st.columns(2)

    # Left column: Generated summary
    with col1:
        st.subheader("🎯 Generated Executive Summary")
        cv_data = state.get("tailored_cv")
        if cv_data:
            # Find the Executive Summary section
            summary_section = None
            for section in cv_data.sections:
                if "summary" in section.name.lower() or "executive" in section.name.lower():
                    summary_section = section
                    break

            if summary_section and summary_section.entries:
                # Display the summary content
                summary_entry = summary_section.entries[0]  # Should be only one entry for summary
                st.markdown(f"**{summary_entry.title}**")
                for detail in summary_entry.details:
                    st.markdown(detail)
            else:
                st.warning("No executive summary found in CV.")
        else:
            st.warning("No CV data available.")

    # Right column: Original summary using section map
    with col2:
        st.subheader("📄 Original Summary/Profile")
        source_data = state.get("source_cv")
        section_map = state.get("section_map")
        original_summary_section = None

        if source_data and section_map and section_map.executive_summary_source_index is not None:
            try:
                summary_index = section_map.executive_summary_source_index
                original_summary_section = source_data.sections[summary_index]
            except IndexError:
                st.warning("Original summary section index out of bounds.")

        if original_summary_section:
            for entry in original_summary_section.entries:
                for detail in entry.details:
                    st.markdown(detail)
        else:
            st.warning("No original summary/profile section could be identified in the source CV.")

    render_approval_buttons(state, "summary", "start_cv_finalization")