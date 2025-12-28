"""
Unit tests for agents module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import (
    AgentState, ConversationMemory, UserProfile, 
    AgentPlan, PlanStep, AgentStateEnum
)


class TestPlannerAgent:
    """Tests for the Planner agent."""
    
    def test_extract_user_info_age(self):
        """Test extraction of age from Hindi text."""
        from agents.planner import planner_agent
        
        # Mock the groq client
        with patch('agents.planner.groq_client') as mock_client:
            mock_client.chat_json.return_value = {"age": 35}
            
            result = planner_agent.extract_user_info(
                "मेरी उम्र 35 साल है",
                {}
            )
            
            assert result.get("age") == 35
    
    def test_extract_user_info_multiple_fields(self):
        """Test extraction of multiple fields."""
        from agents.planner import planner_agent
        
        with patch('agents.planner.groq_client') as mock_client:
            mock_client.chat_json.return_value = {
                "age": 40,
                "category": "obc",
                "state": "Maharashtra"
            }
            
            result = planner_agent.extract_user_info(
                "मैं 40 साल का हूं, OBC हूं, महाराष्ट्र में रहता हूं",
                {}
            )
            
            assert result.get("age") == 40
            assert result.get("category") == "obc"
            assert result.get("state") == "Maharashtra"
    
    def test_build_plan(self):
        """Test plan building from LLM response."""
        from agents.planner import planner_agent
        
        llm_response = {
            "user_intent": "किसान योजना जानना",
            "required_info": ["age", "state"],
            "missing_info": [],
            "steps": [
                {
                    "step_id": 1,
                    "action": "योजनाएं खोजें",
                    "tool_name": "eligibility_engine",
                    "tool_input": {},
                    "expected_output": "योजनाओं की सूची"
                }
            ]
        }
        
        plan = planner_agent._build_plan(llm_response, "test input")
        
        assert plan.user_intent == "किसान योजना जानना"
        assert len(plan.steps) == 1
        assert plan.steps[0].tool_name == "eligibility_engine"


class TestExecutorAgent:
    """Tests for the Executor agent."""
    
    def test_register_tool(self):
        """Test tool registration."""
        from agents.executor import ExecutorAgent
        
        executor = ExecutorAgent()
        mock_tool = Mock(return_value={"success": True})
        
        executor.register_tool("test_tool", mock_tool)
        
        assert "test_tool" in executor.get_registered_tools()
    
    def test_execute_step_with_tool(self):
        """Test step execution with a registered tool."""
        from agents.executor import ExecutorAgent
        
        executor = ExecutorAgent()
        mock_tool = Mock(return_value={"schemes": ["PM-KISAN"]})
        executor.register_tool("test_tool", mock_tool)
        
        step = PlanStep(
            step_id=1,
            action="Test action",
            tool_name="test_tool",
            tool_input={"query": "test"},
            expected_output="schemes"
        )
        
        memory = ConversationMemory(session_id="test")
        state = AgentState()
        
        result = executor._execute_step(step, memory, state)
        
        assert result["success"] == True
        assert result["step_id"] == 1


class TestEvaluatorAgent:
    """Tests for the Evaluator agent."""
    
    def test_basic_evaluation_success(self):
        """Test basic evaluation of successful results."""
        from agents.evaluator import evaluator_agent
        
        results = [
            {"success": True, "result": {"schemes": []}},
            {"success": True, "result": {"data": "test"}}
        ]
        
        evaluation = evaluator_agent._basic_evaluation(results)
        
        assert evaluation["has_results"] == True
        assert evaluation["all_successful"] == True
        assert evaluation["success_rate"] == 1.0
    
    def test_basic_evaluation_partial_failure(self):
        """Test evaluation with partial failures."""
        from agents.evaluator import evaluator_agent
        
        results = [
            {"success": True},
            {"success": False, "error": "test error"}
        ]
        
        evaluation = evaluator_agent._basic_evaluation(results)
        
        assert evaluation["all_successful"] == False
        assert evaluation["success_rate"] == 0.5
    
    def test_generate_clarification_question(self):
        """Test clarification question generation."""
        from agents.evaluator import evaluator_agent
        
        question = evaluator_agent._generate_clarification_question(["age"])
        
        assert "उम्र" in question
    
    def test_contradiction_question(self):
        """Test contradiction question generation."""
        from agents.evaluator import evaluator_agent
        
        contradiction = {
            "field": "age",
            "old_value": 35,
            "new_value": 40
        }
        
        question = evaluator_agent._generate_contradiction_question(contradiction)
        
        assert "35" in question
        assert "40" in question


class TestAgentOrchestrator:
    """Tests for the Agent Orchestrator."""
    
    def test_initialization(self):
        """Test orchestrator initialization."""
        from agents.orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        
        assert orchestrator.state.current_state == AgentStateEnum.LISTENING
        assert len(orchestrator.memory.turns) == 0
    
    def test_reset(self):
        """Test orchestrator reset."""
        from agents.orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        orchestrator.memory.turns.append(Mock())
        orchestrator._turn_counter = 5
        
        orchestrator.reset()
        
        assert len(orchestrator.memory.turns) == 0
        assert orchestrator._turn_counter == 0
    
    def test_update_user_profile(self):
        """Test user profile update."""
        from agents.orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        
        orchestrator._update_user_profile({"age": 30, "category": "obc"})
        
        assert orchestrator.memory.user_profile.age == 30
        assert orchestrator.memory.user_profile.category == "obc"
    
    def test_get_user_profile(self):
        """Test getting user profile."""
        from agents.orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        orchestrator.memory.user_profile.age = 25
        
        profile = orchestrator.get_user_profile()
        
        assert profile["age"] == 25
