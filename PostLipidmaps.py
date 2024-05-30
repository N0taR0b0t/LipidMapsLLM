#!/Users/matias/anaconda3/bin/python3
import configparser
import os
import logging
from openai import OpenAI
import CheckGPT

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("debug.log", mode='w'), logging.StreamHandler()])

def normalize_group_name(name):
    """Normalize group names to ensure consistency."""
    return name.upper().strip()

def prompt_gpt(client, prompt):
    """Prompt GPT with a given text and return the response using the chat completions endpoint."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are sorting significant compounds from a mass spectrometer analysis."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def setup_logs():
    """Setup a directory for logs and return the path."""
    log_directory = 'logs'
    os.makedirs(log_directory, exist_ok=True)
    return log_directory

def write_to_file(path, content):
    """Write a given content to a specified file."""
    with open(path, 'w') as file:
        file.write(content)

def read_api_key(config_file):
    """Read API key from a config file."""
    config = configparser.ConfigParser()
    config.read(config_file)
    return config['openai']['apikey']

def create_prompt(groups, compounds_to_sort):
    prompt = "Here are the compounds already sorted into groups:\n"
    for group, compounds in groups.items():
        prompt += f"### {group}:\n- " + "\n- ".join(compounds) + "\n"
    prompt += ("""\nMeticulously group these compounds based on their names, by specifying the group name next to each compound.
    Create new groups if necessary or, if you notice a mistake, move compounds between groups using the format 'move <compound> from <old_group> to <new_group>'.
    Format your response as 'Compound => Group' for sorting.
    Group each compound into the most precise category based on its chemical structure, biological function, and standard biochemical classifications.
    Take a nuanced approach to ensure that similar compounds like fatty acids, glycerolipids, glycerophospholipids, eicosanoids, vitamins, steroids, quinones, and lactones are identified and grouped together.
    Try to avoid creating a group called 'Other', make an effort to find an accurate group for all compounds.
    Do not include comments or explanations in your commands.
    Do not include words like 'New', 'Group', or 'None' while sorting, and avoid mistakes such as attempting the command 'from none to new group'.
    Group these compounds for now:\n""")
    prompt += "\n".join(f"- {comp.split(':')[0]}" for comp in compounds_to_sort)
    return prompt

def parse_gpt_output(output, groups, compounds_to_sort, already_sorted, normalized_compounds):
    sorted_compounds = []
    lines = output.strip().split('\n')
    for line in lines:
        original_line = line  # Keep the original line for debugging
        line = line.strip()
        if "=>" in line:
            parts = line.split("=>")
            if len(parts) == 2:
                raw_compound, group = parts[0].replace('-', '').strip(), parts[1].strip()
                normalized_name = (CheckGPT.normalize_compound_name(raw_compound).replace('-', '').split(':')[0]).upper().strip()
                if normalized_name in normalized_compounds:
                    compound = normalized_compounds[normalized_name]
                    if compound not in already_sorted:
                        if group not in groups:
                            groups[group] = []
                        groups[group].append(compound)
                        sorted_compounds.append(compound)
                        already_sorted.add(compound)
                    else:
                        logging.warning(f"Skipping '{compound}'; already sorted into a group.")
                else:
                    logging.warning(f"Compound '{raw_compound}' ({normalized_name}) not found in list.")
            else:
                logging.warning(f"Could not split the line into compound and group: '{original_line}'")
        elif "move" in line.lower():
            parts = line.lower().split("move")[1].strip().split("from")
            if len(parts) == 2:
                move_parts = parts[1].strip().split("to")
                if len(move_parts) == 2:
                    compound_name = parts[0].strip()
                    old_group, new_group = move_parts[0].strip(), move_parts[1].strip()
                    normalized_name = CheckGPT.normalize_compound_name(compound_name)
                    normalized_old_group = normalize_group_name(old_group)
                    normalized_new_group = normalize_group_name(new_group)
                    if normalized_name in normalized_compounds:
                        compound = normalized_compounds[normalized_name]
                        if normalized_old_group in groups and compound in groups[normalized_old_group]:
                            groups[normalized_old_group].remove(compound)
                            if normalized_new_group not in groups:
                                groups[normalized_new_group] = []
                            groups[normalized_new_group].append(compound)
                        else:
                            logging.warning(f"Move failed; compound '{compound_name}' not found in group '{old_group}'.")
                    else:
                        logging.warning(f"Move failed; compound '{compound_name}' not recognized.")
        elif original_line != '':
            logging.warning(f"No valid command found in line: '{original_line}'")
    return sorted_compounds

def load_postgpt_compounds(file_path):
    """Load and parse compounds from PostGPT.txt, returning a dictionary where each formula is a key and its value is the category."""
    compounds = {}
    current_category = None

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line.endswith(':'):
                current_category = line[:-1]  # Remove the colon to get the category name
            elif line:  # This is a list of compounds under the current category
                formulas = line.split(', ')
                for formula in formulas:
                    compounds[formula] = current_category

    return compounds

def main():
    unique_file_path = 'LipidMaps.txt'
    config_file = 'config.ini'
    api_key = read_api_key(config_file)
    client = OpenAI(api_key=api_key)
    compounds = CheckGPT.load_compounds(unique_file_path)
    groups = {}
    already_sorted = set()
    log_contents = []

    # Create a mapping from normalized names to original names
    normalized_compounds = {CheckGPT.normalize_compound_name(comp): comp for comp in compounds}

    while compounds:
        batch_to_sort = compounds[:10] if len(compounds) > 10 else compounds[:]
        prompt = create_prompt(groups, batch_to_sort)
        gpt_output = prompt_gpt(client, prompt)
        sorted_compounds = parse_gpt_output(gpt_output, groups, batch_to_sort, already_sorted, normalized_compounds)
        
        log_contents.append(f"Prompt:\n{prompt}\n")
        log_contents.append(f"GPT Output:\n{gpt_output}\n")
        
        # Update the list of compounds by removing those that have been sorted
        compounds = [comp for comp in compounds if CheckGPT.normalize_compound_name(comp) not in already_sorted]

        if not sorted_compounds:  # Check if no compounds were sorted in this iteration
            print("Warning: No compounds were sorted in this iteration.")
            break  # Optionally break to avoid infinite loop if nothing is being sorted

    # Save to PostGPT.txt before running the not_found check logic
    with open("PostGPT.txt", 'w') as file:
        for group, members in groups.items():
            file.write(f"{group}:\n")
            file.write(", ".join(members) + "\n\n")

    # Validate the sorting using CheckGPT script
    unique_compounds = CheckGPT.load_compounds(unique_file_path)
    postgpt_compounds = load_postgpt_compounds("PostGPT.txt")
    not_found = CheckGPT.compare_compounds(
        {CheckGPT.normalize_compound_name(comp): comp for comp in unique_compounds},
        {CheckGPT.normalize_compound_name(comp): comp for comp in postgpt_compounds}
    )

    # If compounds were not found, reprocess them
    while not_found:
        compounds = not_found
        normalized_compounds = {CheckGPT.normalize_compound_name(comp): comp for comp in compounds}
        while compounds:
            batch_to_sort = compounds[:10] if len(compounds) > 10 else compounds[:]
            prompt = create_prompt(groups, batch_to_sort)
            gpt_output = prompt_gpt(client, prompt)
            sorted_compounds = parse_gpt_output(gpt_output, groups, batch_to_sort, already_sorted, normalized_compounds)
            
            log_contents.append(f"Prompt:\n{prompt}\n")
            log_contents.append(f"GPT Output:\n{gpt_output}\n")
            
            # Update the list of compounds by removing those that have been sorted
            compounds = [comp for comp in compounds if CheckGPT.normalize_compound_name(comp) not in already_sorted]

            if not sorted_compounds:  # Check if no compounds were sorted in this iteration
                print("Warning: No compounds were sorted in this iteration.")
                break  # Optionally break to avoid infinite loop if nothing is being sorted

        # Save to PostGPT.txt again after reprocessing
        with open("PostGPT.txt", 'a') as file:
            for group, members in groups.items():
                file.write(f"{group}:\n")
                file.write(", ".join(members) + "\n\n")

        # Validate the sorting again using CheckGPT script
        unique_compounds = CheckGPT.load_compounds(unique_file_path)
        postgpt_compounds = CheckGPT.load_compounds("PostGPT.txt")
        not_found = CheckGPT.compare_compounds(
            {CheckGPT.normalize_compound_name(comp): comp for comp in unique_compounds},
            {CheckGPT.normalize_compound_name(comp): comp for comp in postgpt_compounds}
        )

    # Once all processing is complete, write the final log file
    log_file_path = os.path.join(setup_logs(), "final_conversation.log")
    write_to_file(log_file_path, "\n".join(log_contents))

if __name__ == "__main__":
    main()