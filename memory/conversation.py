"""
Conversation memory management.
Handles short-term memory for ongoing conversations.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from app.models import ConversationTurn, ConversationMemory, UserProfile


class ConversationManager:
    """Manages short-term conversation memory."""
    
    def __init__(self, max_turns: int = 10):
        """
        Initialize the conversation manager.
        
        Args:
            max_turns: Maximum number of turns to keep in memory
        """
        self.max_turns = max_turns
        self.sessions: Dict[str, ConversationMemory] = {}
    
    def create_session(self, session_id: str) -> ConversationMemory:
        """Create a new conversation session."""
        memory = ConversationMemory(session_id=session_id)
        self.sessions[session_id] = memory
        logger.info(f"Created new session: {session_id}")
        return memory
    
    def get_session(self, session_id: str) -> Optional[ConversationMemory]:
        """Get an existing session."""
        return self.sessions.get(session_id)
    
    def get_or_create_session(self, session_id: str) -> ConversationMemory:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            return self.create_session(session_id)
        return self.sessions[session_id]
    
    def add_turn(
        self,
        session_id: str,
        user_input: str,
        agent_response: str,
        extracted_info: Optional[Dict] = None,
        tools_used: Optional[List[str]] = None
    ) -> ConversationTurn:
        """
        Add a conversation turn to the session.
        
        Args:
            session_id: Session identifier
            user_input: User's input text
            agent_response: Agent's response text
            extracted_info: Information extracted from user input
            tools_used: List of tools used in this turn
            
        Returns:
            The created ConversationTurn
        """
        memory = self.get_or_create_session(session_id)
        
        turn = ConversationTurn(
            turn_id=len(memory.turns),
            user_input_text=user_input,
            agent_response_text=agent_response,
            extracted_info=extracted_info or {},
            tools_used=tools_used or [],
            agent_state=memory.turns[-1].agent_state if memory.turns else "listening"
        )
        
        memory.turns.append(turn)
        
        # Trim if needed
        if len(memory.turns) > self.max_turns:
            memory.turns = memory.turns[-self.max_turns:]
        
        # Update user profile with extracted info
        if extracted_info:
            self._update_profile(memory, extracted_info)
        
        logger.info(f"Added turn {turn.turn_id} to session {session_id}")
        return turn
    
    def _update_profile(self, memory: ConversationMemory, extracted_info: Dict) -> None:
        """Update user profile with extracted information."""
        for key, value in extracted_info.items():
            if value is not None and hasattr(memory.user_profile, key):
                setattr(memory.user_profile, key, value)
    
    def get_context_string(self, session_id: str, num_turns: int = 3) -> str:
        """
        Get a formatted context string from recent turns.
        
        Args:
            session_id: Session identifier
            num_turns: Number of recent turns to include
            
        Returns:
            Formatted context string
        """
        memory = self.get_session(session_id)
        if not memory or not memory.turns:
            return "कोई पिछली बातचीत नहीं"
        
        recent = memory.turns[-num_turns:]
        context_parts = []
        
        for turn in recent:
            context_parts.append(f"उपयोगकर्ता: {turn.user_input_text}")
            context_parts.append(f"सहायक: {turn.agent_response_text}")
        
        return "\n".join(context_parts)
    
    def get_user_profile(self, session_id: str) -> Dict[str, Any]:
        """Get the user profile for a session."""
        memory = self.get_session(session_id)
        if not memory:
            return {}
        return memory.user_profile.model_dump()
    
    def clear_session(self, session_id: str) -> None:
        """Clear a conversation session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
    
    def export_session(self, session_id: str) -> Optional[Dict]:
        """Export session data as dictionary."""
        memory = self.get_session(session_id)
        if not memory:
            return None
        
        return {
            "session_id": session_id,
            "user_profile": memory.user_profile.model_dump(),
            "turns": [
                {
                    "turn_id": t.turn_id,
                    "timestamp": t.timestamp.isoformat(),
                    "user_input": t.user_input_text,
                    "agent_response": t.agent_response_text,
                    "tools_used": t.tools_used
                }
                for t in memory.turns
            ]
        }


# Singleton instance
conversation_manager = ConversationManager()
