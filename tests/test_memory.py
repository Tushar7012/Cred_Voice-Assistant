"""
Unit tests for memory module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import UserProfile, ConversationMemory


class TestConversationManager:
    """Tests for conversation memory management."""
    
    def test_create_session(self):
        """Test session creation."""
        from memory.conversation import ConversationManager
        
        manager = ConversationManager()
        session = manager.create_session("test_123")
        
        assert session.session_id == "test_123"
        assert len(session.turns) == 0
    
    def test_add_turn(self):
        """Test adding conversation turn."""
        from memory.conversation import ConversationManager
        
        manager = ConversationManager()
        manager.create_session("test_123")
        
        turn = manager.add_turn(
            session_id="test_123",
            user_input="टेस्ट इनपुट",
            agent_response="टेस्ट रिस्पॉन्स"
        )
        
        assert turn.turn_id == 0
        assert turn.user_input_text == "टेस्ट इनपुट"
    
    def test_max_turns_limit(self):
        """Test that turns are limited."""
        from memory.conversation import ConversationManager
        
        manager = ConversationManager(max_turns=5)
        manager.create_session("test_123")
        
        for i in range(10):
            manager.add_turn("test_123", f"input_{i}", f"response_{i}")
        
        session = manager.get_session("test_123")
        assert len(session.turns) == 5
    
    def test_context_string(self):
        """Test getting context string."""
        from memory.conversation import ConversationManager
        
        manager = ConversationManager()
        manager.create_session("test_123")
        manager.add_turn("test_123", "सवाल 1", "जवाब 1")
        manager.add_turn("test_123", "सवाल 2", "जवाब 2")
        
        context = manager.get_context_string("test_123", num_turns=2)
        
        assert "सवाल 1" in context
        assert "जवाब 1" in context
    
    def test_export_session(self):
        """Test session export."""
        from memory.conversation import ConversationManager
        
        manager = ConversationManager()
        manager.create_session("test_123")
        manager.add_turn("test_123", "इनपुट", "आउटपुट")
        
        exported = manager.export_session("test_123")
        
        assert exported["session_id"] == "test_123"
        assert len(exported["turns"]) == 1


class TestContradictionHandler:
    """Tests for contradiction detection."""
    
    def test_detect_contradiction(self):
        """Test contradiction detection."""
        from memory.contradiction import ContradictionHandler
        
        handler = ContradictionHandler()
        
        contradiction = handler.detect_contradiction("age", 35, 42)
        
        assert contradiction is not None
        assert contradiction["field"] == "age"
        assert contradiction["old_value"] == 35
        assert contradiction["new_value"] == 42
    
    def test_no_contradiction_same_value(self):
        """Test no contradiction for same values."""
        from memory.contradiction import ContradictionHandler
        
        handler = ContradictionHandler()
        
        contradiction = handler.detect_contradiction("age", 35, 35)
        
        assert contradiction is None
    
    def test_severity_levels(self):
        """Test severity level assignment."""
        from memory.contradiction import ContradictionHandler
        
        handler = ContradictionHandler()
        
        # High severity (immutable field)
        c = handler.detect_contradiction("gender", "male", "female")
        assert c["severity"] == "high"
        
        # Low severity (mutable field)
        handler.detected_contradictions = []
        c = handler.detect_contradiction("annual_income", 100000, 200000)
        assert c["severity"] == "low"
    
    def test_generate_clarification(self):
        """Test clarification question generation."""
        from memory.contradiction import ContradictionHandler
        
        handler = ContradictionHandler()
        
        contradiction = {
            "field": "age",
            "old_value": 35,
            "new_value": 42,
            "severity": "medium"
        }
        
        question = handler.generate_clarification(contradiction)
        
        assert "35" in question
        assert "42" in question
        assert "उम्र" in question


class TestUserContextManager:
    """Tests for user context persistence."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_save_and_load_profile(self, temp_storage):
        """Test saving and loading user profile."""
        from memory.user_context import UserContextManager
        
        manager = UserContextManager(storage_dir=temp_storage)
        
        profile = UserProfile(age=30, category="obc", state="Maharashtra")
        manager.save_user_profile("user_123", profile)
        
        loaded = manager.load_user_profile("user_123")
        
        assert loaded.age == 30
        assert loaded.category == "obc"
    
    def test_load_nonexistent_profile(self, temp_storage):
        """Test loading non-existent profile."""
        from memory.user_context import UserContextManager
        
        manager = UserContextManager(storage_dir=temp_storage)
        
        loaded = manager.load_user_profile("nonexistent")
        
        assert loaded is None
    
    def test_update_field(self, temp_storage):
        """Test updating single field."""
        from memory.user_context import UserContextManager
        
        manager = UserContextManager(storage_dir=temp_storage)
        
        profile = UserProfile(age=30)
        manager.save_user_profile("user_123", profile)
        
        manager.update_user_field("user_123", "age", 35)
        
        loaded = manager.load_user_profile("user_123")
        assert loaded.age == 35
    
    def test_scheme_interaction_history(self, temp_storage):
        """Test tracking scheme interactions."""
        from memory.user_context import UserContextManager
        
        manager = UserContextManager(storage_dir=temp_storage)
        
        manager.add_scheme_interaction("user_123", "pm_kisan", "viewed")
        manager.add_scheme_interaction("user_123", "ayushman", "applied")
        
        history = manager.get_user_scheme_history("user_123")
        
        assert len(history) == 2
        assert history[0]["scheme_id"] == "pm_kisan"
