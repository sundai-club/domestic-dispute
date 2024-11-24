from pathlib import Path
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from langgraph.graph import START, StateGraph, MessagesState, END
from langgraph.prebuilt import tools_condition, ToolNode
from pydantic import BaseModel, field_validator, ValidationError
from typing import Dict, List, Union, Optional
from typing import Annotated
from functools import partial
import operator
import json


########################
### Pydantic Graph Classes ###
########################

class HWInputState(BaseModel):
    name1: str
    name2: str
    conversation: str

class HWOverallState(BaseModel):
    name1: str
    name2: str
    conversation: str
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


########################
### LLM Definitions ###
########################

# Define LLM with bound tools
llm = ChatOpenAI(model="gpt-4o-2024-11-20")
#llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
# llm_with_tools = llm.bind_tools(tools)


########################
### Nodes ###
########################

# Node
def distributor(state: HWInputState):
    return state

# Node
def logical_judge(state: HWOverallState):
    sys_msg = SystemMessage(content=open(Path(__file__).parent / "instructions" / "logical_judge_msg.txt").read().format(
        name1 = state.name1,
        name2 = state.name2
    ))

    llm_output = llm.with_structured_output(LogicalOutput).invoke([sys_msg] + [state.conversation])

    state.name1 = None
    state.name2 = None
    state.conversation = None
    state.name1_logical_score = llm_output.name1_logical_score
    state.name1_logical_explanation = llm_output.name1_logical_explanation
    state.name2_logical_score = llm_output.name2_logical_score
    state.name2_logical_explanation = llm_output.name2_logical_explanation

    return state

# Node
def tonal_judge(state: HWOverallState):
    sys_msg = SystemMessage(content=open(Path(__file__).parent / "instructions" / "tonal_judge_msg.txt").read().format(
        name1 = state.name1,
        name2 = state.name2
    ))

    llm_output = llm.with_structured_output(TonalOutput).invoke([sys_msg] + [state.conversation])

    state.name1 = None
    state.name2 = None
    state.conversation = None
    state.name1_tonality = llm_output.name1_tonality
    state.name1_tonality_explanation = llm_output.name1_tonality_explanation
    state.name2_tonality = llm_output.name2_tonality
    state.name2_tonality_explanation = llm_output.name2_tonality_explanation

    return state

# Node
def volume_judge(state: HWOverallState):
    sys_msg = SystemMessage(content=open(Path(__file__).parent / "instructions" / "volume_judge_msg.txt").read().format(
        name1 = state.name1,
        name2 = state.name2
    ))

    llm_output = llm.with_structured_output(VolumeOutput).invoke([sys_msg] + [state.conversation])

    state.name1 = None
    state.name2 = None
    state.conversation = None
    state.name1_word_count = llm_output.name1_word_count
    state.name2_word_count = llm_output.name2_word_count
    state.name1_volume_percentage = (llm_output.name1_word_count / (llm_output.name1_word_count + llm_output.name2_word_count)) * 100
    state.name2_volume_percentage = (llm_output.name2_word_count / (llm_output.name1_word_count + llm_output.name2_word_count)) * 100

    return state

# Node
def personal_attack_judge(state: HWOverallState):
    sys_msg = SystemMessage(content=open(Path(__file__).parent / "instructions" / "personal_attack_judge_msg.txt").read().format(
        name1 = state.name1,
        name2 = state.name2
    ))

    llm_output = llm.with_structured_output(PersonalAttackOutput).invoke([sys_msg] + [state.conversation])

    state.name1 = None
    state.name2 = None
    state.conversation = None
    state.name1_personal_attacks = llm_output.name1_personal_attacks
    state.name2_personal_attacks = llm_output.name2_personal_attacks

    return state

# Node
def final_arbiter(state: HWOverallState) -> FinalOutputState:
    sys_msg = SystemMessage(content=open(Path(__file__).parent / "instructions" / "final_arbiter_msg.txt").read().format(
        name1 = state.name1,
        name2 = state.name2
    ))

    if isinstance(llm, ChatOpenAI):
        msg_dict = {
            "role": "assistant",
            "content": json.dumps(state.model_dump(exclude={'conversation'}))
        }
    elif isinstance(llm, ChatAnthropic):
        msg_dict = [
            {"role": "user", "content": json.dumps(state.model_dump(exclude={'conversation'}))}
        ]

    return llm.with_structured_output(FinalOutputState).invoke([sys_msg] + [msg_dict])
    
########################
### Graph ###
########################

# Build graph
builder = StateGraph(HWOverallState, input=HWInputState, output=FinalOutputState)

# Add nodes
builder.add_node("distributor", distributor)
builder.add_node("logical_judge", logical_judge)
builder.add_node("tonal_judge", tonal_judge)
builder.add_node("volume_judge", volume_judge)
builder.add_node("personal_attack_judge", personal_attack_judge)
builder.add_node("final_arbiter", final_arbiter)

# Add edges
builder.add_edge(START, "distributor")
builder.add_edge("distributor", "logical_judge")
builder.add_edge("distributor", "tonal_judge")
builder.add_edge("distributor", "volume_judge")
builder.add_edge("distributor", "personal_attack_judge")

builder.add_edge(["logical_judge", "tonal_judge", "volume_judge", "personal_attack_judge"], "final_arbiter")
builder.add_edge("final_arbiter", END)


########################
### Compile Graph ###
########################

# Compile graph
graph = builder.compile()