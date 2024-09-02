import glob
import re
import csv


VERSION = "0.9.0.11307"


files = glob.glob(f'archive/pack/vanilla_extracted_parsed/{VERSION}/AbioticFactor/Content/**/*.*', recursive=True)

pat = re.compile(r"\"Namespace\": \"(.*)\",\s+\"Key\": \"([0-9A-F]+)\",\s+\"SourceString\": \"(.+)\",")
writer = csv.writer(open(f'out/ftexts-{VERSION}.csv', 'w', newline=''), delimiter='\t')


rows = []

for file in files:
    with open(file) as f:
        content = f.read()
        find_index = 0
        while True:
            index = content.find('"Namespace"', find_index)
            if index == -1:
                break
            find_index = index + 1

            end_index = content.find('"LocalizedString"', index)
            if end_index == -1:
                continue

            matches = re.findall(pat, content[index:end_index])
            if not matches:
                continue

            assert len(matches) == 1
            ns, key, text = matches[0]

            ns_n_key = f'{ns}/{key}' if ns else key

            file_name = file.replace('\\', '/').replace(f'archive/pack/vanilla_extracted_parsed/{VERSION}/', '').replace('.json', '')
            rows.append((file_name, ns_n_key, text))

rows = list(dict.fromkeys(rows))
writer.writerows(rows)

