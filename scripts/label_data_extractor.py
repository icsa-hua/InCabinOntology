import os
import re
from collections import defaultdict

def extract_information_from_titles(directory):
    # Dictionary to store categorized data
    categorized_data = defaultdict(list)

    # Regex pattern to extract information from titles
    pattern = re.compile(r"^(?P<age_group>\w+)\s(?P<demographic>\w+)\s(?P<gender>\w+)(?:\swith\s(?P<accessory>.+?))?\s(?P<eye_state_mouth_state>.+)$")

    # Iterate through files in the directory
    for filename in os.listdir(directory):
        if not filename.endswith('.json'):continue
        match = pattern.match(filename)
        if match:
            info = match.groupdict()
            categorized_data['age_group'].append(info['age_group'])
            categorized_data['demographic'].append(info['demographic'])
            categorized_data['gender'].append(info['gender'])
            categorized_data['accessory'].append(info['accessory'] if info['accessory'] else "None")
            categorized_data['eye_state_mouth_state'].append(info['eye_state_mouth_state'])

    return categorized_data

def main():
    # Specify the directory containing the files
    directory = "./data/labels/"  # Change this to your target directory

    # Extract and categorize information
    categorized_data = extract_information_from_titles(directory)

    # Print the categorized data
    for category, items in categorized_data.items():
        print(f"{category}: {set(items)}")


if __name__ == "__main__":
    main()


# Dataset 
# Has no East-America 
# Has different accessory string formats short hair, gray-hair. 
