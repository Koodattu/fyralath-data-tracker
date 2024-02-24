import os
import json
from datetime import datetime
from auction_data_aggregator import AuctionDataAggregator
from mongodb_manager import MongoDBManager

class ExchangeDataParser:
    def __init__(self, base_dir, base_file, output_dir='aggregated_data'):
        self.base_dir = base_dir
        self.base_file = base_file
        self.output_dir = output_dir
        self.base_data = self.load_base_data()
        self.timestamp_cutoff = datetime(2023, 11, 25).timestamp()
        self.aggregator = AuctionDataAggregator()

    def load_base_data(self):
        with open(self.base_file, 'r') as file:
            return json.load(file)

    def process_files(self):
        aggregated_data = []

        for region in os.listdir(self.base_dir):
            region_path = os.path.join(self.base_dir, region)
            if os.path.isdir(region_path):
                region_data = [json.load(open(os.path.join(region_path, item_file), 'r')) for item_file in os.listdir(region_path)]
                total_costs = self.aggregator.process_region_data(self.base_data, region_data, self.timestamp_cutoff)
                if total_costs:
                    aggregated_data.append({'region': region, 'data': total_costs})
                    
        return aggregated_data

    def aggregate_daily_averages_and_save(self):
        mongo_db_manager = MongoDBManager()
        aggregated_data = self.process_files()
        for region_data in aggregated_data:
            daily_averages = self.aggregator.aggregate_daily_averages(region_data['data'])
            collection_prefix = 'daily_averages'
            mongo_db_manager.save_to_collection(collection_prefix, region_data['region'], daily_averages)

if __name__ == "__main__":
    parser = ExchangeDataParser('base_history_data', 'base.json')
    parser.aggregate_daily_averages_and_save()