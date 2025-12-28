"""
Base tool interface for all tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize the tool.
        
        Args:
            name: Tool identifier
            description: Human-readable description
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Args:
            input_data: Tool input parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make the tool callable."""
        return self.execute(input_data)
