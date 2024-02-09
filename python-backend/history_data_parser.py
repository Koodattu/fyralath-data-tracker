import os
import json
from datetime import datetime, timedelta
from collections import defaultdict

class JsonDataParser:
    def __init__(self, base_dir, base_file, output_dir='aggregated_data'):
        self.base_dir = base_dir
        self.base_file = base_file
        self.output_dir = output_dir
        self.base_data = self.load_base_data()
        self.timestamp_cutoff = datetime(2023, 11, 25).timestamp()

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
                total_costs = self.process_region(region_path)
                if total_costs:
                    aggregated_data.append({'region': region, 'data': total_costs})

        self.save_aggregated_data(aggregated_data)


    def process_region(self, region_path):
        total_costs = []
        for item_file in os.listdir(region_path):
            with open(os.path.join(region_path, item_file), 'r') as file:
                item_data = json.load(file)
                item_id = item_data['item']['id']
                for snapshot in item_data['daily']:
                    if snapshot['snapshot'] / 1000 >= self.timestamp_cutoff:
                        total_cost = self.calculate_total_cost(item_id, snapshot['price'])
                        total_costs.append({'timestamp': snapshot['snapshot'], 'total_cost': total_cost})
        return total_costs

    def calculate_total_cost(self, item_id, item_price):
        total_cost = 0
        for part in self.base_data.get('parts', []):
            for subpart in part.get('parts', []):
                if subpart['id'] == item_id and 'amount_needed' in subpart:
                    total_cost += subpart['amount_needed'] * item_price
        return total_cost

    def save_aggregated_data(self, aggregated_data):
        file_path = os.path.join(self.output_dir, 'total_costs.json')
        with open(file_path, 'w') as file:
            json.dump(aggregated_data, file, indent=4)

    def insert_new_record(self, region, new_record):
        self.ensure_output_dir_exists()
        file_path = os.path.join(self.output_dir, 'total_costs.json')
        if not os.path.exists(file_path):
            data = [{'region': region, 'data': [new_record]}]
        else:
            with open(file_path, 'r') as file:
                data = json.load(file)
            for entry in data:
                if entry['region'] == region:
                    entry['data'].append(new_record)
                    break
            else:
                data.append({'region': region, 'data': [new_record]})
        
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)


    def aggregate_daily_averages(self):
        self.ensure_output_dir_exists()
        input_file_path = os.path.join(self.output_dir, 'total_costs.json')
        output_file_path = os.path.join(self.output_dir, 'daily_averages.json')
        
        if not os.path.exists(input_file_path):
            print("Input file does not exist.")
            return
        
        with open(input_file_path, 'r') as file:
            data = json.load(file)
        
        aggregated_data = []
        for region_data in data:
            daily_totals = defaultdict(list)
            for record in region_data['data']:
                date = datetime.fromtimestamp(record['timestamp'] / 1000).date()
                daily_totals[date].append(record['total_cost'])
            
            daily_averages = [{'date': date.strftime('%Y-%m-%d'), 'average_cost': round(sum(prices) / len(prices))} for date, prices in daily_totals.items()]
            aggregated_data.append({'region': region_data['region'], 'data': daily_averages})
        
        with open(output_file_path, 'w') as file:
            json.dump(aggregated_data, file, indent=4)

if __name__ == "__main__":
    parser = JsonDataParser('base_history_data', 'base.json')
    parser.process_files()
    parser.aggregate_daily_averages()