import json
import os
import time
import discord
from discord.ext import commands

KEYS_FILE = "keys.json"

def load_keys():
    with open(KEYS_FILE, "r") as f:
        return json.load(f)

def save_keys(data):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# 1) Load and remove truly expired keys (but leave already‐frozen ones alone)
data = load_keys()
current_time = int(time.time())

expired_ids = []
to_delete = []

for key, value in data.items():
    # skip anything already frozen
    if key.startswith("frozen-"):
        continue

    exp = value.get("expiry")
    if exp and exp < current_time:
        expired_ids.append(value.get("id"))
        to_delete.append(key)

for k in to_delete:
    del data[k]

save_keys(data)
print(f"Removed {len(to_delete)} expired keys.")

# 2) Set up the bot
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    guild = bot.guilds[0]  # assumes a single-guild bot

    # Load fresh data so any concurrent modifications get included
    data = load_keys()
    current_time = int(time.time())
    frozen_count = 0

    # Iterate over a static list of keys to avoid runtime-dict changes
    for orig_key in list(data.keys()):
        if orig_key.startswith("frozen-"):
            continue

        entry = data[orig_key]
        user_id = entry.get("id")
        if not user_id:
            continue

        # Check membership
        member = guild.get_member(int(user_id))
        if member is None:
            # calculate remaining seconds until expiry (or 0 if no expiry)
            exp = entry.get("expiry", current_time)
            remaining = max(0, exp - current_time)

            # build the new frozen key name
            new_key = f"frozen-{remaining};{orig_key}"

            # carry over the entire entry
            data[new_key] = entry
            del data[orig_key]

            print(f"Froze key {orig_key} for user {user_id} (remaining {remaining}s).")
            frozen_count += 1

    # Save after freezing
    save_keys(data)
    print(f"Froze {frozen_count} keys for missing members.")

    # 3) Now remove roles from users whose keys actually expired
    for user_id in expired_ids:
        member = guild.get_member(int(user_id))
        if member:
            roles_to_remove = [r for r in member.roles if 'customer' in r.name.lower()]
            for role in roles_to_remove:
                await member.remove_roles(role)
                print(f"Removed role {role.name} from {member}.")

    await bot.close()

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
