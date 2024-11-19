import os, getpass
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from models import ArgumentResult, ArgumentState
from pydantic import BaseModel, field_validator, ValidationError
from langgraph.graph import START, StateGraph, MessagesState, END
from langchain_core.output_parsers import PydanticOutputParser
from models import ArgumentResult, ArgumentState, DisputeRequest

# TODO: This whole thing should be in a function that takes in the conversation as a string and returns the winner of the argument

def result(person1:dict, person2:dict, conversation:str=""):
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

    def _set_env(var: str):
        if not os.environ.get(var):
            os.environ[var] = getpass.getpass(f"{var}: ")

    _set_env("OPENAI_API_KEY")
    _set_env("LANGCHAIN_API_KEY")
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "langchain-academy"

    # Define LLM with bound tools
    llm = ChatOpenAI(model="gpt-4o")
    # llm_with_tools = llm.bind_tools(tools)

    # System messages
    distributor_msg = SystemMessage(content="You are the distributor of messages. You distribute messages to the logical judge, tonal judge, count judge, and personal attack judge.")
    logical_judge_msg = SystemMessage(content=open(Path(__file__).parent /"logical_judge_msg.txt").read().format(context1=person1["context"], context2=person2["context"], person1 = person1["name"], person2 = person2["name"]))
    tonal_judge_msg = SystemMessage(content=open(Path(__file__).parent /  "tonal_judge_msg.txt").read().format(context1=person1["context"], context2=person2["context"], person1 = person1["name"], person2 = person2["name"]))
    count_judge_msg = SystemMessage(content=open(Path(__file__).parent /  "count_judge_msg.txt").read())
    personal_attack_judge_msg = SystemMessage(content=open((Path(__file__).parent /  "personal_attack_judge_msg.txt")).read().format(context1=person1["context"], context2=person2["context"], person1 = person1["name"], person2 = person2["name"]))
    final_arbiter_msg = SystemMessage(
        content=open(Path(__file__).parent / "final_arbiter_msg.txt").read().format(
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


    
    parser = PydanticOutputParser(pydantic_object=ArgumentResult)
    def final_arbiter(state: MessagesState):
        response = llm.invoke([final_arbiter_msg] + state["messages"])
        try:
            # Extract JSON content from markdown code blocks if present
            content = response.content
            if "```" in content:
                # Find content between ```json and ``` markers
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
                content = json_match.group(1) if json_match else content
            
            json_response = json.loads(content.strip())
            complete_request = {
                "text": response.content,
                "party_one_name": person1["name"],
                "party_two_name": person2["name"],
                "context1": person1["context"],
                "context2": person2["context"],
                **json_response
            }
            parsed_response = parser.parse(json.dumps(complete_request))
            return {"messages": [AIMessage(content=parsed_response.model_dump_json())]}
        except Exception as e:
            print(f"Parsing error: {e}")
            print(f"Raw response: {response.content}")
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

### sample argument ###
maya = {
    "name":"Maya",
    "context":"my boyfriend doesn't appreciate my achievements - he only cares about his life."
}
arjun = {
    "name":"Arjun",
    "context":"I'm just so tired all the time - I don't know how to help"
}

### argument 1 ###
brandon = {
    "name":"Brandon",
    "context":"After pulling a third consecutive 14-hour day trying to secure a major client that could lead to his promotion, Brandon's mind was solely focused on work, running on nothing but coffee and stress while completely losing track of dates and time."
}
brenda = {
    "name":"Brenda",
    "context":"Having dropped hints about her birthday for weeks and even texted Brandon that morning about 'having something to celebrate tonight,' Brenda had spent all day at work watching other couples' birthday posts on social media while receiving zero acknowledgment from her boyfriend."
}

### argument 2 ###
campbell = {
    "name":"Campbell",
    "context":"Campbell had spent another day sending out unsuccessful job applications after being laid off six months ago, his third rejection email of the day still fresh in his mind as he mindlessly scrolled through social media, seeing photos of his former colleagues' successes."
}
sophie = {
    "name":"Sophie",
    "context":"Sophie had just finished a 12-hour workday preparing for a crucial presentation, her head still spinning with deadlines and the mounting pressure of trying to make partner by year's end, while also carrying the emotional weight of her younger sister's recent cancer diagnosis."
}


### argument 3 ###
jacob = {
    "name":"Jacob",
    "context":"Jacob had just returned from his morning walk, where he'd been thinking about his recent retirement and how different life felt without the structure of his 40-year teaching career. He'd been struggling more than he cared to admit with finding his new place in their daily routine."
}
laura = {
    "name":"Laura",
    "context":"Laura had spent the morning organizing old family photo albums, feeling nostalgic about the years gone by and slightly melancholic about how their quiet house used to be filled with children's laughter. The peace lily was a housewarming gift from their daughter Sarah when she moved out ten years ago."
}

#print(result(maya, arjun, open(Path(__file__).parent /"sample_argument.txt", "r", encoding="utf-8").read()))