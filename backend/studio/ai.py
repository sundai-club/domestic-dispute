from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode

# Define LLM with bound tools
llm = ChatOpenAI(model="gpt-4o")
# llm_with_tools = llm.bind_tools(tools)

# System messages
distributor_msg = SystemMessage(content="You are the distributor of messages. You distribute messages to the logical judge, tonal judge, count judge, and personal attack judge.")
logical_judge_msg = SystemMessage(content="You are the logical judge. You judge the logical correctness of the message.")
tonal_judge_msg = SystemMessage(content="You are the tonal judge. You judge the tonal correctness of the message.")
count_judge_msg = SystemMessage(content="You are the count judge. You judge the count of the message.")
personal_attack_judge_msg = SystemMessage(content="You are the personal attack judge. You judge the personal attack of the message.")
final_arbiter_msg = SystemMessage(content="You are the final arbiter. You combine the outputs (scores) from the logical judge, tonal judge, count judge, and personal attack judge and you decide who won the argument.")

# Node
def distributor(state: MessagesState):
   return {"messages": [llm.invoke([distributor_msg] + state["messages"])]}

# Node
def logical_judge(state: MessagesState):
   return {"messages": [llm.invoke([logical_judge_msg] + state["messages"])]}

# Node
def tonal_judge(state: MessagesState):
    return {"messages": [llm.invoke([tonal_judge_msg] + state["messages"])]}

# Node
def count_judge(state: MessagesState):
    return {"messages": [llm.invoke([count_judge_msg] + state["messages"])]}

# Node
def personal_attack_judge(state: MessagesState):
    return {"messages": [llm.invoke([personal_attack_judge_msg] + state["messages"])]}

# Node
def final_arbiter(state: MessagesState):
    return {"messages": [llm.invoke([final_arbiter_msg] + state["messages"])]}

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

# Compile graph
graph = builder.compile()
