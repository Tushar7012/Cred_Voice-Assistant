"""
Executor Agent - Executes plan steps using available tools.
"""

import time
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from agents.base import BaseAgent
from app.models import AgentState, ConversationMemory, PlanStep, ToolResult


class ExecutorAgent(BaseAgent):
    """Agent responsible for executing plan steps using tools."""
    
    def __init__(self):
        super().__init__("Executor")
        self._tools = {}
        
    def register_tool(self, name: str, tool_callable: callable) -> None:
        """
        Register a tool for execution.
        
        Args:
            name: Tool identifier
            tool_callable: Function to execute
        """
        self._tools[name] = tool_callable
        self.log_action("Registered tool", {"name": name})
    
    def process(
        self,
        input_data: Dict[str, Any],
        memory: ConversationMemory,
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Execute the current step in the plan.
        
        Args:
            input_data: Contains 'step' (current PlanStep to execute)
            memory: Conversation memory
            state: Current agent state
            
        Returns:
            Execution result
        """
        step = input_data.get("step")
        if not step:
            return {
                "success": False,
                "error": "No step provided for execution"
            }
        
        self.log_action("Executing step", {
            "step_id": step.step_id,
            "action": step.action,
            "tool": step.tool_name
        })
        
        # Execute the step
        result = self._execute_step(step, memory, state)
        
        return result
    
    def _execute_step(
        self,
        step: PlanStep,
        memory: ConversationMemory,
        state: AgentState
    ) -> Dict[str, Any]:
        """Execute a single plan step."""
        start_time = time.time()
        
        try:
            if step.tool_name and step.tool_name in self._tools:
                # Execute the tool
                tool_input = step.tool_input or {}
                
                # Add user profile to tool input
                tool_input["user_profile"] = memory.user_profile.model_dump()
                
                result = self._tools[step.tool_name](tool_input)
                
                execution_time = (time.time() - start_time) * 1000
                
                tool_result = ToolResult(
                    tool_name=step.tool_name,
                    success=True,
                    result=result,
                    execution_time_ms=execution_time
                )
                
                return {
                    "success": True,
                    "step_id": step.step_id,
                    "tool_result": tool_result,
                    "action_completed": step.action
                }
                
            elif step.tool_name:
                # Tool not found
                return {
                    "success": False,
                    "step_id": step.step_id,
                    "error": f"Tool '{step.tool_name}' not registered"
                }
            else:
                # No tool needed, just mark as complete
                return {
                    "success": True,
                    "step_id": step.step_id,
                    "action_completed": step.action,
                    "result": "Step completed without tool"
                }
                
        except Exception as e:
            self.logger.error(f"Step execution failed: {e}")
            return {
                "success": False,
                "step_id": step.step_id,
                "error": str(e)
            }
    
    def execute_all_steps(
        self,
        steps: list,
        memory: ConversationMemory,
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Execute all steps in sequence.
        
        Args:
            steps: List of PlanStep objects
            memory: Conversation memory
            state: Agent state
            
        Returns:
            Combined results from all steps
        """
        results = []
        all_successful = True
        
        for step in steps:
            result = self._execute_step(step, memory, state)
            results.append(result)
            
            if not result.get("success", False):
                all_successful = False
                # Continue execution for remaining steps (best effort)
        
        return {
            "success": all_successful,
            "results": results,
            "steps_executed": len(results),
            "steps_succeeded": sum(1 for r in results if r.get("success", False))
        }
    
    def get_registered_tools(self) -> list:
        """Get list of registered tool names."""
        return list(self._tools.keys())


# Singleton instance
executor_agent = ExecutorAgent()
