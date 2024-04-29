# agentgarage-quickstart
Quickstart for creating agent teams in the Agent Garage stack

# Replit hosting configuration
These are the instructions for using the Replit component of
the Agent Garage stack for agent team deployment.

## Add OpenAI Key
If utilizing the OpenAI component of the Agent Garage
stack (default case), add your OpenAI API key as a Secret 
named OPENAI_API_KEY.

## Create DB Key
In the replit Shell:

'import securedb'
'securedb.newkey(keyfile="/usage/.key")'

This will enable tracking of per-user spend 
(model usage) for any agents or agent teams 
that are deployed.

## Set Discord Guild Identifier
Add the Discord Guild ID as a Secret named GUILD_ID.

## Set Discord Bot Secret
Add the Discord bot token as a Secret named AGENTBOT_SECRET.

