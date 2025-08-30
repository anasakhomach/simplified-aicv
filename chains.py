"""LangChain LCEL chains for CV generation tasks.

This module contains all chain creation functions. Each function creates one LCEL chain
that performs a single, specific generation task. Following the constitutional rules,
chains create new information by calling the LLM.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from models import (
    JobDescriptionData,
    StructuredCV,
    Section,
    CVEntry
)
from pydantic import BaseModel, Field
from typing import List, Any


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

# Prompt templates
JOB_DESCRIPTION_PARSING_PROMPT = """
You are an expert HR analyst. Parse the following job description and extract structured information.

Job Description:
{job_description}

Extract:
1. Job title
2. Company name (if mentioned)
3. Key responsibilities
4. Required skills with their importance level
5. Preferred skills
6. Experience level required
7. Industry or domain

Be thorough and accurate in your extraction.
"""

KEY_QUALIFICATIONS_PROMPT = """
[System Instruction]
You are an expert CV and LinkedIn profile skill generator. Your goal is to analyze the provided job description and generate a list of the 8 most relevant and impactful skills for a candidate's "Key Qualifications" section.

[Instructions for Skill Generation]
1. **Analyze Job Description:** Carefully read the main job description below. Pay close attention to sections like "Required Qualifications," "Responsibilities," "Ideal Candidate," and "Skills." Prioritize skills mentioned frequently and those listed as essential requirements.

2. **Identify Key Skills:** Extract the 8 most critical core skills and competencies sought by the employer.

3. **Synthesize and Condense:** Rephrase the skills to be concise and impactful. Aim for action-oriented phrases that highlight capabilities. Each skill phrase should be **no longer than 30 characters**.

4. **Format Output:** Return the skills as a valid JSON object with the exact structure shown below. Do not include any additional text, explanations, or formatting outside the JSON.

5. **Generate the "Big 8" Skills:** Create exactly 8 skills that are:
    * Highly relevant to the job description.
    * Concise (under 30 characters).
    * Action-oriented and impactful.
    * Directly aligned with employer requirements.

[Job Description]
{job_requirements}

[Additional Context & Talents to Consider]
{current_skills}

{human_feedback_section}

[Required JSON Output Format]
You must return ONLY a valid JSON object with this exact structure:

```json
{{
  "qualifications": [
    "Data Analysis & Insights",
    "Python for Machine Learning",
    "Strategic Business Planning",
    "Cloud Infrastructure Management",
    "Agile Project Leadership",
    "Advanced SQL & Database Design",
    "Cross-Functional Communication",
    "MLOps & Model Deployment"
  ]
}}
```

**CRITICAL:** Return ONLY the JSON object above. Do not include any explanatory text, markdown formatting, or anything outside of the JSON object.
"""

EXECUTIVE_SUMMARY_PROMPT = """
You are an expert CV writer. Create a compelling executive summary for this candidate using their complete, tailored CV.

Job Description:
{job_description}

Candidate's Complete Enriched CV:
{enriched_cv}

{human_feedback_section}

Write a 3-4 sentence executive summary that:
1. Opens with the candidate's professional identity
2. Highlights years of experience and key expertise from their tailored experience
3. Mentions 2-3 most relevant achievements or skills from their enriched qualifications and projects
4. Concludes with value proposition for this specific role

Use the enriched CV content (qualifications, tailored experience, tailored projects) to create the most compelling and accurate summary.
"""

EXPERIENCE_TAILORING_PROMPT = """
You are an expert CV writer. Tailor this single work experience entry for the specific job using the candidate's key qualifications as context.

Target Job:
{job_description}

Candidate's Key Qualifications (for context):
{key_qualifications}

Current Experience Entry to Tailor:
{current_entry}

For this experience entry:
1. Emphasize responsibilities that match the job requirements and align with the key qualifications
2. Quantify achievements where possible
3. Highlight relevant technologies and skills that support the qualifications
4. Use action verbs and industry keywords from both job description and qualifications
5. Remove or de-emphasize irrelevant details
6. Ensure consistency with the established key qualifications

Return the tailored entry as a CVEntry object with:
- title: Job title
- subtitle: Company name
- date_range: Employment period
- details: List of tailored bullet points
- tags: List of relevant skills/technologies

Maintain truthfulness while optimizing for relevance and coherence with qualifications.
"""

PROJECTS_TAILORING_PROMPT = """
You are an expert CV writer. Tailor the candidate's projects section for this specific job using their qualifications and tailored experience as context.

Target Job:
{job_description}

Candidate's Key Qualifications (for context):
{key_qualifications}

Candidate's Tailored Experience (for context):
{tailored_experience}

Candidate's Projects:
{current_projects}

For each relevant project:
1. Highlight technologies and skills that match job requirements and complement the qualifications and experience
2. Emphasize outcomes and impact that reinforce the established narrative
3. Connect project work to job responsibilities and demonstrated experience
4. Use technical keywords from the job description, qualifications, and experience
5. Focus on the most relevant 3-4 projects that strengthen the overall profile
6. Ensure consistency with qualifications and experience sections

Return the tailored sections as Section objects with:
- name: MUST be exactly "Projects" (standardized section name)
- entries: List of CVEntry objects with title, subtitle, date_range, details (list of strings), and tags (list of strings)

