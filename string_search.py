import glob


# TARGET_STRING = b'\xb1\x02\x47\xaf'
TARGET_STRING = "You're part of the Research Team ...[4.1]I'm sorry"

files = glob.glob('archive/pack/vanilla_extracted/0.9.0.11307/AbioticFactor/Content/Audio/**/*.*', recursive=True)


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
