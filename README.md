# agency-runtime-quickstart
Quickstart for self-hosting and customizing agent teams on the 
Agency Runtime OSS stack.

# Replit hosting configuration
These are the instructions for using the Replit component of
the Agency Runtime stack for agent team deployment.

## Add OpenAI Key
If self-hosting custom agent teams utilizing OpenAI,
add your OpenAI API key as a Secret named OPENAI_API_KEY.

## Create DB Key
If self-hosting and tracking per-user spending, create a
database key local to your hosting environment with the
following step.

In the replit Shell:

'import securedb'
'securedb.newkey(keyfile="/usage/.key")'

This will enable tracking of per-user spend for deployed
agent teams interactions.

## Set Discord Guild Identifier
Add the Discord Guild ID as a Secret named GUILD_ID.

## Set Discord Bot Secret
Add the Discord bot token as a Secret named AGENCYBOT_SECRET.

