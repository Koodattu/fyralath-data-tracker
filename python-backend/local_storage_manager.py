import json
import os

class LocalStorageManager:
    def __init__(self):
        self.base_path = 'aggregated_data'
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def _get_file_path(self, collection_name):
        """Utility method to construct file path for a collection."""
        return os.path.join(self.base_path, f'{collection_name}.json')

    def save_latest_item_prices(self, document):
        """Replaces the existing document in 'latest_item_prices.json' with the new one."""
        file_path = self._get_file_path('latest_item_prices')
        with open(file_path, 'w') as file:
            json.dump(document, file)
        return "saved"

    def save_region_data(self, collection_prefix, region, document):
        """Saves data to the specified region's file."""
        file_path = self._get_file_path(f"{collection_prefix}_{region}")
        with open(file_path, 'w') as file:
            json.dump(document, file)
        return "saved"

    def get_latest_item_prices(self):
        """Retrieves the single document from 'latest_item_prices.json'."""
        file_path = self._get_file_path('latest_item_prices')
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                document = json.load(file)
            return document
        return None

    def get_all_region_data(self, collection_prefix):
        """Retrieves all documents from region-specific files and returns them as a single JSON object."""
        regions = ['us', 'eu', 'kr', 'tw']
        all_data = {}
        for region in regions:
            file_path = self._get_file_path(f"{collection_prefix}_{region}")
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    documents = json.load(file)
                all_data[region] = documents
        return all_data

    def save_total_costs(self, region, document):
        return self.save_region_data('total_costs', region, document)

    def save_daily_average(self, region, document):
        return self.save_region_data('daily_average', region, document)

    def get_all_total_costs(self):
        return self.get_all_region_data("total_costs")
    
    def get_all_daily_averages(self):
        return self.get_all_region_data("daily_average")

# Example usage
# Example usage
if __name__ == "__main__":
    try:
        storage_manager = LocalStorageManager()

        # Retrieve the latest item prices
        latest_prices = storage_manager.get_latest_item_prices()
        if latest_prices:
            print(f'Latest Item Prices: {latest_prices}')
        else:
            print('No data found for latest item prices.')

        # Retrieve total costs data across all regions
        total_costs_data = storage_manager.get_all_total_costs()
        if total_costs_data:
            print('Total Costs Data across all regions:')
            for region, data in total_costs_data.items():
                print(f'{region.upper()}: {data}')
        else:
            print('No data found for total costs across regions.')

        # Retrieve daily average data across all regions
        daily_average_data = storage_manager.get_all_daily_averages()
        if daily_average_data:
            print('Daily Average Data across all regions:')
            for region, data in daily_average_data.items():
                print(f'{region.upper()}: {data}')
        else:
            print('No data found for daily averages across regions.')
    except Exception as e:
        print(f"Failed to operate with Local Storage: {e}")

