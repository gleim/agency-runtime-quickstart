from typing import TypedDict, Annotated, Sequence, operator
from langgraph.pregel import GraphRecursionError
from langchain_openai import ChatOpenAI 
from langchain.schema import (
  HumanMessage,
  BaseMessage,
)
from langgraph.graph import StateGraph, END

from core.agent import PlainGraphAgent

class AgentState(TypedDict):
  messages: Annotated[Sequence[BaseMessage], operator.add]

# Define the role names
inceptor_agent_name = "**\nTask Inception\n**\n"
retriever_agent_name = "**\nTask Guidance\n**\n"
responder_agent_name = "**\nGuidance Assessment\n**\n"

# Define the set of agents
def initialize_agents(interaction):
  global inceptor_agent
  inceptor_agent = PlainGraphAgent(
    interaction,
    ChatOpenAI(
      temperature=0.6,
    )
  )
  inceptor_agent.reset()

  global retriever_agent
  retriever_agent = PlainGraphAgent(
    interaction,
    ChatOpenAI(
      temperature=0.6,
    )
  )
  retriever_agent.reset()

  global responder_agent
  responder_agent = PlainGraphAgent(
    interaction,
    ChatOpenAI(
      temperature=0.6,
    )
  )
  responder_agent.reset()


# Define conditional edge function 
def should_end(state):
  messages = state['messages']
  # get content of last message
  message = messages[-1]
  content = message.content
  
  # flow halting case
  if any(halting_phrase in content for halting_phrase in ["<end keyphrase>"]):
    return "end"
  # default flow continuation case
  else:
    return "continue"

# Define the agent step method
async def inception_step(state):
  messages = state['messages']
  # get content of last message
  message = messages[-1]
  content = message.content
  
  inceptor_prompt = (
    f"""This is your role assignment: <inception prompt> The brief phrase from the user is: {content}"""
  )
  
  response = await inceptor_agent.ainvoke(HumanMessage(content=inceptor_prompt))
  await channel.send(f"{inceptor_agent_name}{response.content[0:1970]}")
  response_msg = HumanMessage(content=response.content)
  return {"messages": [response_msg], "incepted_task": response.content}

# Define the agent step method
async def retrieval_step(state):
  messages = state['messages']
  # get content of last message
  message = messages[-1]
  content = message.content
  
  retrieval_prompt = f"""This is your role assignment: <retrieval prompt> The specified task is {content}."""
  
  response = await retriever_agent.ainvoke(HumanMessage(content=retrieval_prompt))
  await channel.send(f"{retriever_agent_name}{response.content[0:1970]}")
  response_msg = HumanMessage(content=response.content)
  return {"messages": [response_msg]}

# Define the agent step method
async def response_step(state):
  messages = state['messages']
  # get content of last message
  message = messages[-1]
  content = message.content

  response_prompt = f"""This is your role assignment: <response prompt> Evaluate the task guidance {content}."""

  response = await responder_agent.ainvoke(HumanMessage(content=response_prompt))
  await channel.send(f"{responder_agent_name}{response.content[0:1970]}")
  response_msg = HumanMessage(content=response.content)
  return {"messages": [response_msg]}

# Define the operational flow of the agent graph
def define_graph():
  # define workflow as state graph with stored agent state
  workflow = StateGraph(AgentState)
  # define the actions and transition functions of graph
  workflow.add_node("inceptor", inception_step)
  workflow.add_node("retriever", retrieval_step)
  workflow.add_node("responder", response_step)
  workflow.add_edge("inceptor", "retriever")
  workflow.add_edge("retriever", "responder")
  workflow.add_conditional_edges(
    "responder",
    # next state decision (transition function)
    should_end,
    {
      "continue": "inceptor",
      "end": END
    }
  )
  workflow.set_entry_point("inceptor")
  runnable = workflow.compile()
  return runnable
  
# Start the operational flow of the agent graph
async def instigate_agent_flow(interaction, input):
  # define the graph action states and conditional logic
  runnable = define_graph()

  # define the communication channel for this interaction
  global channel
  channel = interaction.channel

  # initialize active graph components
  initialize_agents(interaction)

  try:
    await runnable.ainvoke({"messages": [HumanMessage(content=input)], "original_task": input})  
  except GraphRecursionError as e:
    print(f"exception {e}")
