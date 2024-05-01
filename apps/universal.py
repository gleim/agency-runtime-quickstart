import json
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

agent_team_json = """{
    "team-id": "quickquick",
    "nodes": [
        {
            "name": "inceptor",
            "prompt": "This is your role assignment: take a brief phrase from a user and incept an achievable, detailed variant as a task specification. Make the task achievable within four hundred words. Do not let your response exceed five hundred characters. The brief phrase from the user is: {}"
        },
        {
            "name": "responder",
            "prompt": "This is your role assignment: take a specified task and accomplish it. You may break the specified task into sub-parts for reasoning and planning purposes. Never repeat text. Your sole responsibility is to provide task completion in less than fifteen hundred characters.  The specified task is {}"
        },
        {
            "name": "assessor",
            "prompt": "This is your role assignment: receive a task completion proposal and compare it against the original task request for acceptance test evaluation. Provide the criteria and reasoning during the evaluation process. If and only if the task is correctly and completely addressed by the task completion proposal, end the explanation with the keyword DELIVERED. Do not repeat text. If given a numbered list, do not ever provide a numbered list in response. Your sole responsibility is to evaluate the task completion proposal {}. The original task request is {}. If the proposal does not satisfy the request, explain how the proposal is insufficient and must be modified. Do not let the response exceed fifteen hundred characters."
        }
    ],
    "edges": [
        {
            "from": "inceptor",
            "to": "responder"
        },
        {
            "from": "responder",
            "to": "assessor"
        }
    ],
    "conditional-edges": {
        "from": "assessor",
        "conditional": "should_end",
        "true": "END",
        "false": "inceptor"
    },
    "halt-set": [
        "DELIVERED"
    ]
}"""
  
# Define the role names
inceptor_agent_name = "**\nTask Inception\n**\n"
retriever_agent_name = "**\nTask Guidance\n**\n"
responder_agent_name = "**\nGuidance Assessment\n**\n"

# Define the prompts
inceptor_prompt = (
  """This is your role assignment: take a brief phrase from a user and incept an achievable, detailed variant as a task specification. Make the task achievable within four hundred words. Do not let your response exceed five hundred characters. The brief phrase from the user is: {}"""
)

retrieval_prompt = """This is your role assignment: take a specified task and accomplish it. You may break the specified task into sub-parts for reasoning and planning purposes. Never repeat text. Your sole responsibility is to provide task completion in less than fifteen hundred characters.  The specified task is {}."""

response_prompt = """This is your role assignment: receive a task completion proposal and compare it against the original task request for acceptance test evaluation. Provide the criteria and reasoning during the evaluation process. If and only if the task is correctly and completely addressed by the task completion proposal, end the explanation with the keyword DELIVERED. Do not repeat text. If given a numbered list, do not ever provide a numbered list in response. Your sole responsibility is to evaluate the task completion proposal {}. The original task request is {}. If the proposal does not satisfy the request, explain how the proposal is insufficient and must be modified. Do not let the response exceed fifteen hundred characters."""

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
  if any(halt_str in content for halt_str in agent_team['halt-set']):
    return "true"
  # default flow continuation case
  else:
    return "false"

# Define the agent step method
async def inception_step(state):
  response = await inceptor_agent.ainvoke(HumanMessage(content=inceptor_prompt.format(state['messages'][-1].content)))
  await channel.send(f"{inceptor_agent_name}{response.content[0:1970]}")
  response_msg = HumanMessage(content=response.content)
  return {"messages": [response_msg]}

# Define the agent step method
async def retrieval_step(state):
  response = await retriever_agent.ainvoke(HumanMessage(content=retrieval_prompt.format(state['messages'][-1].content)))
  await channel.send(f"{retriever_agent_name}{response.content[0:1970]}")
  response_msg = HumanMessage(content=response.content)
  return {"messages": [response_msg]}

# Define the agent step method
async def response_step(state):
  response = await responder_agent.ainvoke(HumanMessage(content=response_prompt.format(state['messages'][-1].content, state['messages'][-2].content)))
  
  await channel.send(f"{responder_agent_name}{response.content[0:1970]}")
  response_msg = HumanMessage(content=response.content)
  return {"messages": [response_msg]}

# Define the operational flow of the agent graph
def define_graph(agent_team):
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
      "false": "inceptor",
      "true": END
    }
  )
  workflow.set_entry_point("inceptor")
  runnable = workflow.compile()
  return runnable
  
# Start the operational flow of the agent graph
async def instigate_agent_flow(interaction, input):
  # define the communication channel for this interaction
  global channel
  channel = interaction.channel

  global agent_team
  try:
    agent_team = json.loads(agent_team_json)

    # define the graph action states and conditional logic
    runnable = define_graph(agent_team)

    # initialize active graph components
    initialize_agents(interaction)

    try:
      await runnable.ainvoke({"messages": [HumanMessage(content=input)], "original_task": input})  
    except GraphRecursionError as e:
      print(f"exception {e}")

  except json.JSONDecodeError:
    # invalid Agent specification
    print("Invalid Agent specification [JSON]")
    channel.send("Invalid Agent specification [JSON]")

