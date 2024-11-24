import json
import base64
import os
import getpass
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from models import HWInputState, HWOverallState, AnalysisOutput, FinalOutputState
from models import LogicalOutput, TonalOutput, VolumeOutput, PersonalAttackOutput
from pydantic import BaseModel, field_validator, ValidationError
from langgraph.graph import START, StateGraph, MessagesState, END
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_community.document_loaders.image import UnstructuredImageLoader
from PIL import Image
from PIL.ExifTags import TAGS
from image_processor import sort_images_chronologically

# Load environment variables
load_dotenv()

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")
_set_env("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "langchain-academy"

async def async_result(person1:str, person2:str, conversation:str=""):
    """
    Inputs-
        person1 {'name':'', 'context':''}
        person2 {'name':'', 'context':''}
        conversation
    returns json
        {'winner': 'Maya', 'winner_logical_score': 60, 'winner_tonality': 'Frustrated', 'winner_count': 27, 'winner_personal_attacks': {'Maya': ['The truth is, you only put in effort when it benefits you.', 'Of course you are. You’re always done when it’s about me.']}, 'winner_explanation': 'Maya won because she consistently communicated her needs for more explicit support and appreciation from Arjun, highlighting the emotional aspect of their relationship. Despite some personal attacks, her argument focused on the lack of emotional connection and validation from Arjun, which was the central issue of the dispute.', 'loser': 'Arjun', 'loser_logical_score': 55, 'loser_tonality': 'Defensive', 'loser_count': 25, 'loser_personal_attacks': {'Arjun': ['Maybe because you celebrate enough for both of us?', 'I expect you to understand that I’m trying.']}, 'loser_explanation': "Arjun lost because his responses were largely defensive and did not adequately address Maya's concerns about lack of appreciation. While he insisted he was supportive in his own way, he failed to acknowledge the emotional needs Maya expressed, which left the core issue unresolved."}

    """

    convo_msgs = conversation.splitlines()
    messages = []
    for msg in convo_msgs:
        messages.append(HumanMessage(content=msg))

    # Define LLM with bound tools
    llm = ChatOpenAI(model="gpt-4o-2024-11-20")


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
    builder = StateGraph(MessagesState)

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

    # Compile graph
    graph = builder.compile()

    # Invokation
    return graph.invoke({"name1": person1, "name2": person2, "conversation": conversation})


def result(person1:str, person2:str, conversation:str=""):
    return asyncio.run(async_result(person1, person2, conversation))



# Example usage:
# paths = [
#     "/images/IMG_0138.PNG",
#     "/images/IMG_0139.PNG"
# ]
# conversation = extract_text(paths)
    


#extract_multiple_text(sort_images_chronologically([
#  "/Users/seanklein/Projects/Github/homewrecker_ai/backend/backend/images/IMG_0144.PNG", 
#  "/Users/seanklein/Projects/Github/homewrecker_ai/backend/backend/images/IMG_0145.PNG"
#]))
#extract_text("/Users/seanklein/Projects/Github/domestic-dispute/backend/images/IMG_0138.PNG")
#print(result(maya, arjun, open(Path(__file__).parent /"sample_argument.txt", "r", encoding="utf-8").read()))