import glob

VERSION = "0.9.1.11753"

# TARGET_STRING = b'\xb1\x02\x47\xaf'
TARGET_STRING = "Nothing Urgent"

files = glob.glob(f'archive/pack/vanilla_extracted/{VERSION}/AbioticFactor/Content/Blueprints/Widgets/W_Inventory_HealthPanel.*', recursive=True)


MODE = ('NORMAL', 'SPECIFIC', 'HEX')[1]

if MODE == 'NORMAL':
    for file in files:
        if TARGET_STRING.lower() in file.lower():
            print(file)
    print()

    for file in files:
        with open(file, 'rb') as f:
            text = f.read().decode('ascii', errors='ignore')
            if TARGET_STRING in text:
                print(file)
elif MODE == 'SPECIFIC':
    for file in files:
        with open(file, 'rb') as f:
            text = f.read().decode('ascii', errors='ignore')
            index = text.find(TARGET_STRING)
            if index >= 0:
                print(text[index - 50:index+100])
elif MODE == 'HEX':
    for file in files:
        with open(file, 'rb') as f:
            text = f.read()
            if TARGET_STRING in text:
                print(file)
