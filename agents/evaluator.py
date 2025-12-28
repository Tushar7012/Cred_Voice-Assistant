"""
Evaluator Agent - Validates execution results and determines completeness.
"""

from typing import Dict, Any, List
from pathlib import Path
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from agents.base import BaseAgent
from app.models import AgentState, ConversationMemory
from llm.groq_client import groq_client
from llm.prompts import get_evaluator_messages, EVALUATOR_PROMPT_HINDI


class EvaluatorAgent(BaseAgent):
    """Agent responsible for evaluating execution results."""
    
    def __init__(self):
        super().__init__("Evaluator")
        
    def process(
        self,
        input_data: Dict[str, Any],
        memory: ConversationMemory,
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Evaluate execution results.
        
        Args:
            input_data: Contains 'execution_results' and 'original_intent'
            memory: Conversation memory
            state: Current agent state
            
        Returns:
            Evaluation result
        """
        execution_results = input_data.get("execution_results", [])
        original_intent = input_data.get("original_intent", "")
        
        self.log_action("Evaluating results", {
            "num_results": len(execution_results),
            "intent": original_intent[:50]
        })
        
        # Check for basic success
        basic_check = self._basic_evaluation(execution_results)
        
        if not basic_check["has_results"]:
            return {
                "success": True,
                "is_complete": False,
                "confidence_score": 0.2,
                "needs_more_info": True,
                "follow_up_question": "मुझे खेद है, कोई योजना नहीं मिली। क्या आप अपनी जानकारी फिर से बता सकते हैं?",
                "final_response_ready": False
            }
        
        # Deep evaluation using LLM
        try:
            messages = get_evaluator_messages(execution_results, original_intent)
            evaluation = groq_client.chat_json(messages, temperature=0.2)
            
            # Check for contradictions in memory
            contradictions = self._check_contradictions(memory)
            if contradictions:
                evaluation["contradictions_found"] = contradictions
                evaluation["needs_more_info"] = True
            
            self.log_action("Evaluation complete", {
                "is_complete": evaluation.get("is_complete", False),
                "confidence": evaluation.get("confidence_score", 0)
            })
            
            return {
                "success": True,
                **evaluation
            }
            
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            # Fallback to basic evaluation
            return {
                "success": True,
                "is_complete": basic_check["all_successful"],
                "confidence_score": 0.7 if basic_check["all_successful"] else 0.3,
                "needs_more_info": not basic_check["all_successful"],
                "final_response_ready": basic_check["all_successful"]
            }
    
    def _basic_evaluation(self, results: List[Dict]) -> Dict[str, Any]:
        """Perform basic success/failure evaluation."""
        if not results:
            return {
                "has_results": False,
                "all_successful": False,
                "success_rate": 0
            }
        
        successful = sum(1 for r in results if r.get("success", False))
        
        return {
            "has_results": True,
            "all_successful": successful == len(results),
            "success_rate": successful / len(results) if results else 0,
            "total_steps": len(results),
            "successful_steps": successful
        }
    
    def _check_contradictions(self, memory: ConversationMemory) -> List[Dict]:
        """Check for contradictions in conversation memory."""
        contradictions = []
        
        # Look for changes in user profile across turns
        profile_history = []
        for turn in memory.turns:
            if turn.extracted_info:
                profile_history.append(turn.extracted_info)
        
        if len(profile_history) >= 2:
            # Compare consecutive profile updates
            for i in range(1, len(profile_history)):
                prev = profile_history[i-1]
                curr = profile_history[i]
                
                for key in set(prev.keys()) & set(curr.keys()):
                    if prev[key] != curr[key]:
                        contradictions.append({
                            "field": key,
                            "old_value": prev[key],
                            "new_value": curr[key]
                        })
        
        return contradictions
    
    def should_ask_clarification(
        self,
        evaluation: Dict[str, Any],
        missing_info: List[str]
    ) -> Dict[str, Any]:
        """
        Determine if clarification is needed and what to ask.
        
        Args:
            evaluation: Evaluation result
            missing_info: List of missing information fields
            
        Returns:
            Dict with clarification decision and question
        """
        if not evaluation.get("is_complete", True) or missing_info:
            # Prioritize critical missing info
            priority_fields = ["age", "annual_income", "category", "state"]
            critical_missing = [f for f in missing_info if f in priority_fields]
            
            if critical_missing:
                question = self._generate_clarification_question(critical_missing[:2])
                return {
                    "should_ask": True,
                    "question": question,
                    "fields_needed": critical_missing[:2]
                }
        
        if evaluation.get("contradictions_found"):
            contradiction = evaluation["contradictions_found"][0]
            question = self._generate_contradiction_question(contradiction)
            return {
                "should_ask": True,
                "question": question,
                "type": "contradiction"
            }
        
        return {
            "should_ask": False
        }
    
    def _generate_clarification_question(self, missing_fields: List[str]) -> str:
        """Generate a Hindi question for missing fields."""
        field_questions = {
            "age": "आपकी उम्र क्या है?",
            "annual_income": "आपकी वार्षिक आय कितनी है?",
            "category": "आपकी श्रेणी क्या है - सामान्य, SC, ST, OBC या EWS?",
            "state": "आप किस राज्य में रहते हैं?",
            "occupation": "आपका व्यवसाय क्या है?",
            "is_bpl": "क्या आपके पास BPL कार्ड है?",
            "gender": "आपका लिंग क्या है?",
            "is_disabled": "क्या आप विकलांगता की श्रेणी में आते हैं?"
        }
        
        questions = [field_questions.get(f, f"कृपया अपना {f} बताएं") for f in missing_fields]
        
        if len(questions) == 1:
            return questions[0]
        else:
            return " और ".join(questions)
    
    def _generate_contradiction_question(self, contradiction: Dict) -> str:
        """Generate a question to resolve a contradiction."""
        field = contradiction["field"]
        old_val = contradiction["old_value"]
        new_val = contradiction["new_value"]
        
        return f"पहले आपने {field} '{old_val}' बताया था, अब '{new_val}' बता रहे हैं। कौन सी जानकारी सही है?"


# Singleton instance
evaluator_agent = EvaluatorAgent()
