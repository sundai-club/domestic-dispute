from pydantic import BaseModel, field_validator, ValidationError
from typing import Dict, List, Union, Optional

class ArgumentState(BaseModel):
    name1: str
    name2: str
    context1: str
    context2: str
    conversation: str

class ArgumentResult(BaseModel):
    winner: str
    winner_logical_score: int
    winner_tonality: str
    winner_count: int
    winner_personal_attacks: Dict[str, Union[List, int]]
    winner_explanation: str
    loser: str
    loser_logical_score: int
    loser_tonality: str
    loser_count: int
    loser_personal_attacks: Dict[str, Union[List, int]]
    loser_explanation: str

    @field_validator('winner_logical_score')
    @classmethod
    def validate_logical_score(cls, value):
        if not 0 <= value <= 100:
            raise ValueError("Logical score must be between 0 and 100")
        return value
    
    @field_validator('loser_logical_score')
    @classmethod
    def validate_logical_score(cls, value):
        if not 0 <= value <= 100:
            raise ValueError("Logical score must be between 0 and 100")
        return value

class DisputeRequest(BaseModel):
    text: str  # The entire conversation as a single text block
    party_one_name: str
    party_two_name: str
    context1: str  # Party one's context
    context2: str  # Party two's context
