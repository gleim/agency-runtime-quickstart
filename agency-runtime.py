import os
import discord
from discord import app_commands
from web.server import keep_alive
from agentgarage import quickquick

# main process
apikey = os.environ['OPENAI_API_KEY'],
guild_id = os.environ['AGENCY_GUILD_ID']
app_token = os.environ['AGENCYBOT_TOKEN']
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# Discord decorators
@client.event
async def on_ready():
  await tree.sync(guild=discord.Object(id=guild_id))
  print("Agent is operational.")
  print(client.user)


@tree.command(name="quickquick",
              description="enter a quick phrase for a quick team response",
              guild=discord.Object(id=guild_id))
async def quicki_box(ctx, phrase: str):
  # restrict messaging by channel
  if ctx.channel.name == 'subscription-agents':
    await ctx.response.send_message(
        f"Starting quick response team with \n**\nUser-Specified Input\n**\n{phrase}"
    )
    await quickquick.instigate_agent_flow(ctx, phrase)
  else:
    await ctx.response.send_message(
        "Try the *quickquick* command on #subscription-agents!")


@tree.command(name="quickteam",
              description="interact with your own custom agent team (JSON)",
              guild=discord.Object(id=guild_id))
async def json_box(ctx, phrase: str, team_json: str):
  # restrict messaging by channel
  if ctx.channel.name == 'subscription-agents':
    await ctx.response.send_message(
        f"Starting custom JSON team for \n**\nUser-Specified Agent Input\n**\n{phrase}"
    )
    await quickquick.instigate_runtime_flow(ctx, team_json, phrase)
  else:
    await ctx.response.send_message(
        "Start your agent team with *quickteam* on #subscription-agents!")


# Start agent server
keep_alive()
client.run(app_token)
