import json
import time

# Load the keys.json file
with open("keys.json", "r") as f:
    data = json.load(f)

# Get the current Unix time
current_time = int(time.time())

# Remove expired keys, but keep frozen keys
keys_to_remove = []

for key, value in data.items():
    expiry = value.get("expiry")
    
    # Skip frozen keys
    if key.startswith("frozen-"):
        continue

    # Remove expired keys
    if expiry and expiry < current_time:
        keys_to_remove.append(key)

# Remove expired keys
for key in keys_to_remove:
    del data[key]

# Save the updated keys.json
with open("keys.json", "w") as f:
    json.dump(data, f, indent=4)

print(f"Removed {len(keys_to_remove)} expired keys.")
