import requests
import pandas as pd
import logging
from bs4 import BeautifulSoup
import json
import re

if __name__ == "__main__":

    csv_file = "in/UP/radx_UP_asset_inventory_cleaned.csv"

    #set up logging 
    log_file_path = "in/UP/get_filenames_log_file.txt"
    logging.basicConfig(
		level=logging.INFO, 
		format='%(asctime)s - %(levelname)s - %(message)s', 
		handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()]
		)

    # pattern to find the "items": [...] array in the HTML
    items_pattern = re.compile(r'"items":(\[.*?\])', re.DOTALL)

    df = pd.read_csv(csv_file)

    for index, row in df.iterrows():

        staging_url = row['Staging Location']

        try:
            response = requests.get(staging_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            if not soup: 
                raise Exception(f"NO RETURNED RESPONSE {staging_url}.")
                continue

            # Search for the items array
            items_match = items_pattern.search(response.text)
            if not items_match:
                logging.error(f"Failed to get filename for file: {row['Title']}")
                df.at[index, "Filename"] = "NOT FOUND"
                continue
                
            items_json = items_match.group(1)
            items = json.loads(items_json)

            logging.info(f"\n--- Items for row {index} ---")
            # print(json.dumps(items, indent=2))  # pretty print

            filename = next((i for i in items if i.get("name", "")), None)

            if filename:
                df.at[index, "Filename"] = filename["name"]
                print(filename["name"])
            
        except Exception as e:
            logging.error(f"Failed for file {row['Title']}. Error: {e}")
            continue

    df.to_csv("in/UP/radx_UP_asset_inv_w_filenames.csv", index=False)
