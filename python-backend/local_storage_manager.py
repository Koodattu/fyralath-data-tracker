from datetime import datetime, timedelta
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

    def check_date_exists_in_daily_average(self, region, date):
        """Checks if an entry for the current year, month and day exists in the file."""
        filename = self._get_file_path(f"daily_average_{region}")

        try:
            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    data = json.load(file)
                    for entry in data:
                        entry_date = entry['date']
                        if entry_date == date:
                            return True
            return False
        except Exception as e:
            print(f"Error checking daily average entry existence for {region} region: {e}")
            return False

    def check_timestamp_exists_in_total_costs(self, region, timestamp):
        """Checks if an entry for the current year, month, day, and hour exists in the file."""
        filename = self._get_file_path(f"total_costs_{region}")

        try:
            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    data = json.load(file)
                    for entry in data:
                        entry_date_hour = entry['timestamp']
                        if entry_date_hour == timestamp:
                            return True
            return False
        except Exception as e:
            print(f"Error checking total costs entry existence for {region} region: {e}")
            return False

    def append_document_to_file(self, file_path, document):
        """Appends a new document to the existing JSON file."""
        data = []
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    # Handles empty or corrupted file scenario
                    data = []

        data.append(document)
        
        with open(file_path, 'w') as file:
            json.dump(data, file)

    def get_total_costs_from_previous_day(self, region, given_timestamp):
        """Retrieves documents with timestamps within the previous day of the given timestamp."""
        file_path = self._get_file_path(f"total_costs_{region}")
        previous_day_documents = []

        if not os.path.exists(file_path):
            return previous_day_documents  # Return an empty list if file doesn't exist

        # Convert given timestamp to datetime for calculations
        given_date = datetime.utcfromtimestamp(given_timestamp / 1000)

        # Calculate start and end timestamps for the previous day in milliseconds
        start_of_previous_day = (given_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_previous_day = (given_date - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)

        start_timestamp = int(start_of_previous_day.timestamp() * 1000)
        end_timestamp = int(end_of_previous_day.timestamp() * 1000)

        with open(file_path, 'r') as file:
            try:
                documents = json.load(file)
                for document in documents:
                    # Ensure the document's timestamp is within the previous day's range
                    if "timestamp" in document and start_timestamp <= int(document["timestamp"]) <= end_timestamp:
                        previous_day_documents.append(document)
            except json.JSONDecodeError:
                # If the file is empty or corrupted
                pass

        return previous_day_documents

    def save_to_collection(self, collection_prefix, region, document):
        """Appends total costs data to the specified region's file."""
        file_path = self._get_file_path(f"{collection_prefix}_{region}")
        self.append_document_to_file(file_path, document)
        return "saved"

    def save_total_costs(self, region, document):
        """Appends total costs data to the specified region's file."""
        file_path = self._get_file_path(f"total_costs_{region}")
        self.append_document_to_file(file_path, document)
        return "saved"

    def save_daily_average(self, region, document):
        """Appends daily average data to the specified region's file."""
        file_path = self._get_file_path(f"daily_average_{region}")
        self.append_document_to_file(file_path, document)
        return "saved"

    def get_all_total_costs(self):
        return self.get_all_region_data("total_costs")
    
    def get_all_daily_averages(self):
        return self.get_all_region_data("daily_average")

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

