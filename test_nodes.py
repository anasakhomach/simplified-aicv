"""Tests for nodes.py functions with mocked AI chains."""

import pytest
from unittest.mock import Mock
from typing import Dict, Any

from nodes import (
    parse_cv_node,
    generate_key_qualifications_node,
    generate_executive_summary_node,
    tailor_experience_node,
    tailor_projects_node,
    finalize_cv_node,
    request_human_review_node
)
from state import AppState
from models import StructuredCV, SkillRequirement, JobDescriptionData as JobDescription, CVEntry, Section, ExperienceLevel


@pytest.fixture
def sample_app_state() -> AppState:
    """Create a sample AppState for testing."""
    return {
        "current_step": "parse_cv",
        "raw_cv_text": "John Doe\nSoftware Engineer\n5 years Python experience",
        "raw_job_description": "Looking for Python developer with 3+ years experience",
        "job_description_data": JobDescription(
            job_title="Python Developer",
            company="Tech Corp",
            key_responsibilities=["Develop Python applications"],
            technical_skills=[SkillRequirement(name="Python", is_required=True)],
            experience_level=ExperienceLevel.MID,
            experience_requirements=["3+ years Python experience"]
        ),
        "structured_cv": StructuredCV(
            personal_info={"name": "John Doe", "title": "Software Engineer"},
            sections=[]
        ),
        "human_review_required": False,
        "human_feedback": ""
    }


@pytest.fixture
def mock_cv_parsing_chain(monkeypatch):
    """Mock the CV parsing chain to return structured data."""
    mock_chain = Mock()
    mock_chain.invoke.return_value = StructuredCV(
        personal_info={"name": "John Doe", "title": "Software Engineer"},
        sections=[
            Section(
                name="Experience",
                entries=[
                    CVEntry(
                        title="Senior Developer",
                        subtitle="Tech Corp",
                        date_range="2020-2023",
                        details=["Built Python applications"],
                        tags=["Python", "Django"]
                    )
                ]
            )
        ]
    )
    
    def mock_create_cv_parsing_chain():
        return mock_chain
    
    monkeypatch.setattr("nodes.create_cv_parsing_chain", mock_create_cv_parsing_chain)
    return mock_chain


# Import the output classes from chains
class QualificationsOutput:
    def __init__(self, qualifications):
        self.qualifications = qualifications

class SummaryOutput:
    def __init__(self, summary):
        self.summary = summary

class TailoringOutput:
    def __init__(self, tailored_sections):
        self.tailored_sections = tailored_sections

@pytest.fixture
def mock_qualifications_chain(monkeypatch):
    """Mock the qualifications generation chain."""
    mock_chain = Mock()
    mock_chain.invoke.return_value = QualificationsOutput(
        qualifications=[
            "5+ years Python development experience",
            "Expert in Django framework", 
            "Strong problem-solving skills"
        ]
    )
    
    def mock_create_qualifications_chain():
        return mock_chain
    
    monkeypatch.setattr("nodes.create_key_qualifications_chain", mock_create_qualifications_chain)
    return mock_chain


@pytest.fixture
def mock_summary_chain(monkeypatch):
    """Mock the executive summary generation chain."""
    mock_chain = Mock()
    mock_chain.invoke.return_value = SummaryOutput(
        summary="Experienced Software Engineer with 5+ years in Python development."
    )
    
    def mock_create_summary_chain():
        return mock_chain
    
    monkeypatch.setattr("nodes.create_executive_summary_chain", mock_create_summary_chain)
    return mock_chain


@pytest.fixture
def mock_experience_tailoring_chain(monkeypatch):
    """Mock the experience tailoring chain."""
    mock_chain = Mock()
    mock_chain.invoke.return_value = TailoringOutput(
        tailored_sections=[
            Section(
                name="Experience",
                entries=[
                    CVEntry(
                        title="Senior Python Developer",
                        subtitle="Tech Corp",
                        date_range="2020-2023",
                        details=["Developed scalable Python applications using Django"],
                        tags=["Python", "Django", "Scalability"]
                    )
                ]
            )
        ]
    )
    
    def mock_create_experience_tailoring_chain():
        return mock_chain
    
    monkeypatch.setattr("nodes.create_experience_tailoring_chain", mock_create_experience_tailoring_chain)
    return mock_chain


