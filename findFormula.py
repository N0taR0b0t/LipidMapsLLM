import csv
import logging

# Set up logging
logging.basicConfig(filename='fetch_lipidmaps.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_matching_formula(unique_file, compounds_file, output_file):
    with open(unique_file, 'r') as uf:
        unique_lines = [line.strip() for line in uf.readlines()]

    formula_to_compounds = {}
    unique_formulas = set()
    duplicate_formulas = {}

    with open(compounds_file, 'r') as cf:
        reader = csv.DictReader(cf)
        for unique_line in unique_lines:
            cf.seek(0)
            for row in reader:
                if unique_line in row.values():
                    formula = row['Formula']
                    compound_name = row['Name']
                    if formula in formula_to_compounds:
                        formula_to_compounds[formula].append(compound_name)
                    else:
                        formula_to_compounds[formula] = [compound_name]

    with open(output_file, 'w') as of:
        for formula, compound_names in formula_to_compounds.items():
            unique_compound_names = list(set(compound_names))
            of.write(f"{formula}\n")
            if len(unique_compound_names) > 1:
                duplicate_formulas[formula] = unique_compound_names

    for formula, compound_names in duplicate_formulas.items():
        logging.warning(f"Formula '{formula}' found in multiple compounds: {', '.join(compound_names)}")

if __name__ == "__main__":
    unique_file = 'Unique.txt'
    compounds_file = 'Compounds.csv'
    output_file = 'MatchedFormulas.txt'

    find_matching_formula(unique_file, compounds_file, output_file)
    print(f"Matching formulas have been written to {output_file}")