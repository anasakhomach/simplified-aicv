"""Prompt templates for CV generation tasks.

This module contains all prompt templates used by the chains. Following the constitutional
rules, all configuration (including prompt templates) should be centralized and hard-coded
as constants.
"""

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
You are an expert CV writer. Tailor this single project entry for the specific job using the candidate's key qualifications as context.

Target Job:
{job_description}

Candidate's Key Qualifications (for context):
{key_qualifications}

Current Project Entry to Tailor:
{current_entry}

For this project entry:
1. Highlight technologies and skills that match job requirements and align with the key qualifications
2. Emphasize outcomes and impact that demonstrate relevant capabilities
3. Connect project work to job responsibilities and requirements
4. Use technical keywords from the job description and qualifications
5. Remove or de-emphasize irrelevant details
6. Ensure consistency with the established key qualifications

Return the tailored entry as a CVEntry object with:
- title: Project title
- subtitle: Organization/context (if applicable)
- date_range: Project timeframe
- details: List of tailored bullet points highlighting relevant achievements
- tags: List of relevant technologies/skills

Maintain truthfulness while optimizing for relevance and coherence with qualifications.
"""

CV_PARSING_PROMPT = """You are an expert CV parser. Extract information from the CV text and return ONLY a valid JSON object.

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

SECTION_MAPPING_PROMPT = """
You are an expert CV analyst tasked with mapping ambiguous sections to standardized concepts.
Analyze the following CV, provided as a JSON object. Your goal is to identify which section index corresponds to the concepts of "executive summary" and "qualifications".

The CV JSON object:
{source_cv_json}

**Instructions:**
1.  **Executive Summary:** Find the section that acts as a professional summary, profile, or objective. This is usually a short, paragraph-style section near the top of the CV.
2.  **Qualifications/Skills:** Find the section that lists the candidate's skills, technologies, or core competencies. It might be called "Skills", "Technical Skills", "Key Qualifications", etc.
3.  **Determine the Index:** Identify the 0-based index of these sections within the main `sections` array of the JSON.
4.  **Return JSON:** You MUST return ONLY a single, valid JSON object with the following keys:
    - `executive_summary_source_index`: The integer index of the summary/profile section. If no such section is found, the value must be `null`.
    - `qualifications_source_index`: The integer index of the skills/qualifications section. If no such section is found, the value must be `null`.

**Example Output:**
{{
  "executive_summary_source_index": 0,
  "qualifications_source_index": 4
}}

**CRITICAL:** Do not include any explanations, markdown, or any text outside of the single JSON object in your response.
"""

LATEX_FIXER_PROMPT = """You are an expert LaTeX debugger. A user's LaTeX code failed to compile.
Your task is to analyze the error log and the faulty code, identify the mistake, and provide a fully corrected version of the code.

**Analysis Steps:**
1.  **Read the Error Log:** Look for specific error messages like "Missing }}", "Undefined control sequence", or "File ended while scanning".
2.  **Locate the Error:** Pinpoint the exact line or section in the "FAULTY LATEX CODE" that is causing the error.
3.  **Hypothesize the Fix:** Determine the most likely cause. For example, a missing closing bracket, a misspelled command, or an unescaped special character.
4.  **Construct the Correction:** Rewrite the entire LaTeX code block with the fix applied. Do not explain the fix, just provide the complete, corrected code.

**Error Log:**
{error_log}

**Faulty LaTeX Code:**
{faulty_code}

**Corrected, Complete LaTeX Code:**
"""