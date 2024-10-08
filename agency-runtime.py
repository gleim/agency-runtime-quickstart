import os
import discord
import json
import requests 
from pathlib import Path
from sqlitedict import SqliteDict
from discord import app_commands
from web.server import keep_alive
from agentgarage import quickquick
from web3 import Web3

# main process
apikey = os.environ['OPENAI_API_KEY'],
guild_id = os.environ['AGENCY_GUILD_ID']
app_token = os.environ['AGENCYBOT_TOKEN']
infura_project_id = os.environ['INFURA_PROJECT_ID']
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


@tree.command(name="create_opo",
              description="create your Opo",
              guild=discord.Object(id=guild_id))
async def locker_box(ctx):
  # restrict messaging by channel
  if ctx.channel.name == 'mint-opo':
    await ctx.followup.send(
        "Create Opo agent at https://opopop.ai/"
    )


@tree.command(name="connect_opo",
              description="connect Opo",
              guild=discord.Object(id=guild_id))
async def connect_box(ctx, addr: str):
  # restrict messaging by channel
  if ctx.channel.name == 'mint-opo':
    await ctx.response.defer(ephemeral=True)
    db = SqliteDict("addr.sqlite", outer_stack=False)
    db[str(ctx.user.id)] = {"addr": addr}
    db.commit()
    db.close()

    await ctx.channel.send(
      "Opo connected! Use with /opo"
    )
    await ctx.followup.send(f"User: {ctx.user.id}, Adding locker address {addr}")


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


@tree.command(
    name="hello_opo",
    description="add a quick phrase, your Opo agents provide nifty responses",
    guild=discord.Object(id=guild_id))
async def nifty_box(ctx, phrase: str):
  # restrict messaging by channel
  if ctx.channel.name == 'mint-opo':
    await ctx.response.defer(ephemeral=True)
    
    # extract opo agent from JSON, call instigate_runtime_flow
    w3_provider = Web3.HTTPProvider(f"https://sepolia.infura.io/v3/{infura_project_id}")
    # AgencyInstance on Sepolia
    #agent_factory = '0x5FBB68B52B8017c5A56a5985d87Cb32cb5cb6538'
    #abi = Path('./contract/AgentFactory/abi.json').read_text()
    
    # OpoFactory on Sepolia
    agent_factory = '0xD800E7dEd2778d48B6653284d27Aa7ede7E962CE'
    abi = Path('./contract/OpoFactory/abi.json').read_text()
    
    w3 = Web3(w3_provider)   
    contract_instance = w3.eth.contract(address=agent_factory, abi=abi)

    # retrieve local copy of address for this Discord user
    db = SqliteDict("addr.sqlite", outer_stack=False)
    addr_dict = db[str(ctx.user.id)] 
    db.close()

    user_address = Web3.to_checksum_address(addr_dict['addr'])
    print(f"User address: {user_address}")
    
    # Get the balance (number of tokens owned by the address)
    balance = contract_instance.functions.balanceOf(user_address).call()
    print(f"Token balance: {balance}")

    if balance > 0:
        # Get the token ID of the first token owned by the address
        token_id = contract_instance.functions.tokenOfOwnerByIndex(user_address, 0).call()
        print(f"Token ID: {token_id}")

        # Retrieve the URI for the owned token
        tokenURI = contract_instance.functions.tokenURI(token_id).call()
        print(f"Token URI: {tokenURI}")
    else:
        print("User doesn't own any tokens")
        tokenURI = None

    if tokenURI.startswith('http'):
      opo_json = json.loads(requests.get(tokenURI).text)
      print("Response: ", opo_json)

      opo_json = json.dumps(opo_json)
    else:
      # Remove surrounding double quotes
      if tokenURI.startswith('"') and tokenURI.endswith('"'):
        tokenURI = tokenURI[1:-1]

        try:
            # Parse the JSON string
            data = json.loads(tokenURI)

            # Extract the opo field
            opo_field = data['opo']

            # Convert the opo field back to a JSON string
            opo_json = json.dumps(opo_field[0], indent=2)

        except json.JSONDecodeError as e:
          print(f"Error decoding JSON: {e}")
        except KeyError as e:
          print(f"Key error: {e}")

    print(opo_json)

    await quickquick.instigate_runtime_flow(ctx, opo_json, phrase)
    
  #f"Initiating your opo agents with \n**\nUser-Specified Input\n**\n{phrase}"
  #await quickquick.instigate_agent_flow(ctx, phrase)
  else:
    await ctx.channel.send("Try the *opo* command on #opo-agents!")


# Start agent server
keep_alive()
client.run(app_token)
