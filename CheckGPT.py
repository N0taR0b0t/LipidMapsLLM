#!/Users/matias/anaconda3/bin/python3
import re

def normalize_compound_name(name):
    """Normalize compound names by focusing on essential chemical identifiers."""
    # Extract the primary chemical identifier before any colon or comma
    primary_identifier = re.split(r'[:,]', name)[0].strip()
    # Normalize by converting to uppercase and removing non-alphanumeric characters, except hyphens which might be part of the chemical formula
    normalized = re.sub(r'[^a-zA-Z0-9\-]+', '', primary_identifier).upper()
    return normalized

def load_compounds(file_path):
    """Load compounds from a given file and return a list of normalized compounds."""
    with open(file_path, 'r', encoding='utf-8') as file:
        compounds = [normalize_compound_name(line.strip()) for line in file if line.strip()]
    return compounds

def compare_compounds(unique_compounds, postgpt_compounds):
    """Compare two dictionaries of compounds to find which are missing in the second."""
    not_found = [uc for uc in unique_compounds if uc not in postgpt_compounds]
    if not_found:
        print("The following compounds from Unique.txt were not found in PostGPT.txt:")
        for compound in not_found:
            print(compound)
    return not_found

    print("not_found:", not_found)
    print("unique_compounds:", unique_compounds)
    print("postgpt_compounds:", postgpt_compounds)

    if not_found:
        print("The following compounds were not found in PostGPT.txt:")
        for compound in not_found:
            print(compound)
    return not_found