import csv
import json

result = {}
with open('out/Game.csv', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        key, value, *_ = row
        table, real_key = key.split('/')
        if table not in result:
            result[table] = {}
        result[table][real_key] = value

with open('out/Game.json', 'w') as f:
    json.dump(result, f, indent=2)
