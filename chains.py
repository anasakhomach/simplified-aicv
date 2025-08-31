"""LangChain LCEL chains for CV generation tasks.

This module contains all chain creation functions. Each function creates one LCEL chain
that performs a single, specific generation task. Following the constitutional rules,
chains create new information by calling the LLM.
"""
# pylint: disable=logging-fstring-interpolation
# pylint: disable=line-too-long

import logging
from typing import List, Any, Dict

from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from models import (
    JobDescriptionData,
    StructuredCV,
    Section,
    CVEntry,
    SectionMap
)
from prompts import (
    JOB_DESCRIPTION_PARSING_PROMPT,
    KEY_QUALIFICATIONS_PROMPT,
    EXECUTIVE_SUMMARY_PROMPT,
    EXPERIENCE_TAILORING_PROMPT,
    PROJECTS_TAILORING_PROMPT,
    CV_PARSING_PROMPT,
    SECTION_MAPPING_PROMPT,
)



def clean_llm_output(data: Any) -> Any:
    """Recursively clean LLM output to ensure compatibility with Pydantic models.

    This function standardizes the LLM output at the boundary where unstructured
    output is forced into our strict StructuredCV Pydantic model. It handles:
    - Converting null values to empty lists for 'tags' fields
    - Recursively processing nested structures
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if key == 'tags' and value is None:
                # Replace null tags with empty list
                cleaned[key] = []
            else:
                # Recursively clean nested structures
                cleaned[key] = clean_llm_output(value)
        return cleaned
    elif isinstance(data, list):
        # Recursively clean list items
        return [clean_llm_output(item) for item in data]
    else:
        # Return primitive values as-is
        return data

# Local Pydantic classes for chain outputs (living document pattern)
class QualificationsOutput(BaseModel):
    """Output for key qualifications generation."""
    qualifications: List[str]

class TailoringOutput(BaseModel):
    """Output for experience/projects tailoring."""
    tailored_sections: List[Section]

class TailoredEntryOutput(BaseModel):
    """Output for single experience entry tailoring."""
    tailored_entry: CVEntry

class SummaryOutput(BaseModel):
    """Output for executive summary generation."""
    summary: str

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
MODEL_NAME = "gemini-2.0-flash"
TEMPERATURE = 0.3
MAX_OUTPUT_TOKENS = 2048

# Shared LLM instance
llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    max_output_tokens=MAX_OUTPUT_TOKENS
)

# Prompt templates are now imported from prompts.py

def _create_structured_output_chain(prompt_template: str, output_schema: BaseModel, chain_name: str, input_preprocessor=None):
    """Generic factory function to create structured output chains.

    Args:
        prompt_template: The prompt template string
        output_schema: The Pydantic model for structured output
        chain_name: Name for logging purposes
        input_preprocessor: Optional function to preprocess inputs
    """
    logger.info(f"Creating {chain_name.lower()} chain")

    prompt = ChatPromptTemplate.from_template(prompt_template)

    def log_chain_execution(inputs: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing {chain_name.lower()} chain")
        return inputs

    def log_chain_result(result) -> Any:
        logger.info(f"{chain_name} completed")
        return result

    # Build the chain with optional input preprocessing
    if input_preprocessor:
        chain = RunnableLambda(input_preprocessor) | RunnableLambda(log_chain_execution) | prompt | llm.with_structured_output(output_schema) | RunnableLambda(log_chain_result)
    else:
        chain = RunnablePassthrough.assign(**{}) | RunnableLambda(log_chain_execution) | prompt | llm.with_structured_output(output_schema) | RunnableLambda(log_chain_result)

    return chain

def _create_json_parsing_chain(prompt_template: str, chain_name: str, result_processor):
    """Generic factory function for JSON parsing chains.

    Args:
        prompt_template: The prompt template string
        chain_name: Name for logging purposes
        result_processor: Function to process the JSON result
    """
    logger.info(f"Creating {chain_name.lower()} chain")

    prompt = ChatPromptTemplate.from_template(prompt_template)

    def log_chain_execution(inputs: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing {chain_name.lower()} chain")
        return inputs

    json_parser = JsonOutputParser()
    chain = RunnablePassthrough.assign(**{}) | RunnableLambda(log_chain_execution) | prompt | llm | json_parser | RunnableLambda(result_processor)
    return chain

def create_job_description_parsing_chain():
    """Create a chain to parse job descriptions into structured data."""
    return _create_structured_output_chain(
        prompt_template=JOB_DESCRIPTION_PARSING_PROMPT,
        output_schema=JobDescriptionData,
        chain_name="Job Description Parsing"
    )

def create_cv_parsing_chain():
    """Create a chain to parse raw CV text into structured format."""
    def parse_and_validate_cv(json_result: dict) -> StructuredCV:
        """Parse JSON result and validate it as StructuredCV."""
        try:
            # Clean the JSON data before validation
            cleaned_data = clean_llm_output(json_result)

            # Create StructuredCV from the cleaned JSON
            structured_cv = StructuredCV(**cleaned_data)
            name = structured_cv.personal_info['name'] if structured_cv.personal_info and 'name' in structured_cv.personal_info else 'Unknown'
            logger.info(f"CV parsing completed. Parsed CV for: {name}")
            return structured_cv
        except Exception as e:
            logger.error(f"Failed to validate parsed CV: {e}")
            raise

    return _create_json_parsing_chain(
        prompt_template=CV_PARSING_PROMPT,
        chain_name="CV Parsing",
        result_processor=parse_and_validate_cv
    )

def create_key_qualifications_chain():
    """Create a chain to generate key qualifications."""
    def prepare_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare inputs by adding human feedback section if provided."""
        prepared = inputs.copy()

        if "human_feedback" in inputs and inputs["human_feedback"]:
            prepared["human_feedback_section"] = f"""
            [Human Feedback - IMPORTANT]
            The user has provided specific feedback on the previous qualifications. Please incorporate this feedback:
            {inputs['human_feedback']}

            Adjust the qualifications based on this feedback while maintaining relevance to the job description."""
        else:
            prepared["human_feedback_section"] = ""

        return prepared

    return _create_structured_output_chain(
        prompt_template=KEY_QUALIFICATIONS_PROMPT,
        output_schema=QualificationsOutput,
        chain_name="Key Qualifications",
        input_preprocessor=prepare_inputs
    )

