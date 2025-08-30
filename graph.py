"""LangGraph workflow definition for CV generation.

This module defines the graph structure that orchestrates the CV generation process.
The graph acts as a stateless function that takes AppState and returns updated AppState.
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from state import AppState
from nodes import (
    parse_job_description_node,
    parse_cv_node,
    setup_iterative_session_node,
    generate_key_qualifications_node,
    request_human_review_node,
    generate_executive_summary_node,
    tailor_experience_node,
    should_continue_experience_node,
    tailor_projects_node,
    finalize_cv_node
)

# Configure logging
logger = logging.getLogger(__name__)

# Constants for node names
PARSE_JD_NODE = "parse_job_description"
PARSE_CV_NODE = "parse_cv"
SETUP_ITERATIVE_SESSION_NODE = "setup_iterative_session"
GENERATE_QUALIFICATIONS_NODE = "generate_qualifications"
HUMAN_REVIEW_NODE = "human_review"
GENERATE_SUMMARY_NODE = "generate_summary"
TAILOR_EXPERIENCE_NODE = "tailor_experience"
SHOULD_CONTINUE_EXPERIENCE_NODE = "should_continue_experience"
TAILOR_PROJECTS_NODE = "tailor_projects"
FINALIZE_CV_NODE = "finalize_cv"

def create_cv_generation_graph() -> StateGraph:
    """Create and configure the CV generation workflow graph.
    
    Returns:
        StateGraph: Configured graph ready for execution
    """
    # Initialize the graph with AppState
    workflow = StateGraph(AppState)
    
    # Add nodes to the graph
    workflow.add_node(PARSE_JD_NODE, parse_job_description_node)
    workflow.add_node(PARSE_CV_NODE, parse_cv_node)
    workflow.add_node(SETUP_ITERATIVE_SESSION_NODE, setup_iterative_session_node)
    workflow.add_node(GENERATE_QUALIFICATIONS_NODE, generate_key_qualifications_node)
    workflow.add_node(HUMAN_REVIEW_NODE, request_human_review_node)
    workflow.add_node(GENERATE_SUMMARY_NODE, generate_executive_summary_node)
    workflow.add_node(TAILOR_EXPERIENCE_NODE, tailor_experience_node)
    workflow.add_node(SHOULD_CONTINUE_EXPERIENCE_NODE, should_continue_experience_node)
    workflow.add_node(TAILOR_PROJECTS_NODE, tailor_projects_node)
    workflow.add_node(FINALIZE_CV_NODE, finalize_cv_node)
    
    # Set entry point to use router
    workflow.set_entry_point("router")
    
    # Add router node that determines next step based on current_step
    workflow.add_node("router", lambda state: state)  # Pass-through node
    
    # Router determines which node to go to next
    workflow.add_conditional_edges(
        "router",
        workflow_router,
        {
            PARSE_JD_NODE: PARSE_JD_NODE,
            PARSE_CV_NODE: PARSE_CV_NODE,
            SETUP_ITERATIVE_SESSION_NODE: SETUP_ITERATIVE_SESSION_NODE,
            GENERATE_QUALIFICATIONS_NODE: GENERATE_QUALIFICATIONS_NODE,
            GENERATE_SUMMARY_NODE: GENERATE_SUMMARY_NODE,
            TAILOR_EXPERIENCE_NODE: TAILOR_EXPERIENCE_NODE,
            SHOULD_CONTINUE_EXPERIENCE_NODE: SHOULD_CONTINUE_EXPERIENCE_NODE,
            TAILOR_PROJECTS_NODE: TAILOR_PROJECTS_NODE,
            FINALIZE_CV_NODE: FINALIZE_CV_NODE,
            END: END
        }
    )
    
    # All nodes return to router for next step determination
    workflow.add_edge(PARSE_JD_NODE, "router")
    workflow.add_edge(PARSE_CV_NODE, "router")
    workflow.add_edge(SETUP_ITERATIVE_SESSION_NODE, "router")
    workflow.add_edge(GENERATE_QUALIFICATIONS_NODE, "router")
    workflow.add_edge(HUMAN_REVIEW_NODE, "router")
    workflow.add_edge(GENERATE_SUMMARY_NODE, "router")
    workflow.add_edge(TAILOR_EXPERIENCE_NODE, "router")
    workflow.add_edge(SHOULD_CONTINUE_EXPERIENCE_NODE, "router")
    workflow.add_edge(TAILOR_PROJECTS_NODE, "router")
    workflow.add_edge(FINALIZE_CV_NODE, "router")
    
    return workflow.compile()

def workflow_router(state: AppState) -> str:
    """Central router that determines the next node based on current_step.
    
    New sequential enrichment pattern:
    1. Parse JD → Parse CV → Generate Qualifications
    2. Tailor Experience (using qualifications)
    3. Tailor Projects (using qualifications + experience)
    4. Generate Summary (using complete enriched CV)
    5. Finalize
    """
    current_step = state.get("current_step", "input")
    
    # Handle pause states - any 'awaiting' state should stop the workflow
    if "awaiting" in current_step:
        return END
    
    # Route based on current step - LIVING DOCUMENT PATTERN
    if current_step == "input":
        return PARSE_JD_NODE
    elif current_step == "job_description_parsed":
        return PARSE_CV_NODE
    elif current_step == "cv_parsed":
        return SETUP_ITERATIVE_SESSION_NODE
    elif current_step == "iterative_session_ready":
        return GENERATE_QUALIFICATIONS_NODE
    elif current_step == "qualifications_approved" or current_step == "start_experience_tailoring":
        return TAILOR_EXPERIENCE_NODE
    elif current_step == "experience_entry_tailored":
        return SHOULD_CONTINUE_EXPERIENCE_NODE
    elif current_step == "continue_experience_tailoring":
        return TAILOR_EXPERIENCE_NODE
    elif current_step == "experience_tailoring_complete" or current_step == "start_projects_tailoring":
        return TAILOR_PROJECTS_NODE
    elif current_step == "projects_approved" or current_step == "start_summary_generation":
        return GENERATE_SUMMARY_NODE
    elif current_step == "summary_approved" or current_step == "start_cv_finalization":
        return FINALIZE_CV_NODE
    elif current_step == "cv_finalized":
        return END
    elif current_step == "cv_parsing_failed":
        return END
    else:
        logger.warning(f"Unknown current_step: {current_step}")
        return END

# Old conditional functions removed - using router pattern now

def run_graph_step(state: AppState) -> AppState:
    """Execute one step of the graph workflow.
    
    This function is called by app.py to advance the workflow.
    It creates a fresh graph instance and invokes it with the current state.
    
    Args:
        state: Current application state
        
    Returns:
        AppState: Updated state after graph execution
    """
    try:
        logger.info(f"Starting graph execution with state: {state.get('current_step', 'unknown')}")
        graph = create_cv_generation_graph()
        result = graph.invoke(state)
        
        # Ensure we return a valid AppState
        if isinstance(result, dict):
            logger.info(f"Graph execution completed successfully. New step: {result.get('current_step', 'unknown')}")
            return result
        else:
            # Fallback if graph returns unexpected format
            logger.error("Graph returned unexpected format")
            return {
                **state,
                "error_message": "Graph returned unexpected format",
                "has_error": True
            }
            
    except Exception as e:
        # Handle any graph execution errors
        logger.error(f"Graph execution failed: {str(e)}")
        return {
            **state,
            "error_message": f"Graph execution failed: {str(e)}",
            "has_error": True
        }