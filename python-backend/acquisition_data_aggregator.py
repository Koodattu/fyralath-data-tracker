import json
import os
from datetime import datetime
from collections import defaultdict
from mongodb_manager import MongoDBManager

def load_data_from_file(file_path):
    """Load data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []

def remove_duplicates(data):
    """Remove duplicates from the data list based on the 'id' field."""
    unique_data = {}
    for item in data:
        unique_data[item['id']] = item
    return list(unique_data.values())

def summarize_class_data(data):
    """Summarize data for a class, counting has_fyrath true, false, and total."""
    summary = {'true': 0, 'false': 0, 'total': 0}
    for item in data:
        summary['total'] += 1  # Increment total count for each item
        if item['has_fyralath']:
            summary['true'] += 1
        else:
            summary['false'] += 1
    return summary

def process_and_summarize_files(directory_path, filenames):
    """Process specified JSON files to remove duplicates and summarize data."""
    summary = {}
    total_summary = {'true': 0, 'false': 0, 'total': 0}
    
    for filename in filenames:
        class_name = filename.replace('_data.json', '')
        file_path = os.path.join(directory_path, filename)
        data = load_data_from_file(file_path)
        if data:
            unique_data = remove_duplicates(data)
            class_summary = summarize_class_data(unique_data)
            summary[class_name] = class_summary
            
            # Update total counts
            total_summary['true'] += class_summary['true']
            total_summary['false'] += class_summary['false']
            total_summary['total'] += class_summary['total']
    
    # Add total summary to the overall summary
    summary['total'] = total_summary
    return summary

def save_summary_to_file(summary, file_path):
    """Save the summary to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(summary, file, ensure_ascii=False, indent=4)

def remove_duplicates_and_sort(data):
    # Remove duplicates and sort
    unique_data = {item['id']: item for item in data}
    sorted_unique_data = sorted(unique_data.values(), key=lambda x: x['id'])
    
    # Reset timestamp for each item
    for item in sorted_unique_data:
        item['timestamp'] = 0
    
    return sorted_unique_data

def process_files(directory_path, filenames):
    for filename in filenames:
        base_name = filename.replace('_data.json', '')
        file_path = os.path.join(directory_path, filename)
        data = load_data_from_file(file_path)
        
        if data:
            sorted_unique_data = remove_duplicates_and_sort(data)
            sorted_file_path = os.path.join(directory_path, f"{base_name}_sorted_data.json")
            with open(sorted_file_path, 'w', encoding='utf-8') as file:
                json.dump(sorted_unique_data, file, ensure_ascii=False, indent=4)
            print(f"Processed and saved sorted data to {sorted_file_path}")

def aggregate_fyralath_acquisitions(directory_path, filenames):
    daily_acquisitions = defaultdict(lambda: defaultdict(int))
    for filename in filenames:
        class_name = filename.replace('_updated_data.json', '')  # Extract class name
        file_path = os.path.join(directory_path, filename)
        data = load_data_from_file(file_path)
        
        for item in data:
            if item['has_fyralath']:
                date = datetime.utcfromtimestamp(item['timestamp']).strftime('%Y-%m-%d')
                daily_acquisitions[date][class_name] += 1
                daily_acquisitions[date]['total'] = daily_acquisitions[date].get('total', 0) + 1
    
    # Convert defaultdict to regular dict for JSON serialization
    daily_acquisitions = {date: dict(classes) for date, classes in daily_acquisitions.items()}
    
    # Generate cumulative data with totals
    cumulative_acquisitions = {}
    total_counts = defaultdict(int)
    cumulative_total = 0
    for date in sorted(daily_acquisitions.keys()):
        daily_total = 0  # Reset daily total for each day
        for class_name, count in daily_acquisitions[date].items():
            if class_name != 'total':  # Exclude the pre-calculated 'total' from double counting
                total_counts[class_name] += count
                daily_total += count  # Sum up daily total from individual class counts
        cumulative_total += daily_total  # Update cumulative total
        
        # Record cumulative totals including the 'total' field
        cumulative_acquisitions[date] = {class_name: total for class_name, total in total_counts.items()}
        cumulative_acquisitions[date]['total'] = cumulative_total
    
    # Save daily and cumulative data to files
    save_summary_to_file(daily_acquisitions, os.path.join(directory_path, 'daily_acquisitions.json'))
    save_summary_to_file(cumulative_acquisitions, os.path.join(directory_path, 'cumulative_acquisitions.json'))

def json_to_document_list(json_data, json_key):
    documents = []
    for key, value in json_data.items():
        document = {json_key: key}  # Change 'class_name' to your desired field name for the key
        document.update(value)  # Add the nested key-value pairs to the document
        documents.append(document)
    return documents

DATA_DIR = "./rio_data"  # Example directory
FILES_TO_PROCESS = ["death-knight_data.json", "paladin_data.json", "warrior_data.json"]
UPDATED_FILES_TO_PROCESS = ["death-knight_updated_data.json", "paladin_updated_data.json", "warrior_updated_data.json"]
SUMMARY_FILE_PATH = os.path.join(DATA_DIR, "summary_data.json")

if __name__ == "__main__":
    #summary = process_and_summarize_files(DATA_DIR, FILES_TO_PROCESS)
    #save_summary_to_file(summary, SUMMARY_FILE_PATH)
    #print(f"Summary saved to {SUMMARY_FILE_PATH}")
    #process_files(DATA_DIR, FILES_TO_PROCESS)
    #print("All files processed and sorted.")

    #aggregate_fyralath_acquisitions(DATA_DIR, UPDATED_FILES_TO_PROCESS)
    #print("Fyralath acquisitions aggregated and saved.")

    db_manager = MongoDBManager()
    db_manager.bulk_save_to_collection('acquisitions_cumulative', json_to_document_list(load_data_from_file('./rio_data/cumulative_acquisitions.json'), 'date'))
    #db_manager.bulk_save_to_collection('acquisitions_daily', json_to_document_list(load_data_from_file('./rio_data/daily_acquisitions.json'), 'date'))
    #db_manager.bulk_save_to_collection('acquisitions_summary', json_to_document_list(load_data_from_file('./rio_data/summary_data.json'), 'date'))