@pytest.fixture
def mock_projects_tailoring_chain(monkeypatch):
    """Mock the projects tailoring chain."""
    mock_chain = Mock()
    mock_chain.invoke.return_value = TailoringOutput(
        tailored_sections=[
            Section(
                name="Projects",
                entries=[
                    CVEntry(
                        title="E-commerce Platform",
                        subtitle="Personal Project",
                        date_range="2022",
                        details=["Built using Python and Django"],
                        tags=["Python", "Django", "E-commerce"]
                    )
                ]
            )
        ]
    )
    
    def mock_create_projects_tailoring_chain():
        return mock_chain
    
    monkeypatch.setattr("nodes.create_projects_tailoring_chain", mock_create_projects_tailoring_chain)
    return mock_chain


class TestParseCV:
    """Test the parse_cv_node function."""
    
    def test_parse_cv_success(self, sample_app_state, mock_cv_parsing_chain):
        """Test successful CV parsing."""
        result = parse_cv_node(sample_app_state)
        
        # Verify chain was called with correct input
        mock_cv_parsing_chain.invoke.assert_called_once_with({
            "cv_text": sample_app_state["raw_cv_text"]
        })
        
        # Verify result structure
        assert "structured_cv" in result
        assert "current_step" in result
        assert result["current_step"] == "cv_parsed"
        
        # Verify structured_cv was updated
        structured_cv = result["structured_cv"]
        assert structured_cv.personal_info["name"] == "John Doe"
        assert len(structured_cv.sections) == 1
        assert structured_cv.sections[0].name == "Experience"


class TestGenerateQualifications:
    """Test the generate_key_qualifications_node function."""
    
    def test_generate_qualifications_success(self, sample_app_state, mock_qualifications_chain):
        """Test successful qualifications generation."""
        # Add some experience to the CV
        sample_app_state["structured_cv"].sections = [
            Section(
                name="Experience",
                entries=[
                    CVEntry(
                        title="Developer",
                        subtitle="Company",
                        date_range="2020-2023",
                        details=["Python development"],
                        tags=["Python"]
                    )
                ]
            )
        ]
        
        result = generate_key_qualifications_node(sample_app_state)
        
        # Verify chain was called
        mock_qualifications_chain.invoke.assert_called_once()
        
        # Verify result structure
        assert "structured_cv" in result
        assert "current_step" in result
        assert result["current_step"] == "awaiting_qualifications_review"
        
        # Verify qualifications section was added
        structured_cv = result["structured_cv"]
        qualifications_section = next((s for s in structured_cv.sections if "qualifications" in s.name.lower()), None)
        assert qualifications_section is not None
        assert len(qualifications_section.entries) == 3


class TestGenerateSummary:
    """Test the generate_executive_summary_node function."""
    
    def test_generate_summary_success(self, sample_app_state, mock_summary_chain):
        """Test successful summary generation."""
        result = generate_executive_summary_node(sample_app_state)
        
        # Verify chain was called
        mock_summary_chain.invoke.assert_called_once()
        
        # Verify result structure
        assert "structured_cv" in result
        assert "current_step" in result
        assert result["current_step"] == "awaiting_summary_review"
        
        # Verify summary section was added
        structured_cv = result["structured_cv"]
        summary_section = next((s for s in structured_cv.sections if "summary" in s.name.lower()), None)
        assert summary_section is not None
        assert len(summary_section.entries) == 1
        assert "Experienced Software Engineer" in summary_section.entries[0].details[0]


