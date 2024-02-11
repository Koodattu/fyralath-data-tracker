import os
import json
from datetime import datetime

from auction_data_aggregator import AuctionDataAggregator
from local_storage_manager import LocalStorageManager
from mongodb_manager import MongoDBManager

class ExchangeDataParser:
    def __init__(self, base_dir, base_file, output_dir='aggregated_data'):
        self.base_dir = base_dir
        self.base_file = base_file
        self.output_dir = output_dir
        self.base_data = self.load_base_data()
        self.timestamp_cutoff = datetime(2023, 11, 25).timestamp()
        self.aggregator = AuctionDataAggregator()

    def ensure_output_dir_exists(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def load_base_data(self):
        with open(self.base_file, 'r') as file:
            return json.load(file)

    def process_files(self):
        self.ensure_output_dir_exists()
        aggregated_data = []

        for region in os.listdir(self.base_dir):
            region_path = os.path.join(self.base_dir, region)
            if os.path.isdir(region_path):
                region_data = [json.load(open(os.path.join(region_path, item_file), 'r')) for item_file in os.listdir(region_path)]
                total_costs = self.aggregator.process_region_data(self.base_data, region_data, self.timestamp_cutoff)
                if total_costs:
                    aggregated_data.append({'region': region, 'data': total_costs})

        self.save_aggregated_data(aggregated_data)

    def save_aggregated_data(self, aggregated_data, filename='total_costs.json'):
        file_path = os.path.join(self.output_dir, filename)
        with open(file_path, 'w') as file:
            json.dump(aggregated_data, file, indent=4)

    def aggregate_daily_averages(self):
        input_file_path = os.path.join(self.output_dir, 'total_costs.json')
        if not os.path.exists(input_file_path):
            print("Input file does not exist.")
            return
        
        with open(input_file_path, 'r') as file:
            total_costs_data = json.load(file)
        
        aggregated_data = []
        for region_data in total_costs_data:
            daily_averages = self.aggregator.aggregate_daily_averages(region_data['data'])
            aggregated_data.append({'region': region_data['region'], 'data': daily_averages})
        
        self.save_aggregated_data(aggregated_data, 'daily_averages.json')

    def save_data_to_mongodb(self, db_manager):
        # Assuming you want to save both total costs and daily averages
        for filename in ['total_costs.json', 'daily_averages.json']:
            file_path = os.path.join(self.output_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    data = json.load(file)
                for record in data:
                    region = record['region']
                    for document in record['data']:
                        collection_prefix = filename.split('.')[0]  # 'total_costs' or 'daily_averages'
                        db_manager.save_to_collection(collection_prefix, region, document)

if __name__ == "__main__":
    parser = ExchangeDataParser('base_history_data', 'base.json')
    parser.process_files()
    parser.aggregate_daily_averages()
    mongo_db_manager = MongoDBManager()
    parser.save_data_to_mongodb(mongo_db_manager)
    local_db_manager = LocalStorageManager()
    #parser.save_data_to_mongodb(local_db_manager)