"""
Contradiction detection and resolution.
Handles conflicting information in user inputs.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from llm.groq_client import groq_client


class ContradictionHandler:
    """Handles detection and resolution of contradictions in user information."""
    
    # Fields that are immutable once set (should always clarify)
    IMMUTABLE_FIELDS = {"gender", "category"}
    
    # Fields that might reasonably change
    MUTABLE_FIELDS = {"annual_income", "occupation", "state", "district"}
    
    def __init__(self):
        """Initialize the contradiction handler."""
        self.detected_contradictions: List[Dict] = []
    
    def detect_contradiction(
        self,
        field: str,
        old_value: Any,
        new_value: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if there's a contradiction between old and new values.
        
        Args:
            field: Field name
            old_value: Previous value
            new_value: New value
            
        Returns:
            Contradiction dict if detected, None otherwise
        """
        if old_value is None or new_value is None:
            return None
        
        if old_value == new_value:
            return None
        
        # Age should generally only increase slightly between sessions
        if field == "age":
            if isinstance(old_value, int) and isinstance(new_value, int):
                # Allow +1 year as natural progression
                if new_value == old_value + 1:
                    return None
        
        contradiction = {
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "timestamp": datetime.now().isoformat(),
            "severity": self._get_severity(field)
        }
        
        self.detected_contradictions.append(contradiction)
        logger.warning(f"Contradiction detected: {contradiction}")
        
        return contradiction
    
    def _get_severity(self, field: str) -> str:
        """Determine the severity of a contradiction."""
        if field in self.IMMUTABLE_FIELDS:
            return "high"
        elif field in self.MUTABLE_FIELDS:
            return "low"
        else:
            return "medium"
    
    def generate_clarification(self, contradiction: Dict[str, Any]) -> str:
        """
        Generate a clarification question for a contradiction.
        
        Args:
            contradiction: Contradiction information
            
        Returns:
            Hindi clarification question
        """
        field = contradiction["field"]
        old_val = contradiction["old_value"]
        new_val = contradiction["new_value"]
        
        field_names_hi = {
            "age": "उम्र",
            "annual_income": "वार्षिक आय",
            "category": "श्रेणी",
            "state": "राज्य",
            "gender": "लिंग",
            "occupation": "व्यवसाय",
            "is_bpl": "BPL स्थिति"
        }
        
        field_hi = field_names_hi.get(field, field)
        
        if contradiction["severity"] == "high":
            return f"आपने पहले अपना {field_hi} '{old_val}' बताया था, लेकिन अब '{new_val}' बता रहे हैं। सही जानकारी देने के लिए कृपया स्पष्ट करें - आपका सही {field_hi} क्या है?"
        else:
            return f"आपने पहले {field_hi} '{old_val}' बताया था। क्या यह बदलकर '{new_val}' हो गया है?"
    
    def resolve_contradiction(
        self,
        contradiction: Dict[str, Any],
        user_response: str
    ) -> Dict[str, Any]:
        """
        Resolve a contradiction based on user's response.
        
        Args:
            contradiction: The contradiction to resolve
            user_response: User's clarification response
            
        Returns:
            Resolution result
        """
        prompt = f"""उपयोगकर्ता ने विरोधाभास को स्पष्ट किया है।

विरोधाभास:
- फ़ील्ड: {contradiction['field']}
- पुराना मान: {contradiction['old_value']}
- नया मान: {contradiction['new_value']}

उपयोगकर्ता का जवाब: {user_response}

JSON में बताएं कि सही मान क्या है:
{{"correct_value": "सही मान", "understood": true/false}}"""

        try:
            messages = [
                {"role": "system", "content": "आप एक जानकारी निकालने वाले सहायक हैं।"},
                {"role": "user", "content": prompt}
            ]
            
            result = groq_client.chat_json(messages, temperature=0.1)
            
            return {
                "field": contradiction["field"],
                "resolved_value": result.get("correct_value", contradiction["new_value"]),
                "understood": result.get("understood", True)
            }
            
        except Exception as e:
            logger.error(f"Failed to resolve contradiction: {e}")
            # Default to newer value
            return {
                "field": contradiction["field"],
                "resolved_value": contradiction["new_value"],
                "understood": False
            }
    
    def get_pending_contradictions(self) -> List[Dict]:
        """Get list of unresolved contradictions."""
        return [c for c in self.detected_contradictions if not c.get("resolved", False)]
    
    def clear_contradictions(self) -> None:
        """Clear all detected contradictions."""
        self.detected_contradictions = []


# Singleton instance
contradiction_handler = ContradictionHandler()