class TestTailorExperience:
    """Test the tailor_experience_node function."""
    
    def test_tailor_experience_success(self, sample_app_state, mock_experience_tailoring_chain):
        """Test successful experience tailoring."""
        # Add qualifications and experience to the CV
        sample_app_state["structured_cv"].sections = [
            Section(
                name="qualifications",
                entries=[
                    CVEntry(title="", subtitle="", date_range="", details=["Python expert"], tags=[])
                ]
            ),
            Section(
                name="Experience",
                entries=[
                    CVEntry(
                        title="Developer",
                        subtitle="Company",
                        date_range="2020-2023",
                        details=["Built apps"],
                        tags=["Python"]
                    )
                ]
            )
        ]
        
        result = tailor_experience_node(sample_app_state)
        
        # Verify chain was called
        mock_experience_tailoring_chain.invoke.assert_called_once()
        
        # Verify result structure
        assert "structured_cv" in result
        assert "current_step" in result
        assert result["current_step"] == "awaiting_experience_review"
        
        # Verify experience section was updated
        structured_cv = result["structured_cv"]
        experience_section = next((s for s in structured_cv.sections if s.name == "Experience"), None)
        assert experience_section is not None
        assert "scalable Python applications" in experience_section.entries[0].details[0]


class TestTailorProjects:
    """Test the tailor_projects_node function."""
    
    def test_tailor_projects_success(self, sample_app_state, mock_projects_tailoring_chain):
        """Test successful projects tailoring."""
        # Add qualifications and projects to the CV
        sample_app_state["structured_cv"].sections = [
            Section(
                name="qualifications",
                entries=[
                    CVEntry(title="", subtitle="", date_range="", details=["Python expert"], tags=[])
                ]
            ),
            Section(
                name="Projects",
                entries=[
                    CVEntry(
                        title="Web App",
                        subtitle="Personal",
                        date_range="2022",
                        details=["Built web app"],
                        tags=["Python"]
                    )
                ]
            )
        ]
        
        result = tailor_projects_node(sample_app_state)
        
        # Verify chain was called
        mock_projects_tailoring_chain.invoke.assert_called_once()
        
        # Verify result structure
        assert "structured_cv" in result
        assert "current_step" in result
        assert result["current_step"] == "awaiting_projects_review"
        
        # Verify projects section was updated
        structured_cv = result["structured_cv"]
        projects_section = next((s for s in structured_cv.sections if s.name == "Projects"), None)
        assert projects_section is not None
        assert "E-commerce Platform" in projects_section.entries[0].title


class TestFinalizeCV:
    """Test the finalize_cv_node function."""
    
    def test_finalize_cv_success(self, sample_app_state):
        """Test successful CV finalization."""
        result = finalize_cv_node(sample_app_state)
        
        # Verify result structure
        assert "final_cv" in result
        assert "current_step" in result
        assert result["current_step"] == "cv_finalized"
        assert result["workflow_complete"] is True


class TestRequestHumanReview:
    """Test the request_human_review_node function."""
    
    def test_request_review_with_qualifications(self, sample_app_state):
        """Test human review request with qualifications."""
        # Add qualifications to the CV
        sample_app_state["structured_cv"].sections = [
            Section(
                name="qualifications",
                entries=[
                    CVEntry(title="", subtitle="", date_range="", details=["Python expert", "Django specialist"], tags=[])
                ]
            )
        ]
        
        result = request_human_review_node(sample_app_state)
        
        # Verify result structure
        assert "human_review_required" in result
        assert "human_feedback" in result
        assert result["human_review_required"] is True
        assert result["current_step"] == "awaiting_human_review"
    
    def test_request_review_without_qualifications(self, sample_app_state):
        """Test human review request without qualifications."""
        result = request_human_review_node(sample_app_state)
        
        # Verify result structure
        assert "human_review_required" in result
        assert "human_feedback" in result
        assert result["human_review_required"] is True
        assert result["current_step"] == "awaiting_human_review"