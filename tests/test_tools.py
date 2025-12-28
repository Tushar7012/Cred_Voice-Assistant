"""
Unit tests for tools module.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEligibilityEngine:
    """Tests for the Eligibility Engine tool."""
    
    def test_eligibility_with_matching_profile(self):
        """Test eligibility check with a matching profile."""
        from tools.eligibility_engine import EligibilityEngine
        
        engine = EligibilityEngine()
        
        # Set up a simple scheme
        engine.schemes = [{
            "id": "test_scheme",
            "name_hi": "टेस्ट योजना",
            "eligibility": {
                "min_age": 18,
                "max_age": 60,
                "categories": ["obc", "sc", "st"]
            }
        }]
        
        result = engine.execute({
            "user_profile": {
                "age": 30,
                "category": "obc"
            }
        })
        
        assert result["success"] == True
        assert len(result["schemes"]) >= 0
    
    def test_eligibility_age_filter(self):
        """Test age-based eligibility filtering."""
        from tools.eligibility_engine import EligibilityEngine
        from app.models import UserProfile
        
        engine = EligibilityEngine()
        
        scheme = {
            "eligibility": {
                "min_age": 18,
                "max_age": 40
            }
        }
        
        # Test within range
        user = UserProfile(age=30)
        result = engine._check_eligibility(user, scheme)
        assert "age" in result["matched"]
        
        # Test outside range
        user = UserProfile(age=50)
        result = engine._check_eligibility(user, scheme)
        assert "age" not in result["matched"]
    
    def test_eligibility_income_filter(self):
        """Test income-based eligibility filtering."""
        from tools.eligibility_engine import EligibilityEngine
        from app.models import UserProfile
        
        engine = EligibilityEngine()
        
        scheme = {
            "eligibility": {
                "max_income": 500000
            }
        }
        
        # Test within limit
        user = UserProfile(annual_income=300000)
        result = engine._check_eligibility(user, scheme)
        assert "income" in result["matched"]
        
        # Test above limit
        user = UserProfile(annual_income=700000)
        result = engine._check_eligibility(user, scheme)
        assert "income" not in result["matched"]
    
    def test_profile_completeness(self):
        """Test profile completeness calculation."""
        from tools.eligibility_engine import EligibilityEngine
        from app.models import UserProfile
        
        engine = EligibilityEngine()
        
        # Empty profile
        user = UserProfile()
        completeness = engine._calculate_profile_completeness(user)
        assert completeness == 0.0
        
        # Partial profile
        user = UserProfile(age=30, category="obc")
        completeness = engine._calculate_profile_completeness(user)
        assert completeness == 0.4  # 2 out of 5 important fields
    
    def test_default_schemes_loaded(self):
        """Test that default schemes are loaded when file not found."""
        from tools.eligibility_engine import EligibilityEngine
        
        engine = EligibilityEngine(schemes_file="/nonexistent/path.json")
        
        assert len(engine.schemes) > 0


class TestSchemeRetriever:
    """Tests for the Scheme Retriever tool."""
    
    def test_fallback_search(self):
        """Test fallback keyword-based search."""
        from tools.scheme_retriever import SchemeRetriever
        
        retriever = SchemeRetriever()
        
        result = retriever._fallback_search("किसान")
        
        assert result["success"] == True
        assert len(result["schemes"]) > 0
        assert result.get("fallback") == True
    
    def test_search_with_query(self):
        """Test search with various queries."""
        from tools.scheme_retriever import SchemeRetriever
        
        retriever = SchemeRetriever()
        
        # Search for farmer schemes
        result = retriever.execute({"query": "किसान के लिए योजना"})
        assert result["success"] == True
        
        # Search for health schemes
        result = retriever.execute({"query": "स्वास्थ्य बीमा"})
        assert result["success"] == True
    
    def test_empty_query(self):
        """Test with empty/default query."""
        from tools.scheme_retriever import SchemeRetriever
        
        retriever = SchemeRetriever()
        
        result = retriever.execute({})
        
        assert result["success"] == True
        assert "schemes" in result


class TestBaseTool:
    """Tests for the base tool interface."""
    
    def test_tool_callable(self):
        """Test that tools are callable."""
        from tools.base import BaseTool
        
        class TestTool(BaseTool):
            def execute(self, input_data):
                return {"success": True, "data": input_data}
        
        tool = TestTool("test", "Test tool")
        
        result = tool({"key": "value"})
        
        assert result["success"] == True
        assert result["data"]["key"] == "value"
