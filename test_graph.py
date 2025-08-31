"""Tests for graph.py workflow_router function."""

import pytest
from unittest.mock import Mock, patch
from graph import workflow_router, run_graph_step, create_cv_generation_graph
from state import AppState
from models import StructuredCV, Section, CVEntry
from langgraph.graph import END


@pytest.fixture
def base_app_state() -> AppState:
    """Create a base AppState for testing."""
    return {
        "current_step": "parse_cv",
        "cv_text": "Sample CV text",
        "job_description": "Sample job description",

        "source_cv": StructuredCV(
            personal_info={"name": "John Doe"},
            sections=[]
        ),
        "tailored_cv": StructuredCV(
            personal_info={"name": "John Doe"},
            sections=[]
        ),
        "experience_index": 0,
        "human_review_required": False,
        "human_feedback": "",
        "review_content": ""
    }


class TestWorkflowRouter:
    """Test the workflow_router function for all possible state transitions."""
    
    def test_router_input_to_parse_jd(self, base_app_state):
        """Test routing from input state to parse job description."""
        base_app_state["current_step"] = "input"
        result = workflow_router(base_app_state)
        assert result == "parse_job_description"
    
    def test_router_jd_parsed_to_parse_cv(self, base_app_state):
        """Test routing from job description parsed to parse CV."""
        base_app_state["current_step"] = "job_description_parsed"
        result = workflow_router(base_app_state)
        assert result == "parse_cv"
    
    def test_router_cv_parsed_to_setup_iterative_session(self, base_app_state):
        """Test routing from CV parsed to setup iterative session."""
        base_app_state["current_step"] = "cv_parsed"
        result = workflow_router(base_app_state)
        assert result == "setup_iterative_session"
    
    def test_router_iterative_session_ready_to_map_source_sections(self, base_app_state):
        """Test routing from iterative session ready to map source sections."""
        base_app_state["current_step"] = "iterative_session_ready"
        result = workflow_router(base_app_state)
        assert result == "map_source_sections"
    
    def test_router_sections_mapped_to_generate_qualifications(self, base_app_state):
        """Test routing from sections mapped to generate qualifications."""
        base_app_state["current_step"] = "sections_mapped"
        result = workflow_router(base_app_state)
        assert result == "generate_qualifications"
    
    def test_router_qualifications_approved_to_tailor_experience(self, base_app_state):
        """Test routing from qualifications approved to tailor experience."""
        base_app_state["current_step"] = "qualifications_approved"
        result = workflow_router(base_app_state)
        assert result == "tailor_experience"
    
    def test_router_start_experience_tailoring_to_tailor_experience(self, base_app_state):
        """Test routing from start experience tailoring to tailor experience."""
        base_app_state["current_step"] = "start_experience_tailoring"
        result = workflow_router(base_app_state)
        assert result == "tailor_experience"
    
    def test_router_experience_entry_tailored_to_should_continue(self, base_app_state):
        """Test routing from experience entry tailored to should continue decision."""
        base_app_state["current_step"] = "experience_entry_tailored"
        result = workflow_router(base_app_state)
        assert result == "should_continue_experience"
    
    def test_router_continue_experience_tailoring_to_tailor_experience(self, base_app_state):
        """Test routing from continue experience tailoring back to tailor experience."""
        base_app_state["current_step"] = "continue_experience_tailoring"
        result = workflow_router(base_app_state)
        assert result == "tailor_experience"
    
    def test_router_experience_tailoring_complete_to_tailor_projects(self, base_app_state):
        """Test routing from experience tailoring complete to tailor project entry."""
        base_app_state["current_step"] = "experience_tailoring_complete"
        result = workflow_router(base_app_state)
        assert result == "tailor_project_entry"
    
    def test_router_start_projects_tailoring_to_tailor_projects(self, base_app_state):
        """Test routing from start projects tailoring to tailor project entry."""
        base_app_state["current_step"] = "start_projects_tailoring"
        result = workflow_router(base_app_state)
        assert result == "tailor_project_entry"
    
    def test_router_project_entry_tailored_to_should_continue(self, base_app_state):
        """Test routing from project entry tailored to should continue projects."""
        base_app_state["current_step"] = "project_entry_tailored"
        result = workflow_router(base_app_state)
        assert result == "should_continue_projects"
    
    def test_router_continue_projects_tailoring_to_tailor_project_entry(self, base_app_state):
        """Test routing from continue projects tailoring to tailor project entry."""
        base_app_state["current_step"] = "continue_projects_tailoring"
        result = workflow_router(base_app_state)
        assert result == "tailor_project_entry"
    
    def test_router_projects_tailoring_complete_to_generate_summary(self, base_app_state):
        """Test routing from projects tailoring complete to generate summary."""
        base_app_state["current_step"] = "projects_tailoring_complete"
        result = workflow_router(base_app_state)
        assert result == "generate_summary"
    
    def test_router_start_summary_generation_to_generate_summary(self, base_app_state):
        """Test routing from start summary generation to generate summary."""
        base_app_state["current_step"] = "start_summary_generation"
        result = workflow_router(base_app_state)
        assert result == "generate_summary"
    
    def test_router_summary_approved_to_finalize_cv(self, base_app_state):
        """Test routing from summary approved to finalize CV."""
        base_app_state["current_step"] = "summary_approved"
        result = workflow_router(base_app_state)
        assert result == "finalize_cv"
    
    def test_router_start_cv_finalization_to_finalize_cv(self, base_app_state):
        """Test routing from start CV finalization to finalize CV."""
        base_app_state["current_step"] = "start_cv_finalization"
        result = workflow_router(base_app_state)
        assert result == "finalize_cv"
    
    def test_router_cv_finalized_to_end(self, base_app_state):
        """Test routing from CV finalized to END."""
        base_app_state["current_step"] = "cv_finalized"
        result = workflow_router(base_app_state)
        assert result == END
    
    def test_router_cv_parsing_failed_to_end(self, base_app_state):
        """Test routing from CV parsing failed to END."""
        base_app_state["current_step"] = "cv_parsing_failed"
        result = workflow_router(base_app_state)
        assert result == END
    
    def test_router_awaiting_states_to_end(self, base_app_state):
        """Test that all 'awaiting' states route to END."""
        awaiting_states = [
            "awaiting_qualifications_review",
            "awaiting_summary_review", 
            "awaiting_experience_review",
            "awaiting_projects_review",
            "awaiting_human_review"
        ]
        
        for state_name in awaiting_states:
            base_app_state["current_step"] = state_name
            result = workflow_router(base_app_state)
            assert result == END, f"State {state_name} should route to END"
    
    def test_router_unknown_state_to_end(self, base_app_state):
        """Test that unknown states route to END."""
        base_app_state["current_step"] = "unknown_state"
        result = workflow_router(base_app_state)
        assert result == END
    
    def test_router_missing_current_step_defaults_to_input(self, base_app_state):
        """Test that missing current_step defaults to input routing."""
        del base_app_state["current_step"]
        result = workflow_router(base_app_state)
        assert result == "parse_job_description"


