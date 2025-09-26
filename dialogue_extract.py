import glob
import json
import csv
from common import *


files = glob.glob(f'archive/offset_annotated/AbioticFactor/Content/Audio/**/*.*', recursive=True)

csv_file = open('out/dialogue_extra.csv', 'w', newline='')
writer = csv.writer(csv_file)

for file in files:
    with open(file) as f:
        data_list = json.load(f)

    for data in data_list:
        if data.get('Type', '') != 'DialogueWave':
            continue

        properties = data['Properties']
        if 'SpokenText' not in properties:
            continue

        context_mappings = properties['ContextMappings']
        assert len(context_mappings) == 1
        context_mapping = context_mappings[0]

        sound_wave = context_mapping['SoundWave']

        assert context_mapping['LocalizationKeyFormat'].startswith('{ContextHash}')

        writer.writerow([
            properties['LocalizationGUID'].replace('-', ''),
            sound_wave['ObjectPath'] if sound_wave else '',
            data['Name'],
        ])
