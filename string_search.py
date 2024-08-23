import glob


TARGET_STRING = "You have ${"


files = glob.glob(r'C:\Users\yeshj\Desktop\folders\Pycharm\abiotic_korean\archive\pack\vanilla_extracted\0.9.0.11307\AbioticFactor\Content\**\*.*', recursive=True)


for file in files:
    if TARGET_STRING.lower() in file.lower():
        print(file)
print()

for file in files:
    with open(file, 'rb') as f:
        text = f.read().decode('ascii', errors='ignore')
        if TARGET_STRING in text:
            print(file)
