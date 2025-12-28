"""
Base agent class defining the interface for all agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from app.models import AgentState, ConversationMemory


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, name: str):
        """
        Initialize the agent.
        
        Args:
            name: Agent identifier
        """
        self.name = name
        self.logger = logger.bind(agent=name)
    
    @abstractmethod
    def process(
        self,
        input_data: Dict[str, Any],
        memory: ConversationMemory,
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Process input and return output.
        
        Args:
            input_data: Input data for the agent
            memory: Conversation memory
            state: Current agent state
            
        Returns:
            Processing result
        """
        pass
    
    def log_action(self, action: str, details: Optional[Dict] = None) -> None:
        """Log an agent action."""
        self.logger.info(f"{action}: {details or ''}")
