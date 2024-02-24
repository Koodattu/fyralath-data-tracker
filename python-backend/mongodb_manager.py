from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import os

class MongoDBManager:
    def __init__(self):
        try:
            load_dotenv()
            connection_string = os.getenv('MONGODB_CONNECTION_STRING', '')
            mongo_db_name = os.getenv('MONGODB_DB_NAME', '')
            self.client = MongoClient(connection_string)
            # Check if the server is available
            self.client.admin.command('ping')
            self.db = self.client[mongo_db_name]
        except ConnectionFailure as e:
            print(f"Connection to MongoDB failed: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_characters_without_fyralath(self):
        characters_needing_update = {}
        for class_name in ['death-knight', 'warrior', 'paladin']:
            collection_name = f'chars_{class_name}'
            characters = self.db[collection_name].find({"fyralath_acquired_date": 0}, {'_id':0, 'char_id': 1, 'name': 1, 'region': 1, 'realm': 1})
            characters_needing_update[class_name] = list(characters)
        return characters_needing_update

    def update_character(self, class_name, character_id, updates):
        collection_name = f'chars_{class_name}'
        self.db[collection_name].update_one({'char_id': character_id}, {'$set': updates})

    def get_saved_character_ids_with_class(self):
        """Fetches IDs of all saved characters from specific class collections and their counts."""
        class_collections = {
            'death-knight': 'chars_death-knight',
            'warrior': 'chars_warrior',
            'paladin': 'chars_paladin'
        }
        saved_ids_with_class = {class_name: [] for class_name in class_collections.keys()}
        counts_per_class = {class_name: 0 for class_name in class_collections.keys()}

        for class_name, collection_name in class_collections.items():
            collection = self.db[collection_name]
            characters = collection.find({}, {'char_id': 1, '_id': 0})
            saved_ids_with_class[class_name] = [char['char_id'] for char in characters]
            counts_per_class[class_name] = collection.count_documents({})

        return saved_ids_with_class, counts_per_class

    def save_character_data_by_class(self, class_name, character_data):
        """Saves character data into a collection categorized by class name."""
        collection = self.db[f'chars_{class_name}']
        result = collection.insert_one(character_data)
        return result.inserted_id

    def save_latest_item_prices(self, document):
        """Replaces the existing document in 'latest_item_prices' with the new one."""
        collection = self.db['latest_item_prices']
        # Delete all documents in the collection
        collection.delete_many({})
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

    def get_data_within_period(self, collection_name, period="all"):
        """
        Retrieves documents from a specified collection within the given time period.
        Period can be 'day', 'week', 'month', or 'all'. Defaults to 'all'.
        """
        current_time = datetime.utcnow()
        if period == "day":
            start_time = current_time - timedelta(days=1)
        elif period == "week":
            start_time = current_time - timedelta(weeks=1)
        elif period == "month":
            start_time = current_time - timedelta(days=30)
        else:  # 'all' or any other value defaults to fetching all records
            start_time = None

        query = {}
        if start_time:
            # Adjust based on your timestamp field format
            # For total_cost with 'timestamp' field
            if 'total_costs' in collection_name:
                query["timestamp"] = {"$gte": int(start_time.timestamp() * 1000)}
            # For daily_average with 'date' field
            elif 'daily_averages' in collection_name:
                start_time_str = start_time.strftime("%Y-%m-%d")
                query["date"] = {"$gte": start_time_str}

        regions = ['us', 'eu', 'kr', 'tw']
        all_data = []
        for region in regions:
            region_collection_name = f"{collection_name}_{region}"
            collection = self.db[region_collection_name]
            documents = list(collection.find(query))
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

    def get_all_total_costs(self, period="all"):
        """
        Fetches all total cost data within the specified time period.
        """
        collection_name = "total_costs"
        return self.get_data_within_period(collection_name, period)
    
    def get_all_daily_averages(self, period="all"):
        """
        Fetches all daily average data within the specified time period.
        """
        collection_name = "daily_averages"
        return self.get_data_within_period(collection_name, period)

    def bulk_save_to_collection(self, collection_name, documents):
        """
        Saves a list of JSON objects to the specified collection.
        """
        collection = self.db[collection_name]
        result = collection.insert_many(documents)
        return result.inserted_ids