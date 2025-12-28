"""
Pydantic data models for the Voice Assistant application.
Defines all data structures used throughout the system.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field


# Enums for type safety
class AgentStateEnum(str, Enum):
    """States in the agent lifecycle."""
    LISTENING = "listening"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    RESPONDING = "responding"
    ERROR_HANDLING = "error_handling"


class CategoryEnum(str, Enum):
    """Social category for eligibility."""
    GENERAL = "general"
    SC = "sc"
    ST = "st"
    OBC = "obc"
    EWS = "ews"


class GenderEnum(str, Enum):
    """Gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# User Profile Models
class UserProfile(BaseModel):
    """User profile for eligibility matching."""
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[GenderEnum] = None
    annual_income: Optional[float] = Field(None, ge=0)
    category: Optional[CategoryEnum] = None
    state: Optional[str] = None
    district: Optional[str] = None
    occupation: Optional[str] = None
    is_bpl: Optional[bool] = None  # Below Poverty Line
    is_disabled: Optional[bool] = None
    education_level: Optional[str] = None
    marital_status: Optional[str] = None
    has_bank_account: Optional[bool] = None
    has_ration_card: Optional[bool] = None
    land_holding_acres: Optional[float] = None
    
    def get_missing_fields(self) -> List[str]:
        """Get list of fields that are not filled."""
        missing = []
        for field_name, value in self.model_dump().items():
            if value is None:
                missing.append(field_name)
        return missing
    
    def get_filled_fields(self) -> Dict[str, Any]:
        """Get dictionary of filled fields."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


# Government Scheme Models
class SchemeEligibility(BaseModel):
    """Eligibility criteria for a scheme."""
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    gender: Optional[List[GenderEnum]] = None
    categories: Optional[List[CategoryEnum]] = None
    max_income: Optional[float] = None
    states: Optional[List[str]] = None  # None means all states
    occupations: Optional[List[str]] = None
    requires_bpl: Optional[bool] = None
    requires_disability: Optional[bool] = None
    min_land_holding: Optional[float] = None
    max_land_holding: Optional[float] = None


class Scheme(BaseModel):
    """Government scheme information."""
    id: str
    name_en: str
    name_hi: str
    description_en: str
    description_hi: str
    ministry: str
    scheme_type: str  # central, state
    eligibility: SchemeEligibility
    benefits_en: str
    benefits_hi: str
    required_documents: List[str]
    how_to_apply_en: str
    how_to_apply_hi: str
    official_url: Optional[str] = None
    helpline: Optional[str] = None


class SchemeMatch(BaseModel):
    """Result of scheme matching."""
    scheme: Scheme
    match_score: float = Field(ge=0, le=1)
    matched_criteria: List[str]
    missing_criteria: List[str]
    missing_user_info: List[str]


# Conversation Models
class ConversationTurn(BaseModel):
    """A single turn in the conversation."""
    turn_id: int
    timestamp: datetime = Field(default_factory=datetime.now)
    user_input_text: str
    user_input_audio_path: Optional[str] = None
    agent_response_text: str
    agent_response_audio_path: Optional[str] = None
    agent_state: AgentStateEnum
    tools_used: List[str] = []
    extracted_info: Dict[str, Any] = {}
    confidence_score: float = Field(default=0.0, ge=0, le=1)


class ConversationMemory(BaseModel):
    """Conversation history and context."""
    session_id: str
    turns: List[ConversationTurn] = []
    user_profile: UserProfile = Field(default_factory=UserProfile)
    current_intent: Optional[str] = None
    schemes_discussed: List[str] = []
    contradictions_detected: List[Dict[str, Any]] = []


# Agent Models
class PlanStep(BaseModel):
    """A step in the agent's plan."""
    step_id: int
    action: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    expected_output: str
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None


class AgentPlan(BaseModel):
    """Plan created by the Planner agent."""
    plan_id: str
    user_intent: str
    required_info: List[str]
    missing_info: List[str]
    steps: List[PlanStep]
    created_at: datetime = Field(default_factory=datetime.now)


class AgentState(BaseModel):
    """Current state of the agent system."""
    current_state: AgentStateEnum = AgentStateEnum.LISTENING
    current_plan: Optional[AgentPlan] = None
    current_step_index: int = 0
    execution_results: List[Dict[str, Any]] = []
    evaluation_result: Optional[Dict[str, Any]] = None
    error_count: int = 0
    max_retries: int = 3


# Tool Models
class ToolResult(BaseModel):
    """Result from a tool execution."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: float


# Voice Models
class STTResult(BaseModel):
    """Result from Speech-to-Text."""
    text: str
    language_code: str
    confidence: float = Field(ge=0, le=1)
    audio_duration_seconds: float


class TTSResult(BaseModel):
    """Result from Text-to-Speech."""
    audio_data: bytes
    audio_format: str = "wav"
    duration_seconds: float
    text_length: int
