from datetime import datetime
from mongodb_manager import MongoDBManager

class AcquisitionDataAggregator:
    def aggregate_data(self):
        db_manager = MongoDBManager()
        collections = ['chars_death-knight', 'chars_paladin', 'chars_warrior']
        data = {}
        for collection in collections:
            docs = db_manager.db[collection].find({})
            data[collection] = list(docs)
    
        meeressteel_timestamp = 1701193528
        meeressteel_date = datetime.utcfromtimestamp(meeressteel_timestamp)
        current_time = datetime.utcnow()
        max_weeks_since_meeressteel = (current_time - meeressteel_date).days // 7

        # Initialize the structure for aggregated data
        summary = {
            'total': {'true': 0, 'false': 0},
            'death-knight': {'true': 0, 'false': 0},
            'paladin': {'true': 0, 'false': 0},
            'warrior': {'true': 0, 'false': 0},
            'kills_summary': {
                'chars_with_weapon_hc': {str(k): 0 for k in range(max_weeks_since_meeressteel + 1)},
                'chars_with_weapon_m': {str(k): 0 for k in range(max_weeks_since_meeressteel + 1)},
                'chars_without_weapon_hc': {str(k): 0 for k in range(max_weeks_since_meeressteel + 1)},
                'chars_without_weapon_m': {str(k): 0 for k in range(max_weeks_since_meeressteel + 1)}
            }
        }
        daily_acquisitions = {}
        cumulative_acquisitions = {}

        for collection in collections:
            docs = db_manager.db[collection].find({})
            class_name = collection.split('_')[-1]  # Extract class name from collection name
            for doc in docs:
                timestamp = int(doc['fyralath_acquired_date'])
                kills_hc = min(doc.get('fyrakk_kills_hc', 0), max_weeks_since_meeressteel)
                kills_m = min(doc.get('fyrakk_kills_m', 0), max_weeks_since_meeressteel)
                
                if timestamp == 0:
                    summary[class_name]['false'] += 1
                    summary['total']['false'] += 1
                    summary['kills_summary']['chars_without_weapon_hc'][str(kills_hc)] += 1
                    summary['kills_summary']['chars_without_weapon_m'][str(kills_m)] += 1
                else:
                    summary[class_name]['true'] += 1
                    summary['total']['true'] += 1
                    date_time = datetime.utcfromtimestamp(timestamp)
                    weeks_since_acquisition = (date_time - meeressteel_date).days // 7 + 1
                    kills_hc = min(kills_hc, weeks_since_acquisition)
                    kills_m = min(kills_m, weeks_since_acquisition)
                    summary['kills_summary']['chars_with_weapon_hc'][str(kills_hc)] += 1
                    summary['kills_summary']['chars_with_weapon_m'][str(kills_m)] += 1
                    
                    date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
                    if date not in daily_acquisitions:
                        daily_acquisitions[date] = {'total': 0, 'death-knight': 0, 'paladin': 0, 'warrior': 0}
                    daily_acquisitions[date][class_name] += 1
                    daily_acquisitions[date]['total'] += 1

        # Calculate cumulative acquisitions
        cumulative_counts = {'total': 0, 'death-knight': 0, 'paladin': 0, 'warrior': 0}
        for date in sorted(daily_acquisitions.keys()):
            for class_name in ['death-knight', 'paladin', 'warrior']:
                cumulative_counts[class_name] += daily_acquisitions[date][class_name]
            cumulative_counts['total'] += daily_acquisitions[date]['total']
            cumulative_acquisitions[date] = cumulative_counts.copy()

        self.update_database_with_aggregated_data(db_manager, summary, daily_acquisitions, cumulative_acquisitions)

    def update_database_with_aggregated_data(self, db_manager, summary, daily_acquisitions, cumulative_acquisitions):
        # Ensure only the latest summary document exists
        db_manager.db['acquisitions_summary'].delete_many({})
        db_manager.db['acquisitions_summary'].insert_one(summary)

        # Sort the dates in ascending order for both daily and cumulative acquisitions
        sorted_daily_dates = sorted(daily_acquisitions.keys())
        sorted_cumulative_dates = sorted(cumulative_acquisitions.keys())

        # Save daily acquisitions in the order of the oldest date first
        for date in sorted_daily_dates:
            acquisitions = daily_acquisitions[date]
            db_manager.db['acquisitions_daily'].update_one({'date': date}, {'$set': acquisitions}, upsert=True)

        # Save cumulative acquisitions in the order of the oldest date first
        for date in sorted_cumulative_dates:
            acquisitions = cumulative_acquisitions[date]
            db_manager.db['acquisitions_cumulative'].update_one({'date': date}, {'$set': acquisitions}, upsert=True)

if __name__ == "__main__":
    agg = AcquisitionDataAggregator()
    agg.aggregate_data()