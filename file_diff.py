import glob


OLD_VERSION = "0.9.2.12333"
NEW_VERSION = "0.9.3.13049"


old_files = glob.glob(f'archive/pack/vanilla_extracted/{OLD_VERSION}/AbioticFactor/Content/**/*.*', recursive=True)
old_files_no_prefix = [old_file.replace(f'archive/pack/vanilla_extracted/{OLD_VERSION}/', '') for old_file in old_files]

new_files = glob.glob(f'archive/pack/vanilla_extracted/{NEW_VERSION}/AbioticFactor/Content/**/*.*', recursive=True)
new_files_no_prefix = [new_file.replace(f'archive/pack/vanilla_extracted/{NEW_VERSION}/', '') for new_file in new_files]


added_list = []
modified_list = []
removed_list = []

for old_file in old_files_no_prefix:
    if old_file not in new_files_no_prefix:
        print(f'Removed: {old_file}')
        removed_list.append(old_file)

for new_file in new_files_no_prefix:
    if new_file not in old_files_no_prefix:
        print(f'Added: {new_file}')
        added_list.append(new_file)
        continue

    with open(f'archive/pack/vanilla_extracted/{NEW_VERSION}/{new_file}', 'rb') as new:
        with open(f'archive/pack/vanilla_extracted/{OLD_VERSION}/{new_file}', 'rb') as old:
            if new.read() != old.read():
                modified_list.append(new_file)


print('\n'.join([f'Modified: {file}' for file in modified_list]))


with open(f'out/file_diff_{OLD_VERSION}_{NEW_VERSION}.txt', 'w') as out:
    out.write('\n'.join([f'Added: {file}' for file in added_list]))
    out.write('\n')
    out.write('\n'.join([f'Modified: {file}' for file in modified_list]))
    out.write('\n')
    out.write('\n'.join([f'Removed: {file}' for file in removed_list]))
