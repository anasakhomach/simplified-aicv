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
    
    # Parsed Pydantic objects
    job_description_data: NotRequired[JobDescriptionData]
    structured_cv: NotRequired[StructuredCV]  # Transient key for passing parsed CV
    
    # Iterative processing state (workbench model)
    source_cv: NotRequired[StructuredCV]      # Read-only original CV
    tailored_cv: NotRequired[StructuredCV]     # Work-in-progress "living document"
    item_index: NotRequired[int]               # Current item for iterative review
    
    # Final output
    final_cv: NotRequired[StructuredCV]
    
    # Workflow control
    current_step: NotRequired[str]
    workflow_complete: NotRequired[bool]
    
    # Human-in-the-loop state
    human_review_required: NotRequired[bool]
    human_feedback: NotRequired[str]
    human_approved: NotRequired[bool]
    user_intent: NotRequired[str]  # For signaling user actions like "skip"
    
    # Error handling
    error_message: NotRequired[str]
    has_error: NotRequired[bool]


def get_initial_state() -> AppState:
    """Create initial application state with default values.
    
    Returns:
        AppState: Initial state with default CV and JD loaded
    """
    # Read default files
    with open("test-cv.txt", "r", encoding="utf-8") as f:
        default_cv = f.read()
    
    with open("test-jd.txt", "r", encoding="utf-8") as f:
        default_jd = f.read()
    
    return {
        "raw_cv_text": default_cv,
        "raw_job_description": default_jd,
        "current_step": "input",
        "human_review_required": False,
        "item_index": 0
    }
