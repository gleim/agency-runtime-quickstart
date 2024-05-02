import json
from typing import TypedDict, Annotated, Sequence, operator
from langgraph.pregel import GraphRecursionError
from langchain_openai import ChatOpenAI 
from langchain.schema import (
  HumanMessage,
  BaseMessage,
)
from langgraph.graph import StateGraph

from core.agent import PlainGraphAgent

class AgentState(TypedDict):
  messages: Annotated[Sequence[BaseMessage], operator.add]

# explicit import for string invocation
langgraph = __import__('langgraph')

agents = []

agent_team_json = """{
    "team-id": "quickquick",
    "nodes": [
        {
            "name": "**Task Inception**",
            "index": 0,
            "prompt": "This is your role assignment: take a brief phrase from a user and incept an achievable, detailed variant as a task specification. Make the task achievable within four hundred words. Do not let your response exceed five hundred characters. The brief phrase from the user is: {}"
        },
        {
            "name": "**Task Guidance**",
            "index": 1,
            "prompt": "This is your role assignment: take a specified task and accomplish it. You may break the specified task into sub-parts for reasoning and planning purposes. Never repeat text. Your sole responsibility is to provide task completion in less than fifteen hundred characters.  The specified task is {}"
        },
        {
            "name": "**Guidance Assessment**",
            "index": 2,
            "prompt": "This is your role assignment: receive a task completion proposal and compare it against the original task request for acceptance test evaluation. Provide the criteria and reasoning during the evaluation process. If and only if the task is correctly and completely addressed by the task completion proposal, end the explanation with the keyword DELIVERED. Do not repeat text. If given a numbered list, do not ever provide a numbered list in response. Your sole responsibility is to evaluate the task completion proposal {}. The original task request is {}. If the proposal does not satisfy the request, explain how the proposal is insufficient and must be modified. Do not let the response exceed fifteen hundred characters."
        }
    ],
    "edges": [
        {
            "from": "**Task Inception**",
            "to": "**Task Guidance**"
        },
        {
            "from": "**Task Guidance**",
            "to": "**Guidance Assessment**"
        }
    ],
    "conditional-edges": [
        {
            "from": "**Guidance Assessment**",
            "conditional": "should_end",
            "true": "END",
            "false": "**Task Inception**"
        }
    ],
    "halt-set": [
        "DELIVERED"
    ]
}"""

# Define the set of agents
def initialize_agents(interaction):
  for index in range(len(agent_team['nodes'])):
    agent = PlainGraphAgent(
      interaction,
      ChatOpenAI(
        temperature=0.6,
      )
    )
    agent.reset()
    # add to global agent set
    agents.append(agent)

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

# Universal action graph with graph structure constraints
async def action_step(state):
  # graph starts with single message in history and index zero
  index = (len(state['messages'])-1) % len(agent_team['nodes'])  
  
  # set graph variables that are dependent on graph index
  name = agent_team['nodes'][index]['name']
  prompt = agent_team['nodes'][index]['prompt']
  agent = agents[index]
  
  # initialize formatted prompt without formatting
  formatted_prompt = prompt
  
  try:
    # configure prompt dependent on previous message
    if (prompt.count("{}")==1):
      message = state['messages'][-1]
      formatted_prompt = prompt.format(message.content)
    # configure prompt dependent on previous two messages
    elif (prompt.count("{}")==2):
      task_guidance = state['messages'][-1]
      task_specification = state['messages'][-2]
      formatted_prompt = prompt.format(task_guidance.content, task_specification.content)
  except IndexError as e:
    # invalid Agent specification
    print(f"Invalid index: {e}")
  finally:
    response = await agent.ainvoke(HumanMessage(content=formatted_prompt))
    await channel.send(f"\n{name}\n{response.content[0:1970]}\n")
    response_msg = HumanMessage(content=response.content)
    return {"messages": [response_msg]}

# Define the operational flow of the agent graph
def define_graph():  
  # define workflow as state graph with stored agent state
  workflow = StateGraph(AgentState)

  # define the start node of the graph
  workflow.set_entry_point(agent_team['nodes'][0]['name'])
  
  # define the actions of graph
  for node in agent_team['nodes']:
    workflow.add_node(node['name'], action_step)    

  # define the transition functions of graph
  for edge in agent_team['edges']:
    workflow.add_edge(edge['from'], edge['to'])

  for edge in agent_team['conditional-edges']:
    workflow.add_conditional_edges(
      edge['from'],
      globals()[edge['conditional']],
      {
        "false": edge['false'],
        "true": getattr(langgraph.graph, edge['true'])
      }
    )
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
    runnable = define_graph()

    # initialize active graph components
    initialize_agents(interaction)

    try:
      await runnable.ainvoke({"messages": [HumanMessage(content=input)], "original_task": input})  
    except GraphRecursionError as e:
      print(f"exception {e}")

  except json.JSONDecodeError:
    # invalid Agent specification
    print("Invalid Agent specification [JSON]")
    await channel.send("Invalid Agent specification [JSON]")