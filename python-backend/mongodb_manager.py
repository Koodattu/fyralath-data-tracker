from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import os

class MongoDBManager:
    def __init__(self):
        try:
            # Load environment variables
            load_dotenv()
            # Load MongoDB connection string from .env file
            connection_string = os.getenv('MONGODB_CONNECTION_STRING', '')
            self.client = MongoClient(connection_string)
            # Check if the server is available
            self.client.admin.command('ping')
            # Assuming the database name is included in the connection string
            # If not, replace 'fyralath-price-data' with your database name
            self.db = self.client['fyralath-price-data']
        except ConnectionFailure as e:
            print(f"Connection to MongoDB failed: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def save_latest_item_prices(self, document):
        """Replaces the existing document in 'latest_item_prices' with the new one."""
        collection = self.db['latest_item_prices']
        collection.delete_many({})  # Delete all documents in the collection
        result = collection.insert_one(document)
        return result.inserted_id

    def save_region_data(self, collection_prefix, region, document):
        """Saves data to the specified region's collection."""
        collection_name = f"{collection_prefix}_{region}"
        collection = self.db[collection_name]
        result = collection.insert_one(document)
        return result.inserted_id

    def get_latest_item_prices(self):
        """Retrieves the single document from 'latest_item_prices'."""
        collection = self.db['latest_item_prices']
        document = collection.find_one()
        return document

    def get_all_region_data(self, collection_prefix):
        """Retrieves all documents from region-specific collections and returns them as a single JSON object."""
        regions = ['us', 'eu', 'kr', 'tw']
        all_data = []
        for region in regions:
            collection_name = f"{collection_prefix}_{region}"
            collection = self.db[collection_name]
            documents = list(collection.find())
            all_data.append({"region": region, "data": documents})
        return all_data

    def check_date_exists_in_daily_average(self, region, date):
        """Checks if a given date already exists in the daily_average_[region] collection."""
        collection_name = f"daily_averages_{region}"
        collection = self.db[collection_name]
        exists = collection.find_one({"date": date}) is not None
        return exists

    def check_timestamp_exists_in_total_costs(self, region, timestamp):
        """Checks if a given timestamp already exists in the total_costs_[region] collection."""
        collection_name = f"total_costs_{region}"
        collection = self.db[collection_name]
        exists = collection.find_one({"timestamp": timestamp}) is not None
        return exists

    def get_total_costs_from_previous_day(self, region, given_timestamp):
        """Fetches documents that have timestamps within the previous day of the given timestamp."""
        # Convert given_timestamp from milliseconds to a datetime object
        given_date = datetime.utcfromtimestamp(given_timestamp / 1000)
        
        # Calculate start and end of the previous day
        start_of_previous_day = given_date - timedelta(days=1)
        start_of_previous_day = datetime(start_of_previous_day.year, start_of_previous_day.month, start_of_previous_day.day)
        end_of_previous_day = start_of_previous_day + timedelta(days=1)

        # Convert back to timestamps in milliseconds
        start_timestamp = int(start_of_previous_day.timestamp() * 1000)
        end_timestamp = int(end_of_previous_day.timestamp() * 1000)

        # Define collection name based on prefix and region
        collection_name = f"total_costs_{region}"
        collection = self.db[collection_name]

        # Query for documents within the previous day
        documents = list(collection.find({
            "timestamp": {
                "$gte": start_timestamp,
                "$lt": end_timestamp
            }
        }))

        return documents

    def get_all_acquisitions(self, collection_suffix):
        """Retrieves all documents from the specified collection."""
        collection_name = f"acquisitions_{collection_suffix}"
        collection = self.db[collection_name]
        documents = list(collection.find())
        return documents

    def save_to_collection(self, collection_prefix, region, document):
        """Appends total costs data to the specified region's file."""
        return self.save_region_data(collection_prefix, region, document)

    def save_total_costs(self, region, document):
        return self.save_region_data('total_costs', region, document)

    def save_daily_average(self, region, document):
        return self.save_region_data('daily_averages', region, document)

    def get_all_total_costs(self):
        collection_name = "total_costs"
        return self.get_all_region_data(collection_name)
    
    def get_all_daily_averages(self):
        collection_name = "daily_averages"
        return self.get_all_region_data(collection_name)

    def bulk_save_to_collection(self, collection_name, documents):
        """
        Saves a list of JSON objects to the specified collection.

        Parameters:
        - collection_name: The name of the collection where documents are to be saved.
        - documents: A list of JSON objects to save to the collection.
        """
        collection = self.db[collection_name]
        result = collection.insert_many(documents)
        return result.inserted_ids

# Example usage
if __name__ == "__main__":
    try:
        db_manager = MongoDBManager()
        # Retrieve the latest item prices
        latest_prices = db_manager.get_latest_item_prices()
        print(f'Latest Item Prices: {latest_prices}')

        # Retrieve all documents from total_costs collections across all regions
        total_costs_data = db_manager.get_all_region_data('total_costs')
        print('Total Costs Data across all regions:')
        for region, data in total_costs_data.items():
            print(f'{region.upper()}: {data}')

        # Retrieve all documents from daily_average collections across all regions
        daily_average_data = db_manager.get_all_region_data('daily_average')
        print('Daily Average Data across all regions:')
        for region, data in daily_average_data.items():
            print(f'{region.upper()}: {data}')
    except Exception as e:
        print(f"Failed to operate with MongoDB: {e}")