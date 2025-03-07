import glob
import json
import csv
import struct
import re
from common import *


is_Sign_ModularFacility_only = False


files = glob.glob(f'archive/offset_annotated/AbioticFactor/Content/Maps/**/*.*', recursive=True)

csv_file = open(f'out/signs_{VERSION}{"" if is_Sign_ModularFacility_only else "_all"}.csv', 'w', newline='')
writer = csv.writer(csv_file, delimiter='\t')

csv_file2 = open(f'out/signs_{VERSION}{"" if is_Sign_ModularFacility_only else "_all"}_no_offset.csv', 'w', newline='')
writer2 = csv.writer(csv_file2, delimiter='\t')


outer_trim_pattern = re.compile(r'_\d+$')

for file in files:
    map_name = file.split('/')[-1].split('\\')[-1].split('.')[0]

    with open(file) as f:
        objects = json.load(f)

    for data in objects:
        object_type = data.get('Type', '')
        if 'Properties' not in data:
            continue
        properties = data['Properties']

        # if object_type == 'Sign_ModularFacility_C':
        #     text = properties['DisplayText[5]']
        #     continue  # 아래 것만 바꾸면 됨
        # elif object_type == 'TextRenderComponent':
        if object_type == 'TextRenderComponent':
            outer = data['Outer']
            if (is_Sign_ModularFacility_only and not outer.startswith('Sign_ModularFacility')) or \
                    'Text' not in properties or \
                    'CultureInvariantString' not in properties['Text']:
                continue
            text = properties['Text']['CultureInvariantString']
        else:
            continue
            
        outer = re.sub(outer_trim_pattern, '', outer)

        if '!@#' not in text:
            continue

        text, text_start = text.split('!@#')
        if text == '' or text.isspace():
            continue
        text = visualize_whitespace(text)

        writer.writerow([
            f'AbioticFactor/Content/Maps/{map_name}.umap',
            outer,
            int(text_start) + 4,  # 텍스트 사이즈부터 시작하는데 메인 스크립트가 실제 텍스트 오프셋을 기대해서 4만큼 더하기
            '',
            text
        ])
        writer2.writerow([
            f'AbioticFactor/Content/Maps/{map_name}.umap',
            outer,
            '',
            text
        ])