Provide tailored project descriptions that create a cohesive, compelling narrative.
"""


def create_job_description_parsing_chain():
    """Create a chain to parse job descriptions into structured data."""
    logger.info("Creating job description parsing chain")

    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS
    )

    prompt = ChatPromptTemplate.from_template(JOB_DESCRIPTION_PARSING_PROMPT)

    def log_chain_execution(inputs: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing job description parsing chain with input length: {len(inputs.get('job_description', ''))} characters")
        return inputs

    def log_chain_result(result: JobDescriptionData) -> JobDescriptionData:
        logger.info(f"Job description parsing completed. Extracted job title: {result.job_title}")
        return result

    chain = RunnablePassthrough.assign(**{}) | RunnableLambda(log_chain_execution) | prompt | llm.with_structured_output(JobDescriptionData) | RunnableLambda(log_chain_result)
    return chain


def create_key_qualifications_chain():
    """Create a chain to generate key qualifications."""
    logger.info("Creating key qualifications chain")

    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS
    )

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

    prompt = ChatPromptTemplate.from_template(KEY_QUALIFICATIONS_PROMPT)

    def log_chain_execution(inputs: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing key qualifications chain")
        return inputs

    def log_chain_result(result: QualificationsOutput) -> QualificationsOutput:
        logger.info(f"Key qualifications generation completed. Generated {len(result.qualifications)} qualifications")
        return result

    chain = RunnableLambda(prepare_inputs) | RunnableLambda(log_chain_execution) | prompt | llm.with_structured_output(QualificationsOutput) | RunnableLambda(log_chain_result)
    return chain


def create_executive_summary_chain():
    """Create a chain to generate executive summaries."""
    logger.info("Creating executive summary chain")

    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS
    )

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

    prompt = ChatPromptTemplate.from_template(EXECUTIVE_SUMMARY_PROMPT)

    def log_chain_execution(inputs: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing executive summary chain")
        return inputs

    def log_chain_result(result: SummaryOutput) -> SummaryOutput:
        logger.info(f"Executive summary generation completed. Summary length: {len(result.summary)} characters")
        return result

    chain = RunnableLambda(prepare_inputs) | RunnableLambda(log_chain_execution) | prompt | llm.with_structured_output(SummaryOutput) | RunnableLambda(log_chain_result)
    return chain


def create_experience_tailoring_chain():
    """Create a chain to tailor work experience entries."""
    logger.info("Creating experience tailoring chain")

    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS
    )

    prompt = ChatPromptTemplate.from_template(EXPERIENCE_TAILORING_PROMPT)

    def log_chain_execution(inputs: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing experience tailoring chain")
        return inputs

    def log_chain_result(result: TailoredEntryOutput) -> TailoredEntryOutput:
        logger.info(f"Experience entry tailoring completed for: {result.tailored_entry.title}")
        return result

    chain = RunnablePassthrough.assign(**{}) | RunnableLambda(log_chain_execution) | prompt | llm.with_structured_output(TailoredEntryOutput) | RunnableLambda(log_chain_result)
    return chain


def create_projects_tailoring_chain():
    """Create a chain to tailor projects section."""
    logger.info("Creating projects tailoring chain")

    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS
    )

    prompt = ChatPromptTemplate.from_template(PROJECTS_TAILORING_PROMPT)

    def log_chain_execution(inputs: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing projects tailoring chain")
        return inputs

    def log_chain_result(result: TailoringOutput) -> TailoringOutput:
        logger.info(f"Projects tailoring completed. Tailored {len(result.tailored_sections)} projects")
        return result

    chain = RunnablePassthrough.assign(**{}) | RunnableLambda(log_chain_execution) | prompt | llm.with_structured_output(TailoringOutput) | RunnableLambda(log_chain_result)
    return chain


def create_cv_parsing_chain():
    """Create a chain to parse raw CV text into structured format."""
    logger.info("Creating CV parsing chain")

    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS
    )

    prompt = ChatPromptTemplate.from_template(
        """You are an expert CV parser. Extract information from the CV text and return ONLY a valid JSON object.

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no explanations, no markdown, no extra text
2. Every entry MUST have a "title" field - this is required
3. personal_info must be a JSON object with separate fields for name, email, phone
4. Use null for optional fields that are empty
5. MANDATORY SECTION NAMING: When you find work experience/employment history, the section name MUST be exactly "Experience"
6. MANDATORY SECTION NAMING: When you find projects/portfolio work, the section name MUST be exactly "Projects"

JSON STRUCTURE:
{{
  "personal_info": {{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "phone number"
  }},
  "sections": [
    {{
      "name": "Experience",
      "entries": [
        {{
          "title": "Job Title",
          "subtitle": "Company Name",
          "date_range": "2020-2023",
          "details": ["Achievement 1", "Achievement 2"],
          "tags": ["Skill1", "Skill2"]
        }}
      ]
    }}
  ]
}}

SECTION NAMING GUIDE:
- Work experience/employment history → MUST use "Experience"
- Projects/portfolio work → MUST use "Projects"
- Education/academic background → Use "Education"
- Skills/technical abilities → Use "Skills"
- Certifications → Use "Certifications"
- Languages → Use "Languages"

TITLE EXAMPLES:
- Experience: "Data Scientist", "Software Engineer"
- Education: "Master of Science in Data Science", "Bachelor of Computer Science"
- Skills: "Technical Skills", "Programming Languages"
- Certifications: "Google Analytics Certified", "AWS Solutions Architect"
- Languages: "Languages"

CV Text to parse:
{cv_text}

Return the JSON object:"""
    )

    def log_chain_execution(inputs: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing CV parsing chain with input length: {len(inputs.get('cv_text', ''))} characters")
        return inputs

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

    json_parser = JsonOutputParser()
    chain = RunnablePassthrough.assign(**{}) | RunnableLambda(log_chain_execution) | prompt | llm | json_parser | RunnableLambda(parse_and_validate_cv)
    return chain