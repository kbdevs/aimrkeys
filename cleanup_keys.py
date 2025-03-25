import json
import time
import discord
import os
from discord.ext import commands

# Load the keys.json file
with open("keys.json", "r") as f:
    data = json.load(f)

# Get the current Unix time
current_time = int(time.time())

# Remove expired keys, but keep frozen keys
keys_to_remove = []
expired_user_ids = []

for key, value in data.items():
    expiry = value.get("expiry")
    
    # Skip frozen keys
    if key.startswith("frozen-"):
        continue

    # Remove expired keys
    if expiry and expiry < current_time:
        keys_to_remove.append(key)
        # Store user ID if it exists
        if 'id' in value:
            expired_user_ids.append(value['id'])

# Remove expired keys
for key in keys_to_remove:
    del data[key]

# Save the updated keys.json
with open("keys.json", "w") as f:
    json.dump(data, f, indent=4)

print(f"Removed {len(keys_to_remove)} expired keys.")

# Discord bot setup
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    guild = discord.utils.get(bot.guilds)
    
    if guild:
        for user_id in expired_user_ids:
            try:
                member = guild.get_member(int(user_id))
                if member:
                    roles_to_remove = [role for role in member.roles if 'customer' in role.name.lower()]
                    for role in roles_to_remove:
                        await member.remove_roles(role)
                        print(f'Removed role {role.name} from user {member.name}')
            except Exception as e:
                print(f"Error removing roles from user {user_id}: {str(e)}")
    
    # Close the bot after removing roles
    await bot.close()

# Get token from environment variable
discord_token = os.environ('DISCORD_BOT_TOKEN')
if not discord_token:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is not set")

# Run the bot with token from environment
bot.run(discord_token)
