from discord import Interaction
import securedb
from langchain.schema import (
  HumanMessage,
  BaseMessage,
  AIMessage
)
from typing import List
from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI 

# Discord-LangGraph agent helper class, adapted in part from CAMEL
class PlainGraphAgent:
  def __init__(
    self,
    interaction: Interaction,
    model: ChatOpenAI,
  ) -> None:
    self.username = interaction.user.global_name
    self.model = model
    self.init_messages()    
    
  def reset(self) -> None:
    self.init_messages()
    return

  def init_messages(self) -> None:
    self.stored_messages = []

  def update_messages(self, message: BaseMessage) -> List[BaseMessage]:
    self.stored_messages.append(message)
    return self.stored_messages

  def track_spending(self, total_cost: float) -> bool:
    return True

  async def ainvoke(self, message: HumanMessage) -> AIMessage: 
    output_message = AIMessage(content = "")
    try:
      with get_openai_callback() as cb:
        output_message = await self.model.ainvoke(message.content)
        self.track_spending(cb.total_cost)       
    except Exception as e:
      print(f"ainvoke() Exception occurred: {e}")
      output_message = AIMessage(content = "Agent flow complete (cause: ainvoke).")
    return output_message

  def invoke(self, message: HumanMessage) -> AIMessage: 
    output_message = BaseMessage(content = "")
    try:
      with get_openai_callback() as cb:
        output_message = self.model.invoke(message.content)
        print(f"output message from invoke(): {output_message}")
        self.track_spending(cb.total_cost)       
    except Exception as e:
      print(f"invoke() Exception occurred: {e}")
      output_message = AIMessage(content = "Agent flow complete (cause: invoke).")
    return output_message