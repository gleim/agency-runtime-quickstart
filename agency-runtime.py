import os
import discord
from discord import app_commands
from web.server import keep_alive
from agentgarage import quickquick

# main process
apikey = os.environ['OPENAI_API_KEY'] ,
guild_id = os.environ['AGENCY_GUILD_ID']
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents = intents)
tree = app_commands.CommandTree(client)

# Discord decorators
@client.event
async def on_ready():
  await tree.sync(guild=discord.Object(id=guild_id))
  print("Agent is operational.")
  print(client.user)
    
@tree.command(
  name="quickquick",
  description="enter a quick phrase for a quick team response",
  guild=discord.Object(id=guild_id)
)
async def quicki_box(ctx, input:str):
  # restrict messaging by channel
  if ctx.channel.name == 'agent-teams':
    await ctx.response.send_message(f"Starting quick response team with \n**\nUser-Specified Input\n**\n{input}")
    await quickquick.instigate_agent_flow(ctx, input)
  else:
    await ctx.response.send_message("Try the *quickquick* command on #agent-teams!")

@tree.command(
  name="agency-run",
  description="make a team for a quick response",
  guild=discord.Object(id=guild_id)
)
async def runtime_box(ctx, json:str, input:str):
  # restrict messaging by channel
  if ctx.channel.name == 'agent-teams':
    await ctx.response.send_message(f"Starting custom JSON team for \n**\nUser-Specified Agent Input\n**\n{input}")
    await quickquick.instigate_runtime_flow(ctx, json, input)
  else:
    await ctx.response.send_message("Set up your agents with *agency-run* on #agent-teams!")

# Spin up server
keep_alive()
my_secret = os.environ['AGENCYBOT_SECRET']
client.run(my_secret)
