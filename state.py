"""Application state management.

This module defines the AppState TypedDict which serves as the single source of truth
for all application state. Following the constitutional rules, this is the beginning
and end of all state in the application.
"""

from typing import TypedDict, Optional
from typing_extensions import NotRequired
from models import JobDescriptionData, StructuredCV


class AppState(TypedDict):
    """The canonical representation of the application's memory.
    
    Clean, non-redundant state definition that serves as the single source of truth.
    Only app.py is permitted to read from or write to st.session_state.
    """
    
    # Raw user inputs
    raw_cv_text: NotRequired[str]
    raw_job_description: NotRequired[str]
    
    # Parsed Pydantic objects (not dictionaries)
    job_description_data: NotRequired[JobDescriptionData]
    structured_cv: NotRequired[StructuredCV]
    
    # Note: No separate output models needed - using living document pattern
    # All generated content is directly added to structured_cv
    
    # Workflow control
    current_step: NotRequired[str]  # "input", "parsing", "generating", "complete"
    
    # Human-in-the-loop state
    human_review_required: NotRequired[bool]
    human_feedback: NotRequired[str]
    
    # Error handling
    error_message: NotRequired[str]


def create_initial_state() -> AppState:
    """Create and return the initial application state.
    
    Returns:
        AppState: Fresh application state with default values
    """
    try:
        with open("C:\\Users\\Nitro\\aicvgen\\simplified\\test-cv.txt", "r") as f:
            default_cv = f.read()
    except FileNotFoundError:
        default_cv = ""

    try:
        with open("C:\\Users\\Nitro\\aicvgen\\simplified\\test-jd.txt", "r") as f:
            default_jd = f.read()
    except FileNotFoundError:
        default_jd = ""

    return {
        "raw_cv_text": default_cv,
        "raw_job_description": default_jd,
        "current_step": "input",
        "human_review_required": False
    }
