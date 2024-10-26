import json
import csv


OLD_VERSION = "0.9.2.12106"
NEW_VERSION = "0.9.2.12333"

en_old = json.load(open(f'data/en-{OLD_VERSION}.json'))
en_new = json.load(open(f'data/en-{NEW_VERSION}.json'))


csv_file = open(f'out/diff-{OLD_VERSION}-{NEW_VERSION}.csv', 'w', newline='')
writer = csv.writer(csv_file, delimiter='\t')

for data_table, entries in en_new.items():
    if data_table not in en_old:
        for key, value in entries.items():
            writer.writerow([f'{data_table}/{key}', value, ''])
        continue

    for key, value in entries.items():
        if key not in en_old[data_table]:
            writer.writerow([f'{data_table}/{key}', value, ''])
        elif value != en_old[data_table][key]:
            writer.writerow([f'{data_table}/{key}', value, en_old[data_table][key]])

for data_table, entries in en_old.items():
    if data_table not in en_new:
        for key, value in entries.items():
            writer.writerow([f'{data_table}/{key}', '', value])
        continue

    for key, value in entries.items():
        if key not in en_new[data_table]:
            writer.writerow([f'{data_table}/{key}', '', value])
