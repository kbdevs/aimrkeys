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
id_array = []

for key, value in data.items():
    expiry = value.get("expiry")
    user_id = value.get("id")
    
    # Skip frozen keys
    if key.startswith("frozen-"):
        continue

    # Remove expired keys and save IDs
    if expiry and expiry < current_time:
        keys_to_remove.append(key)
        if user_id:
            id_array.append(user_id)

# Remove expired keys
for key in keys_to_remove:
    del data[key]

# Save the updated keys.json
with open("keys.json", "w") as f:
    json.dump(data, f, indent=4)

print(f"Removed {len(keys_to_remove)} expired keys.")

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event 
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    guild = discord.utils.get(bot.guilds)

    for user_id in id_array:
        member = guild.get_member(int(user_id))
        if member:
            roles_to_remove = [role for role in member.roles if 'customer' in role.name.lower()]
            for role in roles_to_remove:
                await member.remove_roles(role)
                print(f'Removed role {role.name} from user {member.name}')

    await bot.close()

bot.run(os.getenv("DISCORD_BOT_TOKEN"))