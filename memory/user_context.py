"""
User context memory for long-term persistence.
Stores user profiles and preferences across sessions.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from app.models import UserProfile


class UserContextManager:
    """Manages long-term user context and profiles."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the user context manager.
        
        Args:
            storage_dir: Directory for persisting user data
        """
        self.storage_dir = Path(storage_dir or Path(__file__).parent.parent / "data" / "users")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Dict] = {}
    
    def save_user_profile(self, user_id: str, profile: UserProfile) -> bool:
        """
        Save user profile to persistent storage.
        
        Args:
            user_id: Unique user identifier
            profile: UserProfile to save
            
        Returns:
            True if successful
        """
        try:
            file_path = self.storage_dir / f"{user_id}.json"
            
            data = {
                "user_id": user_id,
                "profile": profile.model_dump(),
                "updated_at": datetime.now().isoformat(),
                "version": 1
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self._cache[user_id] = data
            logger.info(f"Saved user profile: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save user profile: {e}")
            return False
    
    def load_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Load user profile from storage.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserProfile if found, None otherwise
        """
        # Check cache first
        if user_id in self._cache:
            return UserProfile(**self._cache[user_id]["profile"])
        
        try:
            file_path = self.storage_dir / f"{user_id}.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self._cache[user_id] = data
            return UserProfile(**data["profile"])
            
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}")
            return None
    
    def update_user_field(self, user_id: str, field: str, value: Any) -> bool:
        """
        Update a single field in user profile.
        
        Args:
            user_id: User identifier
            field: Field name to update
            value: New value
            
        Returns:
            True if successful
        """
        profile = self.load_user_profile(user_id) or UserProfile()
        
        if hasattr(profile, field):
            setattr(profile, field, value)
            return self.save_user_profile(user_id, profile)
        
        return False
    
    def add_scheme_interaction(
        self,
        user_id: str,
        scheme_id: str,
        interaction_type: str
    ) -> None:
        """
        Track user's interaction with a scheme.
        
        Args:
            user_id: User identifier
            scheme_id: Scheme identifier
            interaction_type: Type of interaction (viewed, applied, etc.)
        """
        try:
            file_path = self.storage_dir / f"{user_id}_history.json"
            
            history = []
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            
            history.append({
                "scheme_id": scheme_id,
                "type": interaction_type,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep last 100 interactions
            history = history[-100:]
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to track scheme interaction: {e}")
    
    def get_user_scheme_history(self, user_id: str) -> List[Dict]:
        """Get user's scheme interaction history."""
        try:
            file_path = self.storage_dir / f"{user_id}_history.json"
            
            if not file_path.exists():
                return []
            
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to get scheme history: {e}")
            return []
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data."""
        try:
            profile_path = self.storage_dir / f"{user_id}.json"
            history_path = self.storage_dir / f"{user_id}_history.json"
            
            if profile_path.exists():
                profile_path.unlink()
            if history_path.exists():
                history_path.unlink()
            
            if user_id in self._cache:
                del self._cache[user_id]
            
            logger.info(f"Deleted user data: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return False


# Singleton instance
user_context_manager = UserContextManager()
