from datetime import datetime
from auction_data_aggregator import AuctionDataAggregator
from mongodb_manager import MongoDBManager

class ExchangeDataParser:
    def __init__(self):
        self.timestamp_cutoff = datetime(2023, 11, 25).timestamp()
        self.aggregator = AuctionDataAggregator()
        self.item_requirements = {
            204464: 10, 194755: 250, 194863: 50, 200113: 200,
            190321: 150, 190316: 100, 190324: 50, 205413: 3,
            193230: 50, 204460: 400, 208212: 5
        }

    def aggregate_and_save(self, data):
        mongo_db_manager = MongoDBManager()
        for region, items_data in data.items():
            processed_data = self.process_data_for_region(items_data, self.timestamp_cutoff)
            if processed_data:
                mongo_db_manager.bulk_save_to_collection(f'daily_averages_{region}', processed_data)

    def process_data_for_region(self, items_data, timestamp_cutoff):
        valid_snapshots = {}
        for item in items_data:
            item_id = item['id']
            item_name = item['name']
            for snapshot in item['snapshots']:
                timestamp = snapshot['timestamp']
                if timestamp >= timestamp_cutoff:
                    if timestamp not in valid_snapshots:
                        valid_snapshots[timestamp] = []
                    valid_snapshots[timestamp].append({
                        "name": item_name,
                        "id": item_id,
                        "price": snapshot['price'],
                        "amount_needed": self.item_requirements.get(item_id, 0)
                    })

        # Filter out dates where not all items are present
        complete_snapshots = {ts: items for ts, items in valid_snapshots.items() if len(items) == len(self.item_requirements)}

        documents = []
        for timestamp, items in complete_snapshots.items():
            total_cost = sum(item['price'] * item['amount_needed'] for item in items)
            document = {
                "timestamp": timestamp,
                "items": [{"name":item["name"], "id": item["id"], "price": item["price"]} for item in items]
            }
            
            fyralath_detail = {
                "name": "Fyr'alath the Dreamrender", 
                "id": 206448,
                "price": total_cost
            }

            # Append Fyralath as the first item
            document['items'].insert(0, fyralath_detail)

            documents.append(document)

        return documents