import glob
import json
import csv
import struct

VERSION = "0.9.0.11307"


files = glob.glob(f'archive/pack/vanilla_extracted_parsed/{VERSION}/AbioticFactor/Content/Maps/**/*.*', recursive=True)

csv_file = open('out/signs.csv', 'w', newline='')
writer = csv.writer(csv_file)

for file in files:
    map_name = file.split('/')[-1].split('\\')[-1].split('.')[0]

    with open(file) as f:
        objects = json.load(f)

    for data in objects:
        if 'StartPosition' not in data:
            break

        object_type = data.get('Type', '')
        if object_type == 'Sign_ModularFacility_C':
            properties = data['Properties']
            text = properties['DisplayText']
            if text == '':
                continue

            text_start = int(data['StartPosition']) + 25
            with open(f'archive/pack/vanilla_extracted/{VERSION}/AbioticFactor/Content/Maps/{map_name}.umap', 'rb') as f:
                content = f.read()

            print(data['Name'], text_start)

            text_length = struct.unpack_from('<i', content, text_start)[0] - 1
            bin_text = struct.unpack_from(f'<{text_length}s', content, text_start)[0]

            writer.writerow([
                map_name,
                text_start,
                data['Name'],
                text,
                bin_text,
            ])
        elif object_type == '':
            pass
