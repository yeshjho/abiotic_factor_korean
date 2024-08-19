import json
import os
import re
import shutil
import sys
from glob import glob
from pprint import pprint


OLD_VERSION = "0.9.0"
NEW_VERSION = "0.9.0.11307"

DID_GENERATE_TRANSLATION = True


if __name__ == "__main__":
    ko_old = json.load(open(f'data/ko-{OLD_VERSION}.json'))
    en_old = json.load(open(f'data/en-{OLD_VERSION}.json'))
    en_new = json.load(open(f'data/en-{NEW_VERSION}.json'))
    ja_new = json.load(open(f'data/ja-{NEW_VERSION}.json'))

    if not DID_GENERATE_TRANSLATION:
        # 바뀐 데이터 키 및 값 수집
        diff_keys = {}

        for data_table, entries in en_new.items():
            for key, value in entries.items():
                if data_table in ko_old and key in ko_old[data_table] and key not in en_old[data_table]:
                    print(data_table, key, value)

                if data_table not in ko_old or \
                        key not in ko_old[data_table] or \
                        (key in en_old[data_table] and en_old[data_table][key] != en_new[data_table][key]):
                    if data_table not in diff_keys:
                        diff_keys[data_table] = []
                    diff_keys[data_table].append(key)

        pprint(diff_keys)


        class DiffData:
            def __init__(self):
                self.keys = ['', '', '', '', '', '', '']
                self.lines = ['', '', '', '', '', '', '']
                self.index = 0
                self.cur_length = 0


        ja_diff = DiffData()
        en_diff = DiffData()

        for data_table, entries in diff_keys.items():
            for key in entries:
                if data_table in ja_new and key in ja_new[data_table]:
                    value = ja_new[data_table][key]
                    is_ja = True
                else:
                    value = en_new[data_table][key]
                    is_ja = False

                value = value.replace('\n', '\\n').replace('\r', '\\r')

                line_length = len(value) + 2  # Plus 4 for \r\n\r\n
                diff_to_use = ja_diff if is_ja else en_diff
                if diff_to_use.cur_length + line_length >= 100000:
                    diff_to_use.index += 1
                    diff_to_use.cur_length = line_length
                else:
                    diff_to_use.cur_length += line_length
                diff_to_use.lines[diff_to_use.index] += value + '\n\n'
                diff_to_use.keys[diff_to_use.index] += data_table + '/' + key + '\n\n'

        print(ja_diff.index, en_diff.index)


        def write_diff(diff, name):
            for i, (key, line) in enumerate(zip(diff.keys, diff.lines)):
                if line == '':
                    break
                with open(f'diff/diff-{OLD_VERSION}-{NEW_VERSION}-{name}-{i}.txt', 'w') as f:
                    f.write(line)
                with open(f'diff/diff-{OLD_VERSION}-{NEW_VERSION}-keys-{name}-{i}.txt', 'w') as f:
                    f.write(key)
                with open(f'diff/diff-{OLD_VERSION}-{NEW_VERSION}-ko-{name}-{i}.txt', 'w') as f:
                    f.write('')

        write_diff(ja_diff, "ja")
        write_diff(en_diff, "en")
    else:
        # 새 한국어 파일 생성
        def write_korean(key_file_name, original_file_name, ko_file_name):
            keys = open(key_file_name).read().splitlines()
            original = open(original_file_name).read().splitlines()
            ko = open(ko_file_name).read().splitlines()

            assert len(keys) == len(ko) == len(original)

            should_blank = False
            for key, original_value, value in zip(keys, original, ko):
                assert (should_blank == (value == '')) and (should_blank == (key == ''))

                if should_blank:
                    should_blank = not should_blank
                    continue

                for preserve in re.findall(r'\[[\d\.]+?\]', original_value) + re.findall(r'{.+?}', original_value):
                    if preserve not in value:
                        print(f'missing\n{key}\n{original_value}\n{value}\n{preserve}')
                        assert False

                for preserve in re.findall(r'\[[\d\.]+?\]', value) + re.findall(r'{.+?}', value):
                    if preserve not in original_value:
                        print(f'excessive\n{key}\n{original_value}\n{value}\n{preserve}')
                        assert False

                table, entry = key.split('/')
                if table not in ko_old:
                    ko_old[table] = {}
                ko_old[table][entry] = (value.replace('n\\n\\n', '\\n\\n')  # weird deepl error
                                        .replace('\\n', '\n').replace('\\r', '\r'))

                should_blank = not should_blank

        key_files = [file for file in glob('diff/*.txt') if f'{OLD_VERSION}-{NEW_VERSION}-keys' in file]
        for key_file in key_files:
            write_korean(key_file, key_file.replace('keys-', ''), key_file.replace('keys', 'ko'))

        with open(f'out/ko-{NEW_VERSION}.json', 'w') as f:
            json.dump(ko_old, f, ensure_ascii=False, indent=2)

        # 영어 판에 없는 키 제거
        ko_new = json.load(open(f'out/ko-{NEW_VERSION}.json'))

        tables_to_delete = []
        keys_to_delete = {}

        for data_table, entries in ko_new.items():
            if data_table not in en_new:
                tables_to_delete.append(data_table)
                continue

            for key, value in entries.items():
                if key not in en_new[data_table]:
                    if data_table not in keys_to_delete:
                        keys_to_delete[data_table] = []
                    keys_to_delete[data_table].append(key)

        pprint(tables_to_delete)
        pprint(keys_to_delete)

        for table in tables_to_delete:
            del ko_new[table]

        for table, keys in keys_to_delete.items():
            for key in keys:
                del ko_new[table][key]

        with open(f'out/ko-{NEW_VERSION}.json', 'w') as f:
            json.dump(ko_new, f, ensure_ascii=False, indent=2)

        # json을 locres 파일로 변환
        cwd = os.getcwd().replace('\\', '/')

        shutil.rmtree('out/pakchunk0-Windows_P/', ignore_errors=True)
        os.mkdir('out/pakchunk0-Windows_P/')
        shutil.copytree('pak_template/AbioticFactor/', 'out/pakchunk0-Windows_P/AbioticFactor/')

        shutil.copy2(f'data/en-{NEW_VERSION}.json', 'tools/LocRes-Builder-v0.1.2/out/Game/en.json')
        shutil.copy2(f'out/ko-{NEW_VERSION}.json', 'tools/LocRes-Builder-v0.1.2/out/Game/ja.json')

        with open('tools/LocRes-Builder-v0.1.2/out/Game/locmeta.json', 'r+') as f:
            meta = json.load(f)
            meta['local_languages'] = ['ja']
            json.dump(meta, f, indent=2)

        os.system(f'"{cwd}/tools/LocRes-Builder-v0.1.2/convert.bat" '
                  f'{cwd}/tools/LocRes-Builder-v0.1.2/out/Game/locmeta.json')

        shutil.copy2('tools/LocRes-Builder-v0.1.2/out/Game/ja/Game.locres',
                     'out/pakchunk0-Windows_P/AbioticFactor/Content/Localization/Game/ja/Game.locres')

        # 엔진 번역 파일
        shutil.copy2(f'data/engine-en.json', 'tools/LocRes-Builder-v0.1.2/out/Engine/en.json')
        shutil.copy2(f'out/engine-ko.json', 'tools/LocRes-Builder-v0.1.2/out/Engine/ja.json')

        with open('tools/LocRes-Builder-v0.1.2/out/Engine/locmeta.json', 'r+') as f:
            meta = json.load(f)
            meta['local_languages'] = ['ja']
            json.dump(meta, f, indent=2)

        os.system(f'"{cwd}/tools/LocRes-Builder-v0.1.2/convert.bat" '
                  f'{cwd}/tools/LocRes-Builder-v0.1.2/out/Engine/locmeta.json')

        shutil.copy2('tools/LocRes-Builder-v0.1.2/out/Engine/ja/Engine.locres',
                     'out/pakchunk0-Windows_P/Engine/Content/Localization/Engine/ja/Engine.locres')

        # 모든 작업 완료. 패킹
        os.system(f'"{cwd}/tools/repak_cli-x86_64-pc-windows-msvc/repak.exe" '
                  f'pack {cwd}/out/pakchunk0-Windows_P')
