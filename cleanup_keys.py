import json
import os
import time
import datetime
import discord
from discord.ext import commands

# --- Configuration ---
KEYS_FILE = "keys.json"
# Add your category IDs for ticket channels here
CATEGORY_IDS = [
    # paid
    1252171060736954369, 1294741916784525342, 1304823897727701104,
    # paid support
    1201336360536121394,
    # regular
    1191468195710763080, 1294742646681768017
]

# --- Helper Functions for JSON ---
def load_keys():
    """Loads key data from the JSON file."""
    if not os.path.exists(KEYS_FILE):
        return {}
    with open(KEYS_FILE, "r") as f:
        return json.load(f)

def save_keys(data):
    """Saves key data to the JSON file."""
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Core Functionality ---

async def remove_inactive_tickets(bot):
    """
    Scans specified categories for inactive ticket channels and deletes them.
    - Deletes channels with "paid-" prefix after 1 day of inactivity.
    - Deletes other specified ticket channels after 3 days of inactivity.
    """
    print("\nStarting scan for inactive ticket channels...")
    now = datetime.datetime.now(datetime.timezone.utc)
    three_days_ago = now - datetime.timedelta(days=3)
    one_day_ago = now - datetime.timedelta(days=1)
    
    deleted_count = 0
    for guild in bot.guilds:
        for category in guild.categories:
            if category.id in CATEGORY_IDS:
                print(f"Scanning category: {category.name}")
                
                for channel in category.text_channels:
                    # Check if the channel name matches ticket prefixes
                    if (channel.name.startswith(("ticket-", "coin-", "media-", "cs2_skins-",
                                                  "card-", "pp-", "something_else-", "cashapp-",
                                                  "paysafe-", "apple-", "lifetime-", "paid-",
                                                  "aimr_video-", "custom-"))):
                        try:
                            last_message = await channel.fetch_message(channel.last_message_id) if channel.last_message_id else None
                        
                            if not last_message:
                                print(f" - Deleting channel '{channel.name}' (no messages found).")
                                await channel.delete(reason="Channel was empty.")
                                deleted_count += 1
                                continue

                            # Determine inactivity threshold
                            threshold = one_day_ago if channel.name.startswith("paid-") else three_days_ago
                            
                            if last_message.created_at < threshold:
                                print(f" - Deleting inactive channel '{channel.name}'. Last message: {last_message.created_at.strftime('%Y-%m-%d')}")
                                await channel.delete(reason=f"No activity since {last_message.created_at.strftime('%Y-%m-%d')}")
                                deleted_count += 1

                        except discord.errors.NotFound:
                            print(f" - Deleting channel '{channel.name}' (last message not found, likely deleted).")
                            await channel.delete(reason="Orphaned channel.")
                            deleted_count += 1
                        except Exception as e:
                            print(f"Error processing channel {channel.name}: {e}")
    print(f"Finished scanning. Deleted {deleted_count} inactive channels.")


# 1) Pre-Bot: Load and remove truly expired keys
print("Processing expired keys...")
data = load_keys()
current_time = int(time.time())
expired_ids = []
keys_to_delete = []

for key, value in data.items():
    if key.startswith("frozen-"):
        continue

    expiry_time = value.get("expiry")
    if expiry_time and expiry_time < current_time:
        expired_ids.append(value.get("id"))
        keys_to_delete.append(key)

for k in keys_to_delete:
    del data[k]

save_keys(data)
print(f"Removed {len(keys_to_delete)} expired keys.")

# 2) Set up the bot with combined intents
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True # Needed to check channel history

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """
    Runs once the bot is logged in and ready.
    """
    print(f'\nLogged in as {bot.user.name}')
    guild = bot.guilds[0] # Assumes the bot is in only one server

    # 3) Freeze keys for users who have left the server
    print("\nChecking for members who have left...")
    data = load_keys() # Reload data to include any concurrent modifications
    current_time = int(time.time())
    frozen_count = 0

    for orig_key in list(data.keys()):
        if orig_key.startswith("frozen-"):
            continue

        entry = data[orig_key]
        user_id = entry.get("id")
        if not user_id:
            continue

        member = guild.get_member(int(user_id))
        if member is None:
            expiry_time = entry.get("expiry", current_time)
            remaining_seconds = max(0, expiry_time - current_time)
            new_key = f"frozen-{remaining_seconds};{orig_key}"
            
            data[new_key] = entry
            del data[orig_key]

            print(f"Froze key '{orig_key}' for user {user_id} (left server).")
            frozen_count += 1
    
    save_keys(data)
    print(f"Froze {frozen_count} keys for missing members.")

    # 4) Remove roles from users with expired keys
    print("\nRemoving roles from users with expired keys...")
    removed_roles_count = 0
    for user_id in expired_ids:
        member = guild.get_member(int(user_id))
        if member:
            roles_to_remove = [r for r in member.roles if 'customer' in r.name.lower()]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="License key expired")
                print(f"Removed roles: {[r.name for r in roles_to_remove]} from {member.display_name}")
                removed_roles_count += 1
    print(f"Removed roles from {removed_roles_count} members.")

    # 5) Remove inactive ticket channels
    await remove_inactive_tickets(bot)

    # 6) Shutdown
    print("\nAll tasks complete. Shutting down.")
    await bot.close()

# Run the bot
# Make sure to set the DISCORD_BOT_TOKEN environment variable
bot_token = os.getenv("DISCORD_BOT_TOKEN")
if not bot_token:
    print("Error: DISCORD_BOT_TOKEN environment variable not set.")
else:
    bot.run(bot_token)
