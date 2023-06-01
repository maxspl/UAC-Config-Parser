import os
import yaml
import pandas as pd
import argparse
import fnmatch

def unknown_constructor(loader, tag_suffix, node): #If  profile contains "!", replace it by "exclude_" or script will crash
    return "exclude_" + node.tag[1:]


parser = argparse.ArgumentParser()
parser.add_argument('root_path', help='The root path to begin searching for YAML files. Hint : submit UAC path')
args = parser.parse_args()

print("\n[INFO] - Parsing started.\n----------\n\n")

root_path = args.root_path

data = pd.DataFrame()
profile_data = {}

# Parse profiles
profiles_path = os.path.join(root_path, 'profiles')
for file in os.listdir(profiles_path):
    if file.endswith('.yaml'):
        with open(os.path.join(profiles_path, file), 'r') as f:
            try:
                yaml.SafeLoader.add_multi_constructor('!', unknown_constructor)
                profile_content = yaml.safe_load(f)
                if profile_content is not None and 'artifacts' in profile_content:
                    for artifact in profile_content['artifacts']:
                        if artifact not in profile_data:
                            profile_data[artifact] = []
                        profile_data[artifact].append(file)
            except yaml.YAMLError as e:
                print(f"Failed to parse {os.path.join(profiles_path, file)}: {e}")

for root, dirs, files in os.walk(os.path.join(root_path, 'artifacts')):
    for file in files:
        if file.endswith('.yaml'):
            parts = os.path.relpath(os.path.join(root, file), os.path.join(root_path, 'artifacts')).split('/')
            category = parts[0]
            subcategories = '/'.join(parts[1:-1]) 
            yaml_name = parts[-1]

            with open(os.path.join(root, file), 'r') as f:
                try:
                    yaml_content = yaml.safe_load(f)
                    if yaml_content is not None:
                        yaml_df = pd.json_normalize(yaml_content, record_path=['artifacts'])
                        yaml_df['Category'] = category
                        yaml_df['Subcategory'] = subcategories
                        yaml_df['YAML Name'] = yaml_name
                        yaml_df['Profiles'] = ''  # Initialize Profiles column

                        for artifact, profiles in profile_data.items():
                            if fnmatch.fnmatch(os.path.join(category, subcategories, yaml_name), artifact):
                                yaml_df['Profiles'] += ', '.join(profiles)

                        data = pd.concat([data, yaml_df], ignore_index=True)
                except yaml.YAMLError as e:
                    print(f"[ERROR] - Failed to parse {os.path.join(root, file)}")
                    # Modify the file content in memory to remove the problematic characters
                    file_content = open(os.path.join(root, file),'r').read() # Remove chars that break prevent python to read the yaml
                    modified_content = file_content.replace("'", "")
                    modified_content = modified_content.replace('\t', '')
                    modified_content = modified_content.replace('%', '')
                    # Use the modified content for further processing or parsing
                    try :
                        yaml_content = yaml.safe_load(modified_content)
                        if yaml_content is not None:
                            # Continue with the parsing process using the modified content
                            print('....[INFO] - Yaml modification succeed. Yaml has been finally read')
                            yaml_df = pd.json_normalize(yaml_content, record_path=['artifacts'])
                            yaml_df['Category'] = category
                            yaml_df['Subcategory'] = subcategories
                            yaml_df['YAML Name'] = yaml_name
                            yaml_df['Profiles'] = ''  # Initialize Profiles column

                            for artifact, profiles in profile_data.items():
                                if fnmatch.fnmatch(os.path.join(category, subcategories, yaml_name), artifact):
                                    yaml_df['Profiles'] += ', '.join(profiles)

                            data = pd.concat([data, yaml_df], ignore_index=True)
                        else :
                            print('WHAT ?')
                    except Exception as e:
                        print('....[ERROR] - yaml modification didnt help. Error :',e)


# Post-processing: exclude profiles
for artifact, profiles in profile_data.items():
    if artifact.startswith('exclude'):  # This is an exclude rule
        artifact = artifact[8:]  # Remove exclude_
        for index, row in data.iterrows():
            #print("hey ",os.path.join(row['Category'], row['Subcategory'], row['YAML Name']),artifact)
            if fnmatch.fnmatch(os.path.join(row['Category'], row['Subcategory'], row['YAML Name']), artifact):
                for profile in profiles:
                    # Remove this profile from the list of profiles for this row
                    
                    profile_list = row['Profiles'].split(', ')
                    
                    if profile in profile_list:
                        profile_list.remove(profile)
                        data.at[index, 'Profiles'] = ', '.join(profile_list)

data = data.reindex(columns=['description', 'Category', 'Subcategory', 'YAML Name','collector','Profiles','path','exclude_file_system','name_pattern',"command"] + [col for col in data.columns if col not in ['description', 'Category', 'Subcategory', 'YAML Name','collector','Profiles','path','exclude_file_system','name_pattern',"command"]])

data.to_csv('UAC_artifacts_flatten.csv', index=False)

print("\n----------\n\n[INFO] - Parsing succesful. Output : UAC_artifacts_flatten.csv\n"    )

