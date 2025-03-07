from glob import glob
import json
from common import *


files = glob(f'archive/pack/vanilla_extracted_parsed/{VERSION}/AbioticFactor/**/*.*', recursive=True)

for file in files:
    with open(file) as f:
        data = json.load(f)

    data = data[0]
    if data.get('Type', '') == 'Texture2D':
        print(f"{data['Name']: <60}{file}")
