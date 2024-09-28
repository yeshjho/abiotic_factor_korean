import glob

VERSION = "0.9.1.11753"

# TARGET_STRING = b'\xb1\x02\x47\xaf'
TARGET_STRING = "Your previous corpse loot bag"

files = glob.glob(f'archive/pack/vanilla_extracted/{VERSION}/AbioticFactor/Content/**/*.*', recursive=True)


if True:
    for file in files:
        if TARGET_STRING.lower() in file.lower():
            print(file)
    print()

    for file in files:
        with open(file, 'rb') as f:
            text = f.read().decode('ascii', errors='ignore')
            if TARGET_STRING in text:
                print(file)
else:
    for file in files:
        with open(file, 'rb') as f:
            text = f.read()
            if TARGET_STRING in text:
                print(file)
