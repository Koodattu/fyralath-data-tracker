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
        all_data = {}
        for region in regions:
            collection_name = f"{collection_prefix}_{region}"
            collection = self.db[collection_name]
            documents = list(collection.find())
            all_data[region] = documents
        return all_data

    def save_total_costs(self, region, document):
        return self.save_region_data('total_costs', region, document)

    def save_daily_average(self, region, document):
        return self.save_region_data('daily_average', region, document)

    def get_all_total_costs(self):
        collection_name = "total_costs"
        return self.get_all_region_data(collection_name)
    
    def get_all_daily_averages(self):
        collection_name = "daily_average"
        return self.get_all_region_data(collection_name)

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