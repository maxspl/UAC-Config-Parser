import os
import yaml
import pandas as pd
import argparse
import fnmatch
import sys

def unknown_constructor(loader, tag_suffix, node):
    return "exclude_" + node.tag[1:]

# Determine OS
if sys.platform.startswith('win'):
    current_os = "win"
    file_separator = "\\"
elif sys.platform.startswith('linux'):
    current_os = "lin"
    file_separator = "/"

parser = argparse.ArgumentParser()
parser.add_argument('root_path', help='The root path to begin searching for YAML files.')
args = parser.parse_args()

print("\n[INFO] - Parsing started.\n----------\n\n")

root_path = args.root_path

data = pd.DataFrame()
profile_data = {}

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
            parts = os.path.relpath(os.path.join(root, file), os.path.join(root_path, 'artifacts')).split(file_separator)
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
                                if yaml_df['Profiles'].values[0] != '':
                                    yaml_df['Profiles'] += ', '
                                yaml_df['Profiles'] += ', '.join(profiles)

                        data = pd.concat([data, yaml_df], ignore_index=True)
                except yaml.YAMLError as e:
                    print(f"[ERROR] - Failed to parse {os.path.join(root, file)}")
                    file_content = open(os.path.join(root, file),'r').read()
                    modified_content = file_content.replace("'", "")
                    modified_content = modified_content.replace('\t', '')
                    modified_content = modified_content.replace('%', '')
                    try :
                        yaml_content = yaml.safe_load(modified_content)
                        if yaml_content is not None:
                            print('....[INFO] - Yaml modification succeed. Yaml has been finally read')
                            yaml_df = pd.json_normalize(yaml_content, record_path=['artifacts'])
                            yaml_df['Category'] = category
                            yaml_df['Subcategory'] = subcategories
                            yaml_df['YAML Name'] = yaml_name
                            yaml_df['Profiles'] = ''  # Initialize Profiles column

                            for artifact, profiles in profile_data.items():
                                if fnmatch.fnmatch(os.path.join(category, subcategories, yaml_name), artifact):
                                    if yaml_df['Profiles'].values[0] != '':
                                        yaml_df['Profiles'] += ', '
                                    yaml_df['Profiles'] += ', '.join(profiles)

                            data = pd.concat([data, yaml_df], ignore_index=True)
                        else :
                            print('WHAT ?')
                    except Exception as e:
                        print('....[ERROR] - yaml modification didnt help. Error :',e)


for artifact, profiles in profile_data.items():
    if artifact.startswith('exclude'):  # This is an exclude rule
        artifact = artifact[8:]  # Remove exclude_
        for index, row in data.iterrows():
            if fnmatch.fnmatch(os.path.join(row['Category'], row['Subcategory'], row['YAML Name']), artifact):
                for profile in profiles:
                    profile_list = row['Profiles'].split(', ')
                    if profile in profile_list:
                        profile_list.remove(profile)
                        profile_list = list(set(profile_list))
                        data.at[index, 'Profiles'] = ', '.join(profile_list)

data = data.reindex(columns=['description', 'Category', 'Subcategory', 'YAML Name','collector','Profiles','path','exclude_file_system','name_pattern',"command"] + [col for col in data.columns if col not in ['description', 'Category', 'Subcategory', 'YAML Name','collector','Profiles','path','exclude_file_system','name_pattern',"command"]])
data.replace(';', ',', regex=True, inplace=True)
# Convert strings to lists, remove duplicates from each list, then convert back to strings
data['Profiles'] = data['Profiles'].apply(lambda x: ', '.join(list(set(x.split(', ')))))
data.to_csv('UAC_artifacts_flatten.csv', index=False,sep="|")

print("\n----------\n\n[INFO] - Parsing successful. Output : UAC_artifacts_flatten.csv\n"    )
