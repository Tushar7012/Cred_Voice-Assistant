"""
Eligibility Engine Tool - Matches users to eligible government schemes.
Rule-based matching system using user profile and scheme eligibility criteria.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from tools.base import BaseTool
from app.models import UserProfile, Scheme, SchemeMatch, SchemeEligibility, CategoryEnum, GenderEnum


class EligibilityEngine(BaseTool):
    """
    Tool for matching users to eligible government schemes.
    Uses rule-based matching against scheme eligibility criteria.
    """
    
    def __init__(self, schemes_file: Optional[str] = None):
        """
        Initialize the eligibility engine.
        
        Args:
            schemes_file: Path to JSON file containing scheme data
        """
        super().__init__(
            name="eligibility_engine",
            description="उपयोगकर्ता प्रोफ़ाइल के आधार पर पात्र योजनाएं खोजता है"
        )
        self.schemes: List[Dict] = []
        self.schemes_file = schemes_file or str(Path(__file__).parent.parent / "data" / "schemes" / "schemes.json")
        self._load_schemes()
    
    def _load_schemes(self) -> None:
        """Load schemes from JSON file."""
        try:
            schemes_path = Path(self.schemes_file)
            if schemes_path.exists():
                with open(schemes_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.schemes = data.get("schemes", [])
                logger.info(f"Loaded {len(self.schemes)} schemes from {self.schemes_file}")
            else:
                logger.warning(f"Schemes file not found: {self.schemes_file}")
                self.schemes = self._get_default_schemes()
        except Exception as e:
            logger.error(f"Error loading schemes: {e}")
            self.schemes = self._get_default_schemes()
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find eligible schemes for a user.
        
        Args:
            input_data: Contains 'user_profile' dict
            
        Returns:
            Dict with eligible schemes and match details
        """
        logger.info("Executing eligibility engine")
        
        user_profile_data = input_data.get("user_profile", {})
        user_profile = UserProfile(**{k: v for k, v in user_profile_data.items() if v is not None})
        
        eligible_schemes = []
        
        for scheme_data in self.schemes:
            match_result = self._check_eligibility(user_profile, scheme_data)
            if match_result["is_eligible"]:
                eligible_schemes.append({
                    "scheme": scheme_data,
                    "match_score": match_result["score"],
                    "matched_criteria": match_result["matched"],
                    "missing_criteria": match_result["missing"],
                    "missing_user_info": match_result["missing_user_info"]
                })
        
        # Sort by match score
        eligible_schemes.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "success": True,
            "schemes": eligible_schemes[:10],  # Return top 10
            "total_matches": len(eligible_schemes),
            "user_profile_completeness": self._calculate_profile_completeness(user_profile)
        }
    
    def _check_eligibility(
        self, 
        user: UserProfile, 
        scheme: Dict
    ) -> Dict[str, Any]:
        """Check if user is eligible for a scheme."""
        eligibility = scheme.get("eligibility", {})
        matched = []
        missing = []
        missing_user_info = []
        
        score = 0.0
        total_criteria = 0
        
        # Age check
        if eligibility.get("min_age") or eligibility.get("max_age"):
            total_criteria += 1
            if user.age is not None:
                min_age = eligibility.get("min_age", 0)
                max_age = eligibility.get("max_age", 150)
                if min_age <= user.age <= max_age:
                    matched.append("age")
                    score += 1
                else:
                    missing.append(f"age: {min_age}-{max_age} required")
            else:
                missing_user_info.append("age")
        
        # Income check
        if eligibility.get("max_income"):
            total_criteria += 1
            if user.annual_income is not None:
                if user.annual_income <= eligibility["max_income"]:
                    matched.append("income")
                    score += 1
                else:
                    missing.append(f"income: max {eligibility['max_income']} required")
            else:
                missing_user_info.append("annual_income")
        
        # Category check
        if eligibility.get("categories"):
            total_criteria += 1
            if user.category:
                category_str = user.category.value if isinstance(user.category, CategoryEnum) else user.category
                if category_str in eligibility["categories"]:
                    matched.append("category")
                    score += 1
                else:
                    missing.append(f"category: {eligibility['categories']} required")
            else:
                missing_user_info.append("category")
        
        # State check
        if eligibility.get("states"):
            total_criteria += 1
            if user.state:
                if user.state.lower() in [s.lower() for s in eligibility["states"]]:
                    matched.append("state")
                    score += 1
                else:
                    missing.append(f"state: {eligibility['states']} required")
            else:
                missing_user_info.append("state")
        
        # Gender check
        if eligibility.get("gender"):
            total_criteria += 1
            if user.gender:
                gender_str = user.gender.value if isinstance(user.gender, GenderEnum) else user.gender
                if gender_str in eligibility["gender"]:
                    matched.append("gender")
                    score += 1
                else:
                    missing.append(f"gender: {eligibility['gender']} required")
            else:
                missing_user_info.append("gender")
        
        # BPL check
        if eligibility.get("requires_bpl"):
            total_criteria += 1
            if user.is_bpl is not None:
                if user.is_bpl:
                    matched.append("bpl_status")
                    score += 1
                else:
                    missing.append("BPL card required")
            else:
                missing_user_info.append("is_bpl")
        
        # Calculate final score
        final_score = score / total_criteria if total_criteria > 0 else 0.5
        
        # User is eligible if they match all criteria that can be checked
        # and don't fail any criteria
        is_eligible = len(missing) == 0 and (len(matched) > 0 or total_criteria == 0)
        
        return {
            "is_eligible": is_eligible,
            "score": final_score,
            "matched": matched,
            "missing": missing,
            "missing_user_info": missing_user_info
        }
    
    def _calculate_profile_completeness(self, user: UserProfile) -> float:
        """Calculate how complete the user profile is."""
        important_fields = ["age", "annual_income", "category", "state", "gender"]
        filled = sum(1 for f in important_fields if getattr(user, f, None) is not None)
        return filled / len(important_fields)
    
    def _get_default_schemes(self) -> List[Dict]:
        """Return default schemes if file not found."""
        return [
            {
                "id": "pm_kisan",
                "name_en": "PM-KISAN",
                "name_hi": "प्रधानमंत्री किसान सम्मान निधि",
                "description_hi": "किसानों को प्रति वर्ष ₹6,000 की वित्तीय सहायता",
                "ministry": "Ministry of Agriculture",
                "scheme_type": "central",
                "eligibility": {
                    "max_land_holding": 5.0,
                    "categories": ["general", "sc", "st", "obc", "ews"]
                },
                "benefits_hi": "प्रति वर्ष ₹6,000 तीन किस्तों में",
                "required_documents": ["आधार कार्ड", "बैंक खाता", "भूमि रिकॉर्ड"],
                "how_to_apply_hi": "नजदीकी CSC केंद्र या pmkisan.gov.in पर आवेदन करें"
            },
            {
                "id": "pm_awas_gramin",
                "name_en": "PM Awas Yojana (Gramin)",
                "name_hi": "प्रधानमंत्री आवास योजना (ग्रामीण)",
                "description_hi": "ग्रामीण क्षेत्रों में पक्के मकान के लिए वित्तीय सहायता",
                "ministry": "Ministry of Rural Development",
                "scheme_type": "central",
                "eligibility": {
                    "categories": ["sc", "st", "obc", "ews"],
                    "requires_bpl": True,
                    "max_income": 300000
                },
                "benefits_hi": "पक्का मकान बनाने के लिए ₹1.20 लाख से ₹1.30 लाख",
                "required_documents": ["आधार कार्ड", "BPL कार्ड", "बैंक खाता"],
                "how_to_apply_hi": "ग्राम पंचायत या pmayg.nic.in पर आवेदन करें"
            },
            {
                "id": "ayushman_bharat",
                "name_en": "Ayushman Bharat PM-JAY",
                "name_hi": "आयुष्मान भारत प्रधानमंत्री जन आरोग्य योजना",
                "description_hi": "गरीब परिवारों के लिए स्वास्थ्य बीमा योजना",
                "ministry": "Ministry of Health",
                "scheme_type": "central",
                "eligibility": {
                    "categories": ["sc", "st", "obc", "ews"],
                    "max_income": 500000
                },
                "benefits_hi": "प्रति परिवार प्रति वर्ष ₹5 लाख तक का स्वास्थ्य बीमा",
                "required_documents": ["आधार कार्ड", "राशन कार्ड"],
                "how_to_apply_hi": "नजदीकी CSC केंद्र या pmjay.gov.in पर आवेदन करें"
            },
            {
                "id": "pm_ujjwala",
                "name_en": "PM Ujjwala Yojana",
                "name_hi": "प्रधानमंत्री उज्ज्वला योजना",
                "description_hi": "गरीब महिलाओं को मुफ्त LPG कनेक्शन",
                "ministry": "Ministry of Petroleum",
                "scheme_type": "central",
                "eligibility": {
                    "gender": ["female"],
                    "min_age": 18,
                    "requires_bpl": True
                },
                "benefits_hi": "मुफ्त LPG कनेक्शन और पहला सिलेंडर मुफ्त",
                "required_documents": ["आधार कार्ड", "BPL कार्ड", "बैंक खाता"],
                "how_to_apply_hi": "नजदीकी LPG वितरक से संपर्क करें"
            },
            {
                "id": "sukanya_samriddhi",
                "name_en": "Sukanya Samriddhi Yojana",
                "name_hi": "सुकन्या समृद्धि योजना",
                "description_hi": "बालिकाओं के लिए बचत योजना",
                "ministry": "Ministry of Finance",
                "scheme_type": "central",
                "eligibility": {
                    "gender": ["female"],
                    "max_age": 10,
                    "categories": ["general", "sc", "st", "obc", "ews"]
                },
                "benefits_hi": "उच्च ब्याज दर और कर लाभ",
                "required_documents": ["बालिका का जन्म प्रमाण पत्र", "माता-पिता का आधार"],
                "how_to_apply_hi": "किसी भी पोस्ट ऑफिस या बैंक में खाता खोलें"
            },
            {
                "id": "pm_shram_yogi",
                "name_en": "PM Shram Yogi Maan-dhan",
                "name_hi": "प्रधानमंत्री श्रम योगी मान-धन",
                "description_hi": "असंगठित क्षेत्र के श्रमिकों के लिए पेंशन योजना",
                "ministry": "Ministry of Labour",
                "scheme_type": "central",
                "eligibility": {
                    "min_age": 18,
                    "max_age": 40,
                    "max_income": 180000,
                    "categories": ["general", "sc", "st", "obc", "ews"]
                },
                "benefits_hi": "60 वर्ष के बाद ₹3,000 प्रति माह पेंशन",
                "required_documents": ["आधार कार्ड", "बैंक खाता"],
                "how_to_apply_hi": "नजदीकी CSC केंद्र पर आवेदन करें"
            }
        ]


# Singleton instance
eligibility_engine = EligibilityEngine()


def check_eligibility(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for eligibility check."""
    return eligibility_engine.execute(input_data)
