import glob
import json
import csv
import struct
import re
from common import *


print_all_text_render_component = False
print_outer = True


def is_valid_outer(outer: str):
    if outer.startswith('Sign_ModularFacility') or outer.startswith('Sign_ModularDormitory'):
        return True
    if outer.startswith('TextRenderActor'):
        return True

    if outer.startswith('Trigger') or outer.startswith('Abiotic_TriggerVolume') or outer.startswith('TutorialTrigger'):
        return False
    if outer.startswith('CompendiumUnlock'):
        return False
    if outer.startswith('SimpleHatch_BP') or outer.startswith('Sliding'):
        return False
    if outer.startswith('StaticMeshActor'):
        return False

    raise RuntimeError(f'Add {outer} to is_valid_outer!')


files = glob.glob(f'archive/offset_annotated/AbioticFactor/Content/Maps/**/*.*', recursive=True)

csv_file = open(f'out/signs_{VERSION}{"_all" if print_all_text_render_component else ""}.csv', 'w', newline='')
writer = csv.writer(csv_file, delimiter='\t')

csv_file2 = open(f'out/signs_{VERSION}{"_all" if print_all_text_render_component else ""}_no_offset.csv', 'w', newline='')
writer_no_offset = csv.writer(csv_file2, delimiter='\t')


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
            if 'Text' not in properties or 'CultureInvariantString' not in properties['Text']:
                continue

            outer = data['Outer']
            if not print_all_text_render_component and not is_valid_outer(outer):
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

        row = [
            f'AbioticFactor/Content/Maps/{map_name}.umap',
            int(text_start) + 4,  # 텍스트 사이즈부터 시작하는데 메인 스크립트가 실제 텍스트 오프셋을 기대해서 4만큼 더하기
            outer,
            text
        ]
        if not print_outer:
            del row[2]

        writer.writerow(row)
        del row[1]  # remove offset
        writer_no_offset.writerow(row)