class TestRunGraphStep:
    """Test the run_graph_step function."""
    
    @patch('graph.create_cv_generation_graph')
    def test_run_graph_step_success(self, mock_create_graph, base_app_state):
        """Test successful graph step execution."""
        # Mock the graph
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "current_step": "job_description_parsed",
            "job_description_data": {"job_title": "Software Engineer"}
        }
        mock_create_graph.return_value = mock_graph
        
        # Test state
        input_state = {"current_step": "input", "raw_job_description": "Job description"}
        
        # Execute
        result = run_graph_step(input_state)
        
        # Verify
        assert result["current_step"] == "job_description_parsed"
        assert "job_description_data" in result
        mock_create_graph.assert_called_once()
        mock_graph.invoke.assert_called_once_with(input_state)
    
    @patch('graph.create_cv_generation_graph')
    def test_run_graph_step_graph_exception(self, mock_create_graph, base_app_state):
        """Test graph step execution with exception."""
        # Mock the graph to raise an exception
        mock_graph = Mock()
        mock_graph.invoke.side_effect = Exception("Graph execution failed")
        mock_create_graph.return_value = mock_graph
        
        # Test state
        input_state = {"current_step": "input"}
        
        # Execute
        result = run_graph_step(input_state)
        
        # Verify error handling
        assert result["has_error"] is True
        assert "Graph execution failed" in result["error_message"]
        assert result["current_step"] == "input"  # Original state preserved
    
    @patch('graph.create_cv_generation_graph')
    def test_run_graph_step_unexpected_return_format(self, mock_create_graph, base_app_state):
        """Test graph step execution with unexpected return format."""
        # Mock the graph to return non-dict
        mock_graph = Mock()
        mock_graph.invoke.return_value = "unexpected_format"
        mock_create_graph.return_value = mock_graph
        
        # Test state
        input_state = {"current_step": "input"}
        
        # Execute
        result = run_graph_step(input_state)
        
        # Verify error handling
        assert result["has_error"] is True
        assert "Graph returned unexpected format" in result["error_message"]
        assert result["current_step"] == "input"  # Original state preserved


class TestCreateCVGenerationGraph:
    """Test the create_cv_generation_graph function."""
    
    def test_create_graph_returns_compiled_graph(self):
        """Test that create_cv_generation_graph returns a compiled graph."""
        graph = create_cv_generation_graph()
        
        # Verify it's a compiled graph (has invoke method)
        assert hasattr(graph, 'invoke')
        assert callable(graph.invoke)
    
    @patch('graph.StateGraph')
    def test_create_graph_adds_all_nodes(self, mock_state_graph):
        """Test that all required nodes are added to the graph."""
        mock_workflow = Mock()
        mock_state_graph.return_value = mock_workflow
        mock_workflow.compile.return_value = Mock()
        
        create_cv_generation_graph()
        
        # Verify all nodes are added
        expected_nodes = [
            "parse_job_description",
            "parse_cv",
            "setup_iterative_session",
            "map_source_sections",
            "generate_qualifications",
            "human_review",
            "generate_summary",
            "tailor_experience",
            "should_continue_experience",
            "tailor_project_entry",
            "should_continue_projects",
            "finalize_cv",
            "router"
        ]
        
        # Check that add_node was called for each expected node
        assert mock_workflow.add_node.call_count == len(expected_nodes)
        
        # Verify router is set as entry point
        mock_workflow.set_entry_point.assert_called_once_with("router")
        
        # Verify conditional edges are added for router
        mock_workflow.add_conditional_edges.assert_called_once()
        
        # Verify all nodes have edges back to router
        expected_edge_calls = len(expected_nodes) - 1  # All nodes except router
        assert mock_workflow.add_edge.call_count == expected_edge_calls
        
        # Verify graph is compiled
        mock_workflow.compile.assert_called_once()