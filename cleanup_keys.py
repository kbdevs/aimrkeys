import json
import os
import time
import discord
from discord.ext import commands

# Load the keys.json file
with open("keys.json", "r") as f:
    data = json.load(f)

# Get the current Unix time
current_time = int(time.time())

# Remove expired keys, but keep frozen keys
keys_to_remove = []
expired_ids = []

for key, value in data.items():
    expiry = value.get("expiry")
    
    # Skip frozen keys
    if key.startswith("frozen-"):
        continue

    # Remove expired keys
    if expiry and expiry < current_time:
        expired_ids.append(value.get("id"))
        keys_to_remove.append(key)

# Remove expired keys
for key in keys_to_remove:
    del data[key]

# Save the updated keys.json
with open("keys.json", "w") as f:
    json.dump(data, f, indent=4)

print(f"Removed {len(keys_to_remove)} expired keys.")

# Rest of the Discord bot code remains the same
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    guild = discord.utils.get(bot.guilds)

    for user_id in expired_ids:
        member = guild.get_member(int(user_id))
        if member:
            roles_to_remove = [role for role in member.roles if 'customer' in role.name.lower()]
            for role in roles_to_remove:
                await member.remove_roles(role)
                print(f'Removed role {role.name} from user {member.name}')

    await bot.close()

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
