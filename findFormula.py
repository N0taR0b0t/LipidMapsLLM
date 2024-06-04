import csv
import logging
import re

# Set up logging
logging.basicConfig(filename='fetch_lipidmaps.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_matching_formula(unique_file, compounds_file, output_file):
    try:
        print(f"Opening unique_file: {unique_file}")
        with open(unique_file, 'r', encoding='utf-8') as uf:
            unique_lines = [line.strip() for line in uf.readlines()]
        print(f"Successfully read unique_file: {unique_lines}")
    except Exception as e:
        print(f"Error reading unique_file: {e}")
        return

    formula_to_compounds = {}
    unique_formulas = set()
    duplicate_formulas = {}
    name_seen = set()

    # Try to read compounds_file with different encodings
    encodings = ['utf-8', 'latin1', 'iso-8859-1']
    for encoding in encodings:
        try:
            print(f"Trying to open compounds_file with encoding: {encoding}")
            with open(compounds_file, 'r', encoding=encoding, errors='replace') as cf:
                reader = csv.DictReader(cf, quotechar='"', skipinitialspace=True)
                for unique_line in unique_lines:
                    cf.seek(0)
                    for row in reader:
                        # Clean up the row keys and values
                        row = {k.strip(): v.strip() for k, v in row.items()}
                        if any(unique_line == str(value) for value in row.values()):
                            print(f"Match found: {unique_line}")
                            formula = row['Formula']
                            compound_name = row['Name']
                            if formula in formula_to_compounds:
                                formula_to_compounds[formula].append(compound_name)
                                if compound_name in name_seen:
                                    logging.warning(f"Duplicate compound name found: {compound_name}")
                                else:
                                    name_seen.add(compound_name)
                            else:
                                formula_to_compounds[formula] = [compound_name]
                                name_seen.add(compound_name)
            print(f"Successfully read compounds_file with encoding: {encoding}")
            break
        except Exception as e:
            print(f"Error reading compounds_file with encoding {encoding}: {e}")
    else:
        print("Failed to read compounds_file with any of the attempted encodings.")
        return

    try:
        print(f"Writing output_file: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as of:
            for formula, compound_names in formula_to_compounds.items():
                unique_compound_names = list(set(compound_names))
                of.write(f"{formula}\n")
                if len(unique_compound_names) > 1:
                    duplicate_formulas[formula] = unique_compound_names
        print(f"Successfully wrote output_file with formulas: {list(formula_to_compounds.keys())}")
    except Exception as e:
        print(f"Error writing output_file: {e}")

    for formula, compound_names in duplicate_formulas.items():
        logging.warning(f"Formula '{formula}' found in multiple compounds: {', '.join(compound_names)}")