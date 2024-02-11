from datetime import datetime
from collections import defaultdict

class AuctionDataAggregator:
    def calculate_total_cost(self, base_data, item_id, item_price):
        """Calculate total cost based on item ID and price."""
        total_cost = 0
        for part in base_data.get('parts', []):
            for subpart in part.get('parts', []):
                if subpart['id'] == item_id and 'amount_needed' in subpart:
                    total_cost += subpart['amount_needed'] * item_price
        return total_cost

    def process_region_data(self, base_data, region_data, timestamp_cutoff):
        """Process data for a single region."""
        # Dictionary to hold summed total costs by timestamp
        costs_by_timestamp = {}
        for item_data in region_data:
            item_id = item_data['item']['id']
            for snapshot in item_data['daily']:
                if snapshot['snapshot'] / 1000 >= timestamp_cutoff:
                    total_cost = self.calculate_total_cost(base_data, item_id, snapshot['price'])
                    timestamp = snapshot['snapshot']
                
                    # Summing total costs for the same timestamp
                    if timestamp in costs_by_timestamp:
                        costs_by_timestamp[timestamp] += total_cost
                    else:
                        costs_by_timestamp[timestamp] = total_cost
        # Convert the dictionary to a list of dictionaries as required
        total_costs = [{'timestamp': timestamp, 'total_cost': total_cost} for timestamp, total_cost in costs_by_timestamp.items()]
        
        return total_costs

    def aggregate_daily_averages(self, total_costs_data):
        """Aggregate daily averages from total costs data."""
        daily_totals = defaultdict(list)
        for record in total_costs_data:
            date = datetime.fromtimestamp(record['timestamp'] / 1000).date()
            daily_totals[date].append(record['total_cost'])
        
        daily_averages = [{'date': date.strftime('%Y-%m-%d'), 'average_cost': round(sum(prices) / len(prices), 2)} for date, prices in daily_totals.items()]
        return daily_averages
