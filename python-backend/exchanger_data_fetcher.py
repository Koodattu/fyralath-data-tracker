import requests
import struct

MS_SEC = 1000
MS_MINUTE = 60 * MS_SEC
MS_HOUR = 60 * MS_MINUTE
MS_DAY = 24 * MS_HOUR
COPPER_SILVER = 100

def read_data(view, offset, fmt):
    size = struct.calcsize(fmt)
    result = struct.unpack_from(fmt, view, offset)
    return result[0], offset + size

def skip_data(buffer, offset, bytes):
    num_entries, offset = read_data(buffer, offset, "H")
    offset += num_entries * bytes
    return offset

def get_item_state(realm_id, item_id):
    mask = item_id & 0xFF
    url = f"https://undermine.exchange/data/cached/{realm_id}/{mask}/{item_id}.bin"
    response = requests.get(url)
    buffer = response.content

    offset = 0
    _, offset = read_data(buffer, offset, "B")
    daily_history = True

    _, offset = read_data(buffer, offset, "I")
    _, offset = read_data(buffer, offset, "I")
    _, offset = read_data(buffer, offset, "I")

    offset = skip_data(buffer, offset, 8)
    offset = skip_data(buffer, offset, 4)
    offset = skip_data(buffer, offset, 12)

    result = {
        "realm": realm_id,
        "item": item_id,
        "daily": []
    }

    if daily_history:
        daily_count, offset = read_data(buffer, offset, "H")
        for _ in range(daily_count):
            snapshot, offset = read_data(buffer, offset, "H")
            snapshot *= MS_DAY
            price, offset = read_data(buffer, offset, "I")
            price *= COPPER_SILVER
            quantity, offset = read_data(buffer, offset, "I")
            day_state = {"snapshot": snapshot, "price": price, "quantity": quantity}
            if result["daily"]:
                prev_seen = result["daily"][-1]
                lost_day = prev_seen["snapshot"] + MS_DAY
                while lost_day < day_state["snapshot"]:
                    result["daily"].append({"snapshot": lost_day, "price": prev_seen["price"], "quantity": 0})
                    lost_day += MS_DAY
            result["daily"].append(day_state)

    return result

import json

# Assuming get_item_state and other necessary functions are defined above

def collect_item_data(items_details):
    realms = {
        "us": 32512,
        "eu": 32513,
        "tw": 32514,
        "kr": 32515
    }
    
    data = {realm: [] for realm in realms}

    for realm_name, realm_id in realms.items():
        for item in items_details["items"]:
            item_state = get_item_state(realm_id, item["id"])
            if "daily" in item_state:
                # Organizing data under each realm with name, id, and snapshots
                data[realm_name].append({
                    "name": item["name"],
                    "id": item["id"],
                    "snapshots": [
                        {"timestamp": entry["snapshot"], "price": entry["price"]}
                        for entry in item_state["daily"]
                    ]
                })

    return data

def save_to_json(data, filename="item_data.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

items_details = {
    "items": [
        {"name": "Shadowflame Essence", "id": 204464, "price": 5, "amount_needed": 10},
        {"name": "Cosmic Ink", "id": 194755, "price": 2, "amount_needed": 250},
        {"name": "Runed Writhebark", "id": 194863, "price": 3, "amount_needed": 50},
        {"name": "Resonant Crystal", "id": 200113, "price": 8, "amount_needed": 200},
        {"name": "Awakened Fire", "id": 190321, "price": 4, "amount_needed": 150},
        {"name": "Awakened Earth", "id": 190316, "price": 4, "amount_needed": 100},
        {"name": "Awakened Order", "id": 190324, "price": 6, "amount_needed": 50},
        {"name": "Obsidian Cobraskin", "id": 205413, "price": 10, "amount_needed": 3},
        {"name": "Mireslush Hide", "id": 193230, "price": 2, "amount_needed": 50},
        {"name": "Zaralek Glowspores", "id": 204460, "price": 1, "amount_needed": 400},
        {"name": "Dreaming Essence", "id": 208212, "price": 5, "amount_needed": 5},
    ],
    "total_price": 0  # This will not be used in the JSON file, just here for completeness
}

# Collect data
collected_data = collect_item_data(items_details)

# Save data to JSON
save_to_json(collected_data)