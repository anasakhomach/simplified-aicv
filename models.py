"""Pydantic models for data structures.

This module contains all Pydantic models used throughout the application.
Following the constitutional rules, these are the only classes permitted
in the project besides AppState TypedDict.
"""

from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field



class ExperienceLevel(str, Enum):
    """Experience level requirements."""
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"


class WorkPolicy(str, Enum):
    """Work arrangement policies."""
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    FLEXIBLE = "flexible"


class SkillRequirement(BaseModel):
    """A skill requirement extracted from a job description."""
    name: str = Field(description="The specific skill or technology")
    is_required: bool = Field(description="True if required, False if preferred/nice-to-have")
    context: Optional[str] = Field(default=None, description="Context or details about how this skill is used")


class JobDescriptionData(BaseModel):
    """Optimized structured data extracted from a job description."""
    job_title: str = Field(description="The job title")
    company: Optional[str] = Field(default=None, description="Company name if mentioned")
    key_responsibilities: List[str] = Field(description="Main responsibilities listed")
    technical_skills: List[SkillRequirement] = Field(description="Technical skills with requirement level")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills mentioned")
    experience_level: ExperienceLevel = Field(description="Required experience level")
    work_policy: Optional[WorkPolicy] = Field(default=None, description="Work arrangement if specified")
    industry: Optional[str] = Field(default=None, description="Industry or domain if specified")
    salary_range: Optional[str] = Field(default=None, description="Salary information if mentioned")


class CVEntry(BaseModel):
    """A single entry in any CV section."""
    title: str = Field(description="Entry title (job title, degree, certification name, etc.)")
    subtitle: Optional[str] = Field(default=None, description="Subtitle (company, institution, issuer, etc.)")
    date_range: Optional[str] = Field(default=None, description="Time period or date")
    details: List[str] = Field(default_factory=list, description="Bullet points, responsibilities, or details")
    tags: List[str] = Field(default_factory=list, description="Technologies, skills, or keywords")


class Section(BaseModel):
    """A section of the CV containing multiple entries."""
    name: str = Field(description="Section name (Experience, Education, Certifications, etc.)")
    entries: List[CVEntry] = Field(description="List of entries in this section")


class StructuredCV(BaseModel):
    """Simplified structured representation of a CV."""
    personal_info: Dict[str, str] = Field(description="Name, contact information, etc.")
    sections: List[Section] = Field(description="All CV sections (experience, education, etc.)")


# Note: Output models removed - using living document pattern
# All generated content is directly added to StructuredCV sections