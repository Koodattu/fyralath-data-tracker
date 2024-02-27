import requests
import struct
import json
from exchange_data_parser import ExchangeDataParser

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

class ExchangeDataFetcher:
    def collect_item_data(self):
        realms = {
            "us": 32512,
            "eu": 32513,
            "tw": 32514,
            "kr": 32515
        }

        items_details = {
        "items": [
            {"name": "Shadowflame Essence", "id": 204464},
            {"name": "Cosmic Ink", "id": 194755},
            {"name": "Runed Writhebark", "id": 194863},
            {"name": "Resonant Crystal", "id": 200113},
            {"name": "Awakened Fire", "id": 190321},
            {"name": "Awakened Earth", "id": 190316},
            {"name": "Awakened Order", "id": 190324},
            {"name": "Obsidian Cobraskin", "id": 205413},
            {"name": "Mireslush Hide", "id": 193230},
            {"name": "Zaralek Glowspores", "id": 204460},
            {"name": "Dreaming Essence", "id": 208212},
            ]
        }

        data = {realm: [] for realm in realms}

        for realm_name, realm_id in realms.items():
            for item in items_details["items"]:
                item_state = get_item_state(realm_id, item["id"])
                if "daily" in item_state:
                    data[realm_name].append({
                        "name": item["name"],
                        "id": item["id"],
                        "snapshots": [
                            {"timestamp": entry["snapshot"], "price": entry["price"]}
                            for entry in item_state["daily"]
                        ]
                    })

        return data

if __name__ == "__main__":
    fetcher = ExchangeDataFetcher()
    data = fetcher.collect_item_data()
    parser = ExchangeDataParser()
    parser.aggregate_and_save(data)