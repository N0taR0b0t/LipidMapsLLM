import requests
import logging
import findFormula
import time
import re

# Set up logging
logging.basicConfig(filename='fetch_lipidmaps.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_lipidmaps_data(formula):
    """
    Fetches data from the LipidMaps API for the given formula.
    """
    url = f"https://lipidmaps.org/rest/compound/formula/{formula.replace(' ', '')}/all"
    response = requests.get(url)
    logging.debug(f"Requested URL: {url}")
    logging.debug(f"Response status code: {response.status_code}")
    logging.debug(f"Response content: {response.text}")

    if response.status_code == 200:
        data = response.json()
        logging.debug(f"Response JSON: {data}")

        if isinstance(data, dict):
            if 'Row1' in data:
                data = data['Row1']
            return {
                'core': data.get('core', ''),
                'main_class': data.get('main_class', ''),
                #'sub_class': data.get('sub_class', ''),
                'formula': data.get('formula', '')
            }
        elif isinstance(data, list) and len(data) > 0:
            data = data[0]
            return {
                'core': data.get('core', ''),
                'main_class': data.get('main_class', ''),
                #'sub_class': data.get('sub_class', ''),
                'formula': data.get('formula', '')
            }
        else:
            logging.error(f"No valid data found for formula {formula}")
            print(f"Data for {formula}: {data}")
            return None
    else:
        logging.error(f"Failed to fetch data for formula {formula}")
        return None

def main():
    unique_file = 'Unique.txt'
    compounds_file = 'Compounds.csv'
    matched_formulas_file = 'MatchedFormulas.txt'
    lipidmaps_file = 'LipidMaps.txt'

    # Find matching formulas and write to MatchedFormulas.txt
    findFormula.find_matching_formula(unique_file, compounds_file, matched_formulas_file)

    # Fetch additional data from LipidMaps and write to LipidMaps.txt
    with open(matched_formulas_file, 'r') as mf, open(lipidmaps_file, 'w') as lf:
        for line in mf:
            formula = line.strip().replace(' ', '')
            if formula:
                logging.debug(f"Processing formula: {formula}")
                data = fetch_lipidmaps_data(formula)
                if data:
                    data_core = re.sub(r'\[.*?\]', '', data['core']).strip()
                    data_main_class = re.sub(r'\[.*?\]', '', data['main_class']).strip()
                    lf.write(f"{data['formula']}: {data_core}, {data_main_class}\n")
                    logging.info(f"Fetched data for formula {formula}")
                    time.sleep(0.1)

if __name__ == "__main__":
    main()