from pydantic import BaseModel, field_validator, ValidationError
from typing import Dict, List, Union, Optional
from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

########################
### Pydantic Graph Classes ###
########################

class HWInputState(BaseModel):
    name1: str
    name2: str
    conversation: str
    context: Optional[str] = None

class HWOverallState(BaseModel):
    name1: str
    name2: str
    conversation: str
    context: Optional[str] = None
    name1_logical_score: Optional[int] = None
    name1_logical_explanation: Optional[str] = None
    name2_logical_score: Optional[int] = None
    name2_logical_explanation: Optional[str] = None
    name1_tonality: Optional[str] = None
    name1_tonality_explanation: Optional[str] = None
    name2_tonality: Optional[str] = None
    name2_tonality_explanation: Optional[str] = None
    name1_word_count: Optional[int] = None
    name1_volume_percentage: Optional[float] = None
    name2_word_count: Optional[int] = None
    name2_volume_percentage: Optional[float] = None
    name1_personal_attacks: Optional[List[str]] = None
    name2_personal_attacks: Optional[List[str]] = None

    @field_validator('name1_logical_score', 'name2_logical_score')
    @classmethod
    def validate_logical_score(cls, value):
        if not 0 <= value <= 100:
            raise ValueError("Logical score must be between 0 and 100")
        return value
    
class AnalysisOutput(BaseModel):
    name: str
    explanation: str
    logical_score: int
    logical_explanation: str
    tonality: str
    tonality_explanation: str
    word_count: int
    volume_percentage: float
    personal_attacks: List[str]

class FinalOutputState(BaseModel):
    winner: AnalysisOutput
    loser: AnalysisOutput


########################
### Output Classes ###
########################

class LogicalOutput(BaseModel):
    name1: str
    name2: str
    name1_logical_score: int
    name1_logical_explanation: str
    name2_logical_score: int
    name2_logical_explanation: str
    
class TonalOutput(BaseModel):
    name1: str
    name2: str
    name1_tonality: str
    name1_tonality_explanation: str
    name2_tonality: str
    name2_tonality_explanation: str

class VolumeOutput(BaseModel):
    name1: str
    name2: str
    name1_word_count: int
    name2_word_count: int

class PersonalAttackOutput(BaseModel):
    name1: str
    name2: str
    name1_personal_attacks: List[str]
    name2_personal_attacks: List[str]

class OverreactionInputState(BaseModel):
    name: str
    context : str
    conversation: str

class OverreactionOutput(BaseModel):
    is_overreacting: bool
    confidence_score: int  # 0-100
    explanation: str
    cognitive_distortions: str
    key_triggers: List[str]  # Specific phrases/moments that indicate overreaction
    suggested_responses: List[str]  # Alternative ways to respond
    emotional_state: str  # e.g., "Highly Emotional", "Slightly Agitated", "Reasonable"