import json
import os

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

DATA_DIR = "./rio_data"  # Example directory
FILES_TO_PROCESS = ["death-knight_data.json", "paladin_data.json", "warrior_data.json"]
SUMMARY_FILE_PATH = os.path.join(DATA_DIR, "summary_data.json")

if __name__ == "__main__":
    summary = process_and_summarize_files(DATA_DIR, FILES_TO_PROCESS)
    save_summary_to_file(summary, SUMMARY_FILE_PATH)
    print(f"Summary saved to {SUMMARY_FILE_PATH}")