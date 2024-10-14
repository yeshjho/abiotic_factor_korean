import re
import glob
import csv

files = glob.glob(f'archive/offset_annotated/AbioticFactor/Content/Blueprints/**/*.*', recursive=True)

csv_file = open('out/general_text_extracted.csv', 'w', newline='')
writer = csv.writer(csv_file, delimiter='\t')


pat = re.compile(r': "(.+)!@#(\d+)"')

for file in files:
    with open(file) as f:
        for mat in re.findall(pat, f.read()):
            writer.writerow([
                file.replace('\\', '/').replace('archive/offset_annotated/', '').replace('.json', '.uasset'),
                int(mat[1]) + 4,  # 텍스트 사이즈부터 시작하는데 메인 스크립트가 실제 텍스트 오프셋을 기대해서 4만큼 더하기
                '',
                mat[0]
            ])