def create_experience_tailoring_chain():
    """Create a chain to tailor work experience entries."""
    return _create_structured_output_chain(
        prompt_template=EXPERIENCE_TAILORING_PROMPT,
        output_schema=TailoredEntryOutput,
        chain_name="Experience Tailoring"
    )

def create_projects_tailoring_chain():
    """Create a chain to tailor projects section."""
    return _create_structured_output_chain(
        prompt_template=PROJECTS_TAILORING_PROMPT,
        output_schema=TailoredEntryOutput,
        chain_name="Projects Tailoring"
    )

def create_executive_summary_chain():
    """Create a chain to generate executive summaries."""
    def prepare_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare inputs by adding human feedback section if provided."""
        prepared = inputs.copy()

        if "human_feedback" in inputs and inputs["human_feedback"]:
            prepared["human_feedback_section"] = f"""
            [Human Feedback - IMPORTANT]
            The user has provided specific feedback on the previous executive summary. Please incorporate this feedback:
            {inputs['human_feedback']}

            Adjust the executive summary based on this feedback while maintaining relevance to the job description and CV content."""
        else:
            prepared["human_feedback_section"] = ""

        return prepared

    return _create_structured_output_chain(
        prompt_template=EXECUTIVE_SUMMARY_PROMPT,
        output_schema=SummaryOutput,
        chain_name="Executive Summary",
        input_preprocessor=prepare_inputs
    )

def create_section_mapping_chain():
    """Create a chain to map CV sections to standardized concepts."""
    return _create_structured_output_chain(
        prompt_template=SECTION_MAPPING_PROMPT,
        output_schema=SectionMap,
        chain_name="Section Mapping"
    )
