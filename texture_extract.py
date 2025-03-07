import glob
import json
import os
import subprocess
from common import *

# export 형식 png로 바꿨더니 색이 뿌옇게 나와서 CUE4Parse로 이주
"""
cwd = os.getcwd().replace('\\', '/')


files = glob.glob(f'archive/pack/vanilla_extracted_parsed/{VERSION}/AbioticFactor/Content/**/*.*', recursive=True)


for file in files:
    with open(file) as f:
        data = json.load(f)[0]

    if data['Type'] != 'Texture2D':
        continue

    path_normalized = file.replace('\\', '/')
    uasset_path = path_normalized.replace('vanilla_extracted_parsed', 'vanilla_extracted').replace('.json', '.uasset')

    exported_name = path_normalized.split('/')[-1].replace('.json', '.png')
    file_name = path_normalized.replace(f'archive/pack/vanilla_extracted_parsed/{VERSION}/', '').replace('.json', '.png').replace('/', '+')

    subprocess.run([f'{cwd}/tools/UE4-DDS-Tools-v0.6.1-Batch/_1_export_as_png.bat',
                    f'{cwd}/{uasset_path}'])
    os.rename(f'{cwd}/tools/UE4-DDS-Tools-v0.6.1-Batch/exported/{exported_name}', f'{cwd}/tools/UE4-DDS-Tools-v0.6.1-Batch/exported/{file_name}')
"""
