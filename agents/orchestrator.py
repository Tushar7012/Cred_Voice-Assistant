"""
Agent Orchestrator - Manages the Planner-Executor-Evaluator lifecycle.
Implements the state machine for agent coordination.
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from app.models import (
    AgentState, AgentStateEnum, ConversationMemory, 
    ConversationTurn, UserProfile
)
from agents.planner import planner_agent
from agents.executor import executor_agent
from agents.evaluator import evaluator_agent
from llm.groq_client import groq_client
from llm.prompts import get_response_messages, RESPONSE_GENERATOR_PROMPT_HINDI


class AgentOrchestrator:
    """
    Orchestrates the Planner-Executor-Evaluator agent workflow.
    Implements explicit state machine for agent lifecycle.
    """
    
    MAX_ITERATIONS = 5  # Prevent infinite loops
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.state = AgentState()
        self.memory = ConversationMemory(session_id=str(uuid.uuid4()))
        self._turn_counter = 0
        self.logger = logger.bind(component="Orchestrator")
        
    def reset(self) -> None:
        """Reset the orchestrator state."""
        self.state = AgentState()
        self.memory = ConversationMemory(session_id=str(uuid.uuid4()))
        self._turn_counter = 0
        self.logger.info("Orchestrator reset")
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input through the agent workflow.
        
        Args:
            user_input: Transcribed user speech (Hindi text)
            
        Returns:
            Dict containing response and metadata
        """
        self.logger.info(f"Processing user input: {user_input[:50]}...")
        
        # Extract any new user info from input
        extracted_info = planner_agent.extract_user_info(
            user_input, 
            self.memory.user_profile.model_dump()
        )
        self._update_user_profile(extracted_info)
        
        # Run the agent loop
        response = self._run_agent_loop(user_input)
        
        # Create conversation turn
        turn = ConversationTurn(
            turn_id=self._turn_counter,
            user_input_text=user_input,
            agent_response_text=response.get("response", ""),
            agent_state=self.state.current_state,
            tools_used=response.get("tools_used", []),
            extracted_info=extracted_info,
            confidence_score=response.get("confidence", 0.0)
        )
        self.memory.turns.append(turn)
        self._turn_counter += 1
        
        # Limit memory size
        if len(self.memory.turns) > 20:
            self.memory.turns = self.memory.turns[-20:]
        
        return response
    
    def _run_agent_loop(self, user_input: str) -> Dict[str, Any]:
        """Run the Planner-Executor-Evaluator loop."""
        iteration = 0
        tools_used = []
        
        while iteration < self.MAX_ITERATIONS:
            iteration += 1
            self.logger.info(f"Agent loop iteration {iteration}, state: {self.state.current_state}")
            
            # PLANNING PHASE
            self.state.current_state = AgentStateEnum.PLANNING
            plan_result = planner_agent.process(
                {"user_input": user_input},
                self.memory,
                self.state
            )
            
            if not plan_result.get("success"):
                return self._handle_error("Planning failed", plan_result.get("error"))
            
            # Check if clarification needed
            if plan_result.get("needs_clarification"):
                return {
                    "success": True,
                    "response": plan_result.get("clarification_question", ""),
                    "state": "clarification_needed",
                    "missing_info": plan_result.get("missing_info", []),
                    "tools_used": tools_used,
                    "confidence": 0.5
                }
            
            self.state.current_plan = plan_result.get("plan")
            
            # EXECUTION PHASE
            self.state.current_state = AgentStateEnum.EXECUTING
            
            if self.state.current_plan and self.state.current_plan.steps:
                exec_result = executor_agent.execute_all_steps(
                    self.state.current_plan.steps,
                    self.memory,
                    self.state
                )
                
                self.state.execution_results = exec_result.get("results", [])
                tools_used.extend([
                    r.get("tool_result", {}).tool_name 
                    for r in exec_result.get("results", []) 
                    if r.get("tool_result")
                ])
            
            # EVALUATION PHASE
            self.state.current_state = AgentStateEnum.EVALUATING
            eval_result = evaluator_agent.process(
                {
                    "execution_results": self.state.execution_results,
                    "original_intent": self.state.current_plan.user_intent if self.state.current_plan else user_input
                },
                self.memory,
                self.state
            )
            
            self.state.evaluation_result = eval_result
            
            # Check if we need more info
            if eval_result.get("needs_more_info") and eval_result.get("follow_up_question"):
                return {
                    "success": True,
                    "response": eval_result.get("follow_up_question"),
                    "state": "needs_more_info",
                    "tools_used": tools_used,
                    "confidence": eval_result.get("confidence_score", 0.5)
                }
            
            # Check if response is ready
            if eval_result.get("final_response_ready", False) or eval_result.get("is_complete", False):
                break
        
        # RESPONDING PHASE
        self.state.current_state = AgentStateEnum.RESPONDING
        response = self._generate_response()
        
        # Reset state for next turn
        self.state.current_state = AgentStateEnum.LISTENING
        
        return {
            "success": True,
            "response": response,
            "state": "complete",
            "tools_used": list(set(tools_used)),
            "confidence": self.state.evaluation_result.get("confidence_score", 0.7) if self.state.evaluation_result else 0.7,
            "schemes_found": self._extract_schemes_from_results()
        }
    
    def _generate_response(self) -> str:
        """Generate the final response using LLM."""
        schemes = self._extract_schemes_from_results()
        
        messages = get_response_messages(
            schemes,
            self.memory.user_profile.get_filled_fields(),
            self.state.current_plan.user_intent if self.state.current_plan else ""
        )
        
        try:
            response = groq_client.chat(messages, temperature=0.7)
            return response
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            return "मुझे खेद है, कुछ तकनीकी समस्या हुई। कृपया फिर से प्रयास करें।"
    
    def _extract_schemes_from_results(self) -> list:
        """Extract scheme information from execution results."""
        schemes = []
        for result in self.state.execution_results:
            tool_result = result.get("tool_result")
            if tool_result and hasattr(tool_result, "result"):
                if isinstance(tool_result.result, list):
                    schemes.extend(tool_result.result)
                elif isinstance(tool_result.result, dict):
                    if "schemes" in tool_result.result:
                        schemes.extend(tool_result.result["schemes"])
        return schemes
    
    def _update_user_profile(self, extracted_info: Dict[str, Any]) -> None:
        """Update user profile with extracted information."""
        if not extracted_info:
            return
        
        current = self.memory.user_profile.model_dump()
        
        for key, value in extracted_info.items():
            if value is not None and hasattr(self.memory.user_profile, key):
                # Check for contradiction
                if current.get(key) is not None and current.get(key) != value:
                    self.memory.contradictions_detected.append({
                        "field": key,
                        "old_value": current.get(key),
                        "new_value": value,
                        "timestamp": datetime.now().isoformat()
                    })
                setattr(self.memory.user_profile, key, value)
        
        self.logger.info(f"Updated user profile: {self.memory.user_profile.get_filled_fields()}")
    
    def _handle_error(self, message: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Handle errors in the agent loop."""
        self.state.current_state = AgentStateEnum.ERROR_HANDLING
        self.state.error_count += 1
        
        error_response = "मुझे खेद है, कुछ समस्या हुई। "
        
        if self.state.error_count >= self.state.max_retries:
            error_response += "कृपया बाद में फिर से प्रयास करें।"
        else:
            error_response += "क्या आप अपना अनुरोध फिर से बता सकते हैं?"
        
        return {
            "success": False,
            "response": error_response,
            "error": error,
            "state": "error"
        }
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get the current user profile."""
        return self.memory.user_profile.model_dump()
    
    def update_user_profile(self, profile_data: Dict[str, Any]) -> None:
        """Manually update the user profile."""
        for key, value in profile_data.items():
            if hasattr(self.memory.user_profile, key):
                setattr(self.memory.user_profile, key, value)
    
    def get_conversation_history(self) -> list:
        """Get the conversation history."""
        return [
            {
                "turn": turn.turn_id,
                "user": turn.user_input_text,
                "assistant": turn.agent_response_text,
                "timestamp": turn.timestamp.isoformat()
            }
            for turn in self.memory.turns
        ]


# Singleton instance
orchestrator = AgentOrchestrator()
