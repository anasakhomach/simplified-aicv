# latex_graph.py
"""
LaTeX Generation Graph Module

This module implements a LangGraph-based workflow for generating PDF documents from CV data.
The graph handles LaTeX generation, compilation, error detection, and automatic fixing with retry logic.
"""

import logging
from typing import TypedDict
from langgraph.graph import StateGraph, END
from models import StructuredCV
from latex_generator import generate_latex_string
from latex_compiler import compile_latex_to_pdf
from chains import create_latex_fixer_chain

logger = logging.getLogger(__name__)

class LatexAgentState(TypedDict):
    """
    State dictionary for the LaTeX generation workflow.

    Attributes:
        cv_data: Structured CV data containing all resume information
        latex_string: Generated LaTeX code as a string
        pdf_bytes: Compiled PDF document as bytes (None if compilation failed)
        error_log: LaTeX compilation error messages (None if successful)
        retries: Number of fix attempts made during the current workflow
    """
    cv_data: StructuredCV
    latex_string: str
    pdf_bytes: bytes
    error_log: str
    retries: int

MAX_RETRIES = 5  # Maximum number of automatic fix attempts before giving up

def generate_node(state: LatexAgentState):
    """
    Generate LaTeX code from structured CV data.

    This is the entry point of the LaTeX generation workflow. It takes the structured
    CV data and converts it into a LaTeX string using the latex_generator module.

    Args:
        state: Current workflow state containing cv_data

    Returns:
        dict: Updated state with generated latex_string
    """
    logger.info("Generating LaTeX string...")
    latex_string = generate_latex_string(state['cv_data'])
    return {"latex_string": latex_string}

def compile_node(state: LatexAgentState):
    """
    Compile LaTeX code into a PDF document.

    Takes the generated LaTeX string and attempts to compile it into a PDF using
    the latex_compiler module. Handles both successful compilation and error cases.

    Args:
        state: Current workflow state containing latex_string

    Returns:
        dict: Updated state with either pdf_bytes (success) or error_log (failure)
    """
    logger.info("Compiling LaTeX string...")
    latex_string = state['latex_string']
    result = compile_latex_to_pdf(latex_string)
    if result['success']:
        return {"pdf_bytes": result['pdf_bytes'], "error_log": None}
    else:
        return {"pdf_bytes": None, "error_log": result['log']}

def reflect_and_fix_node(state: LatexAgentState):
    """
    Analyze compilation errors and attempt to fix the LaTeX code.

    This node is called when LaTeX compilation fails. It uses an LLM-based fixer chain
    to analyze the error log and generate corrected LaTeX code. Includes logic to detect
    when the fixer fails to make changes and terminates the retry loop to prevent infinite loops.
    Now handles structured output from the enhanced fixer chain.

    Args:
        state: Current workflow state containing latex_string and error_log

    Returns:
        dict: Updated state with either corrected latex_string and incremented retries,
              or error termination when fixer fails to make changes
    """
    logger.info("Reflecting on error and attempting to fix...")
    fixer_chain = create_latex_fixer_chain()

    faulty_code = state['latex_string']
    error_log = state['error_log']

    corrected_latex = fixer_chain.invoke({
        "faulty_code": faulty_code,
        "error_log": error_log
    })

    # If the fixer chain returns the same broken code, terminate the loop.
    if corrected_latex.strip() == faulty_code.strip():
        logger.warning("Fixer chain failed to produce a change. Terminating loop.")
        return {
            "error_log": "The LaTeX fixer failed to modify the code, terminating.",
            "retries": MAX_RETRIES # Set retries to max to force an end state.
        }
    else:
        logger.info("Fixer chain provided a new version of the code. Retrying compilation.")
        return {
            "latex_string": corrected_latex,
            "retries": state.get('retries', 0) + 1
        }

def should_retry(state: LatexAgentState):
    """
    Determine the next step in the workflow based on compilation results and retry count.

    This conditional edge function evaluates the current state to decide whether to:
    - End successfully (no errors)
    - End with failure (max retries reached)
    - Continue with error fixing (errors present, retries available)

    Args:
        state: Current workflow state containing error_log and retries

    Returns:
        str: Next node name - "end", "end_with_error", or "reflect_and_fix"
    """
    if state['error_log'] is None:
        logger.info("Compilation successful. Ending graph.")
        return "end"
    elif state.get('retries', 0) >= MAX_RETRIES:
        logger.error("Max retries reached. Ending graph with failure.")
        return "end_with_error"
    else:
        logger.info("Compilation failed. Retrying with fix...")
        return "reflect_and_fix"

# Create the graph
workflow = StateGraph(LatexAgentState)
workflow.add_node("generate", generate_node)
workflow.add_node("compile", compile_node)
workflow.add_node("reflect_and_fix", reflect_and_fix_node)

workflow.set_entry_point("generate")
workflow.add_edge("generate", "compile")
workflow.add_conditional_edges(
    "compile",
    should_retry,
    {
        "end": END,
        "end_with_error": END,
        "reflect_and_fix": "reflect_and_fix"
    }
)
workflow.add_edge("reflect_and_fix", "compile")

latex_generation_graph = workflow.compile()