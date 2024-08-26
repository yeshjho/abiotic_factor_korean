import glob
import json
import csv


files = glob.glob('archive/pack/vanilla_extracted_parsed/0.9.0.11307/AbioticFactor/Content/Audio/**/*.*', recursive=True)

csv_file = open('out/dialogue_extra.csv', 'w', newline='')
writer = csv.writer(csv_file)

for file in files:
    with open(file) as f:
        data = json.load(f)

    data = data[0]
    if data.get('Type', '') != 'DialogueWave':
        continue

    properties = data['Properties']
    if 'SpokenText' not in properties:
        continue

    context_mappings = properties['ContextMappings']
    assert len(context_mappings) == 1
    context_mapping = context_mappings[0]
    assert context_mapping['LocalizationKeyFormat'] == '{ContextHash}'

    writer.writerow([
        properties['LocalizationGUID'].replace('-', ''),
        context_mapping['SoundWave']['ObjectPath'],
        data['Name'],
    ])
