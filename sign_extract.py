import glob
import json
import csv
import struct

VERSION = "0.9.0.11307"


files = glob.glob(f'archive/offset_annotated/**/*.*', recursive=True)

csv_file = open('out/signs.csv', 'w', newline='')
writer = csv.writer(csv_file, delimiter='\t')

for file in files:
    map_name = file.split('/')[-1].split('\\')[-1].split('.')[0]

    with open(file) as f:
        objects = json.load(f)

    for data in objects:
        object_type = data.get('Type', '')
        if 'Properties' not in data:
            continue
        properties = data['Properties']

        if object_type == 'Sign_ModularFacility_C':
            text = properties['DisplayText[5]']
            continue  # 아래 것만 바꾸면 됨
        elif object_type == 'TextRenderComponent':
            if 'Text' not in properties or 'CultureInvariantString' not in properties['Text']:
                continue
            text = properties['Text']['CultureInvariantString']
        else:
            continue

        if '!@#' not in text:
            continue

        text, text_start = text.split('!@#')
        if text == '' or text.isspace():
            continue

        writer.writerow([
            f'AbioticFactor/Content/Maps/{map_name}.umap',
            int(text_start) + 4,  # 텍스트 사이즈부터 시작하는데 메인 스크립트가 실제 텍스트 오프셋을 기대해서 4만큼 더하기
            '',
            text
        ])
