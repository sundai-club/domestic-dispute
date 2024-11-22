import json
import base64
import os
import getpass
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from models import ArgumentResult, ArgumentState
from pydantic import BaseModel, field_validator, ValidationError
from langgraph.graph import START, StateGraph, MessagesState, END
from langchain_core.output_parsers import PydanticOutputParser
from models import ArgumentResult, ArgumentState, DisputeRequest
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_community.document_loaders.image import UnstructuredImageLoader
 

# TODO: This whole thing should be in a function that takes in the conversation as a string and returns the winner of the argument
load_dotenv()

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")
_set_env("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "langchain-academy"

async def async_result(person1:dict, person2:dict, conversation:str=""):
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

    # Load environment variables
    load_dotenv()

    #def _set_env(var: str):
   #     if not os.environ.get(var):
            #os.environ[var] = getpass.getpass(f"{var}: ")

  # # _set_env("OPENAI_API_KEY")
    #_set_env("LANGCHAIN_API_KEY")
   # os.environ["LANGCHAIN_TRACING_V2"] = "true"
   # os.environ["LANGCHAIN_PROJECT"] = "langchain-academy"

    
    # Define LLM with bound tools
    llm = ChatOpenAI(model="gpt-4o-2024-11-20")
    # llm_with_tools = llm.bind_tools(tools)

    # System messages
    distributor_msg = SystemMessage(content="You are the distributor of messages. You distribute messages to the logical judge, tonal judge, count judge, and personal attack judge.")
    logical_judge_msg = SystemMessage(content=open(Path(__file__).parent / "instructions" / "logical_judge_msg.txt").read().format(context1=person1["context"], context2=person2["context"], person1 = person1["name"], person2 = person2["name"]))
    tonal_judge_msg = SystemMessage(content=open(Path(__file__).parent / "instructions" / "tonal_judge_msg.txt").read().format(context1=person1["context"], context2=person2["context"], person1 = person1["name"], person2 = person2["name"]))
    count_judge_msg = SystemMessage(content=open(Path(__file__).parent / "instructions" / "count_judge_msg.txt").read())
    personal_attack_judge_msg = SystemMessage(content=open((Path(__file__).parent / "instructions" / "personal_attack_judge_msg.txt")).read().format(context1=person1["context"], context2=person2["context"], person1 = person1["name"], person2 = person2["name"]))
    final_arbiter_msg = SystemMessage(
        content=open(Path(__file__).parent / "instructions" / "final_arbiter_msg.txt").read().format(
            context1=person1["context"], 
            context2=person2["context"], 
            person1=person1["name"], 
            person2=person2["name"]
        )
    )

    # Node
    def distributor(state: MessagesState):     
        # print("---distributor---")
        return {"messages": [llm.invoke([distributor_msg] + state["messages"])]}

    # Node
    def logical_judge(state: MessagesState):
        # print("---logical judge---")
        return {"messages": [llm.invoke([logical_judge_msg] + state["messages"])]}

    # Node
    def tonal_judge(state: MessagesState):
        # print("---tonal judge---")
        return {"messages": [llm.invoke([tonal_judge_msg] + state["messages"])]}

    # Node
    def count_judge(state: MessagesState):
        # print("---count judge---")
        return {"messages": [llm.invoke([count_judge_msg] + state["messages"])]}

    # Node
    def personal_attack_judge(state: MessagesState):
        # print("---personal attack judge---")
        return {"messages": [llm.invoke([personal_attack_judge_msg] + state["messages"])]}

    # Node
    
    #def final_arbiter(state: MessagesState):
        # print("---final arbiter---")
    #   return {"messages": [llm.invoke([final_arbiter_msg] + state["messages"])]}

    argument_result_schema = {
        "name": "get_argument_result",
        "description": "Get the final result of the argument analysis",
        "parameters": ArgumentResult.model_json_schema()
    }

    def final_arbiter(state: MessagesState):
        response = llm.invoke(
            [final_arbiter_msg] + state["messages"],
            functions=[argument_result_schema],
            function_call={"name": "get_argument_result"}
        )
        
        try:
            function_call = response.additional_kwargs["function_call"]
            result = json.loads(function_call["arguments"])
            parsed_response = ArgumentResult(**result)
            return {"messages": [AIMessage(content=parsed_response.model_dump_json())]}
        except Exception as e:
            print(f"Parsing error: {e}")
            print(f"Raw response: {response}")
            raise ValueError(f"Failed to parse final arbiter response: {e}")
    # Build graph
    builder = StateGraph(MessagesState)

    # Add nodes
    builder.add_node("distributor", distributor)
    builder.add_node("logical_judge", logical_judge)
    builder.add_node("tonal_judge", tonal_judge)
    builder.add_node("count_judge", count_judge)
    builder.add_node("personal_attack_judge", personal_attack_judge)
    builder.add_node("final_arbiter", final_arbiter)

    # Add edges
    builder.add_edge(START, "distributor")
    builder.add_edge("distributor", "logical_judge")
    builder.add_edge("distributor", "tonal_judge")
    builder.add_edge("distributor", "count_judge")
    builder.add_edge("distributor", "personal_attack_judge")

    builder.add_edge("logical_judge", "final_arbiter")
    builder.add_edge("tonal_judge", "final_arbiter")
    builder.add_edge("count_judge", "final_arbiter")
    builder.add_edge("personal_attack_judge", "final_arbiter")
    builder.add_edge("final_arbiter", END)

    # Compile graph
    graph = builder.compile()

    # Invokation
    messages = graph.invoke({"messages": messages})
    result = []
    for m in messages['messages']: 
        result.append(m)

    # Validate JSON output
    try:
        output = result[-1].content
        json_output = json.loads(output)
        validated_output = ArgumentResult(**json_output)
        return validated_output
        
    except json.JSONDecodeError:
        print(output)
        raise ValueError("Output is not valid JSON")
    except ValidationError as e:
        raise ValueError(f"Invalid output format: {str(e)}")

def result(person1:dict, person2:dict, conversation:str=""):
    return asyncio.run(async_result(person1, person2, conversation))

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_text(path):
    image_path = Path(__file__).parent / path
    #load_dotenv()
    #def _set_env(var: str):
    #    if not os.environ.get(var):
    #        os.environ[var] = getpass.getpass(f"{var}: ")
    #_set_env("OPENAI_API_KEY")
    #_set_env("LANGCHAIN_API_KEY")
    #os.environ["LANGCHAIN_TRACING_V2"] = "true"
    #os.environ["LANGCHAIN_PROJECT"] = "langchain-academy"

    base64_image = encode_image(image_path)
    llm = ChatOpenAI(
        model="gpt-4o-2024-11-20",
        max_tokens=1024,
    )
    
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Transribe these iphone screenshots. Make sure it is in the format of a conversation between two people. with each message on a new line and beginnign with the name. Include emojis.The name of party 2 is at the top of the text. The name of party 2 is unknown and you should just put in a placeholder of 'sender'."},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            }
        ]
    )
    
    response = llm.invoke([message])
    print(response.content)
    return response.content



#extract_text("/Users/seanklein/Projects/Github/domestic-dispute/backend/images/IMG_0138.PNG")
#print(result(maya, arjun, open(Path(__file__).parent /"sample_argument.txt", "r", encoding="utf-8").read()))