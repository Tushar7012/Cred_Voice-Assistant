"""
Planner Agent - Analyzes user request and creates action plan.
"""

import json
import uuid
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from agents.base import BaseAgent
from app.models import (
    AgentState, ConversationMemory, AgentPlan, PlanStep
)
from llm.groq_client import groq_client
from llm.prompts import get_planner_messages, PLANNER_PROMPT_HINDI


class PlannerAgent(BaseAgent):
    """Agent responsible for analyzing user intent and creating action plans."""
    
    def __init__(self):
        super().__init__("Planner")
        
    def process(
        self,
        input_data: Dict[str, Any],
        memory: ConversationMemory,
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Analyze user input and create an execution plan.
        
        Args:
            input_data: Contains 'user_input' (transcribed text)
            memory: Conversation memory with user profile
            state: Current agent state
            
        Returns:
            Dict containing the plan and any clarification needs
        """
        self.log_action("Starting planning", {"input": input_data.get("user_input", "")[:100]})
        
        user_input = input_data.get("user_input", "")
        
        # Build context from memory
        user_profile = memory.user_profile.get_filled_fields()
        conversation_history = [
            {"user": turn.user_input_text, "assistant": turn.agent_response_text}
            for turn in memory.turns[-3:]
        ]
        
        # Create messages for the LLM
        messages = get_planner_messages(user_input, user_profile, conversation_history)
        
        try:
            # Get plan from LLM
            response = groq_client.chat_json(messages, temperature=0.3)
            
            self.log_action("Received plan", {"intent": response.get("user_intent", "")})
            
            # Build the plan object
            plan = self._build_plan(response, user_input)
            
            return {
                "success": True,
                "plan": plan,
                "needs_clarification": response.get("needs_clarification", False),
                "clarification_question": response.get("clarification_question", ""),
                "missing_info": response.get("missing_info", []),
                "available_info": response.get("available_info", {})
            }
            
        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "plan": None
            }
    
    def _build_plan(self, llm_response: Dict, user_input: str) -> AgentPlan:
        """Build an AgentPlan from LLM response."""
        steps = []
        for step_data in llm_response.get("steps", []):
            step = PlanStep(
                step_id=step_data.get("step_id", len(steps) + 1),
                action=step_data.get("action", ""),
                tool_name=step_data.get("tool_name"),
                tool_input=step_data.get("tool_input"),
                expected_output=step_data.get("expected_output", ""),
                status="pending"
            )
            steps.append(step)
        
        # Add default steps if no steps were generated
        if not steps:
            steps = self._get_default_steps()
        
        return AgentPlan(
            plan_id=str(uuid.uuid4()),
            user_intent=llm_response.get("user_intent", user_input),
            required_info=llm_response.get("required_info", []),
            missing_info=llm_response.get("missing_info", []),
            steps=steps,
            created_at=datetime.now()
        )
    
    def _get_default_steps(self) -> List[PlanStep]:
        """Get default plan steps when LLM doesn't provide any."""
        return [
            PlanStep(
                step_id=1,
                action="उपयोगकर्ता प्रोफ़ाइल से पात्र योजनाएं खोजें",
                tool_name="eligibility_engine",
                tool_input={},
                expected_output="पात्र योजनाओं की सूची",
                status="pending"
            ),
            PlanStep(
                step_id=2,
                action="योजनाओं की विस्तृत जानकारी प्राप्त करें",
                tool_name="scheme_retriever",
                tool_input={"query": "सरकारी योजना"},
                expected_output="योजनाओं का विवरण",
                status="pending"
            )
        ]
    
    def extract_user_info(
        self,
        user_input: str,
        current_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract user information from natural language input.
        
        Args:
            user_input: User's message in Hindi
            current_profile: Existing user profile data
            
        Returns:
            Extracted information dict
        """
        extraction_prompt = """उपयोगकर्ता के संदेश से निम्नलिखित जानकारी निकालें (अगर उपलब्ध हो):
- age (उम्र, संख्या में)
- annual_income (वार्षिक आय, संख्या में)
- category (श्रेणी: general, sc, st, obc, ews)
- state (राज्य का नाम)
- occupation (व्यवसाय)
- is_bpl (BPL कार्ड है: true/false)
- is_disabled (विकलांग है: true/false)
- gender (लिंग: male, female, other)

JSON फॉर्मेट में जवाब दें। जो जानकारी नहीं मिली, उसे null रखें।

उपयोगकर्ता संदेश: """ + user_input
        
        messages = [
            {"role": "system", "content": "आप एक जानकारी निकालने वाले सहायक हैं।"},
            {"role": "user", "content": extraction_prompt}
        ]
        
        try:
            extracted = groq_client.chat_json(messages, temperature=0.1)
            
            # Filter out null values
            return {k: v for k, v in extracted.items() if v is not None}
            
        except Exception as e:
            self.logger.error(f"Info extraction failed: {e}")
            return {}


# Singleton instance
planner_agent = PlannerAgent()
