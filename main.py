import json
import csv
import os
import shutil
import subprocess
import struct
import glob
import pprint


"""
# 영어 원문 파일
data/en-[버전].json
구조: { 네임스페이스: { 키: 값 } }

# 번역 파일
data/ko-[버전].csv
헤더: 네임스페이스/키\t원문\t번역본

# 추가 번역 파일
data/ko-[버전]-extra.csv
헤더: 네임스페이스/키\t원문\t번역본

# 바이너리 덮어쓰는 파일
data/binary_override/[버전].csv
헤더: 파일 경로\t바이트 오프셋\t(무시)\t원문\t번역본
주의: \r, \n 일부러 \\r, \\n으로 바꿔둠. 되돌려서 넣어야 함.
주의: 바이트 오프셋은 실제 텍스트의 시작 오프셋임. 사이즈는 앞에서 찾아야 함.

# 이미지 덮어쓰는 파일
data/image/[버전]/이미지+까지+경로
"""


GAME_VERSION = "0.9.0.11307"
PATCH_VERSION = "0.9"


def visualize_whitespace(text: str):
    return text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def inline_whitespace(text: str):
    return text.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')


def build_pak():
    en_file = json.load(open(f'data/en-{GAME_VERSION}.json'))

    keys_nonexistent_in_en = []
    keys_missing_in_ko = []
    keys_not_translated = []
    original_not_matching = []

    translated_file = {}
    with (open(f'data/ko-{PATCH_VERSION}.csv', newline='') as f):
        reader = csv.reader(f, delimiter='\t')
        for namespace_n_key, original, translated in reader:
            namespace, key = namespace_n_key.split('/')

            if namespace not in en_file or key not in en_file[namespace]:
                keys_nonexistent_in_en.append(namespace_n_key)
                continue

            if original != en_file[namespace][key]:
                original_not_matching.append(
                    (namespace_n_key, visualize_whitespace(en_file[namespace][key]), visualize_whitespace(original))
                )

            if translated:
                if namespace not in translated_file:
                    translated_file[namespace] = {}
                translated_file[namespace][key] = translated
            else:
                keys_not_translated.append(namespace_n_key)

    for namespace, pairs in en_file.items():
        if namespace not in translated_file:
            for key in pairs.keys():
                keys_missing_in_ko.append(f'{namespace}/{key}')
            continue

        for key in pairs.keys():
            if ((namespace not in translated_file or key not in translated_file[namespace]) and
                    f'{namespace}/{key}' not in keys_not_translated):
                keys_missing_in_ko.append(f'{namespace}/{key}')


    if keys_nonexistent_in_en:
        print('[경고] 다음 키들은 영문 파일에 존재하지 않습니다. 무시됩니다.')
        print(keys_nonexistent_in_en)
        print()
    if keys_missing_in_ko:
        print('[경고] 다음 키들은 번역본에 존재하지 않습니다. 원문이 출력됩니다.')
        print(keys_missing_in_ko)
        print()
    if keys_not_translated:
        print('[경고] 다음 키들은 번역본이 없습니다. 원문이 출력됩니다.')
        print(keys_not_translated)
        print()
    if original_not_matching:
        print('[경고] 다음 항목들은 영문 파일과 번역본의 원문에 차이가 있습니다.')
        print(original_not_matching)
        print()


    with (open(f'data/ko-{PATCH_VERSION}-extra.csv', newline='') as f):
        reader = csv.reader(f, delimiter='\t')
        for namespace_n_key, original, translated in reader:
            split = namespace_n_key.split('/')
            namespace = ''
            if len(split) == 2:
                namespace, key = split
            else:
                key = namespace_n_key

            if namespace not in translated_file:
                translated_file[namespace] = {}
            translated_file[namespace][key] = translated if translated else original

            if namespace not in en_file:
                en_file[namespace] = {}
            en_file[namespace][key] = original


    with open(f'out/en-{PATCH_VERSION}.json', 'w') as f:
        json.dump(en_file, f, ensure_ascii=False, indent=2)
    with open(f'out/ko-{PATCH_VERSION}.json', 'w') as f:
        json.dump(translated_file, f, ensure_ascii=False, indent=2)

    shutil.rmtree('out/pakchunk0-Windows_P/', ignore_errors=True)
    shutil.copytree('pak_template', 'out/pakchunk0-Windows_P')

    shutil.copy2(f'out/en-{PATCH_VERSION}.json', 'tools/LocRes-Builder-v0.1.2/out/Game/en.json')
    shutil.copy2(f'out/ko-{PATCH_VERSION}.json', 'tools/LocRes-Builder-v0.1.2/out/Game/ko.json')

    with open('tools/LocRes-Builder-v0.1.2/out/Game/locmeta.json', 'r+') as f:
        meta = json.load(f)
        if 'ko' not in meta['local_languages']:
            meta['local_languages'].append('ko')
            meta['local_languages'].sort()
        f.seek(0)
        json.dump(meta, f, indent=2)
        f.truncate()

    subprocess.run([f'{cwd}/tools/LocRes-Builder-v0.1.2/convert.bat',
                    f'{cwd}/tools/LocRes-Builder-v0.1.2/out/Game/locmeta.json'])

    shutil.copy2('tools/LocRes-Builder-v0.1.2/out/Game/Game.locmeta',
                 'out/pakchunk0-Windows_P/AbioticFactor/Content/Localization/Game/Game.locmeta')
    shutil.copy2('tools/LocRes-Builder-v0.1.2/out/Game/ko/Game.locres',
                 'out/pakchunk0-Windows_P/AbioticFactor/Content/Localization/Game/ko/Game.locres')

    print('pak 파일 생성 중...')
    subprocess.run([f'{cwd}/tools/repak_cli-x86_64-pc-windows-msvc/repak.exe',
                    f'pack',
                    f'{cwd}/out/pakchunk0-Windows_P'])

    return [
        '# 영문 파일에 존재하지 않는데 번역본에 존재하는 키',
        pprint.pformat(keys_nonexistent_in_en, indent=4),
        '',
        '# 영문판에 존재하는데 번역본에 존재하지 않는 키',
        pprint.pformat(keys_missing_in_ko, indent=4),
        '',
        '# 번역이 되지 않은 키',
        pprint.pformat(keys_not_translated, indent=4),
        '',
        '# 영문 파일의 값과 번역본의 원문이 동일하지 않은 키 (키, 영문 파일 값, 번역본 원문)',
        pprint.pformat(original_not_matching, indent=4),
        ''
    ]


def build_io_store():
    shutil.rmtree('out/pakchunk0-Windows_P/', ignore_errors=True)
    shutil.copytree('ucas_template', 'out/pakchunk0-Windows_P')


    output = []
    output += build_binary_overrides()
    output += build_image_overrides()


    if not os.path.exists(f'archive/manifest/{GAME_VERSION}.manifest'):
        print('manifest 파일을 찾지 못하여 생성합니다. 시간이 오래 걸릴 수 있습니다...')
        subprocess.run([f'{cwd}/tools/UEcastoc-1.0.1/cpp/main.exe',
                        f'manifest',
                        f'{cwd}/archive/pack/vanilla/pakchunk0-Windows-{GAME_VERSION}.utoc',
                        f'{cwd}/archive/pack/vanilla/pakchunk0-Windows-{GAME_VERSION}.ucas',
                        f'{cwd}/archive/manifest/{GAME_VERSION}.manifest'])

    print('IOStore 파일 생성 중...')
    subprocess.run([f'{cwd}/tools/UEcastoc-1.0.1/cpp/main.exe',
                    f'pack',
                    f'{cwd}/out/pakchunk0-Windows_P',
                    f'{cwd}/archive/manifest/{GAME_VERSION}.manifest',
                    f'{cwd}/out/pakchunk0-Windows_P',
                    f'None'])

    return output


def build_binary_overrides():
    SIZE_OFFSET_MAP = {
        'AbioticFactor/Content/Blueprints/DataTables/DT_Compendium.uasset': 0x2753
    }

    pairs_per_file = {}
    with open(f'data/binary_override/{PATCH_VERSION}.csv', newline='') as f:
        reader = csv.reader(f, delimiter='\t')
        for file, byte_offset, *_, translated in reader:
            if file not in pairs_per_file:
                pairs_per_file[file] = []
            pairs_per_file[file].append((byte_offset, translated))

    no_size_offset_files = []

    for file, pairs in pairs_per_file.items():
        with open(f'archive/pack/vanilla_extracted/{GAME_VERSION}/{file}', 'rb') as f:
            data = f.read()
        total_offset = 0

        for byte_offset, translated in sorted(pairs, key=lambda x: x[0]):  # 오프셋 순으로 정렬
            byte_offset = int(byte_offset)
            translated = inline_whitespace(translated)
            original_length = struct.unpack_from('<i', data, total_offset + byte_offset - 4)[0]
            original_length_bytes = original_length if original_length > 0 else -original_length * 2

            is_translated_ascii = translated.isascii()
            new_length = (len(translated) + 1) * (1 if is_translated_ascii else -1)
            new_length_bytes = (len(translated) + 1) * (1 if is_translated_ascii else 2)

            data = (data[:total_offset + byte_offset - 4] + struct.pack('<i', new_length) +
                    ((translated.encode('ascii') + b'\x00') if is_translated_ascii else
                     translated.encode('utf-16')[2:] + b'\x00\x00') +
                    data[total_offset + byte_offset + original_length_bytes:])

            total_offset += new_length_bytes - original_length_bytes

        if file in SIZE_OFFSET_MAP:
            size_offset = SIZE_OFFSET_MAP[file]
            expected_read_size = struct.unpack_from('<i', data, size_offset)[0]
            data = data[:size_offset] + struct.pack('<i', expected_read_size + total_offset) + data[size_offset + 4:]
        else:
            no_size_offset_files.append(file)

        os.makedirs('/'.join(f'out/pakchunk0-Windows_P/{file}'.split('/')[:-1]), exist_ok=True)
        with open(f'out/pakchunk0-Windows_P/{file}', 'wb') as f:
            f.write(data)

    if no_size_offset_files:
        print('[경고] 다음 파일들의 사이즈 오프셋 데이터가 없어 파일 사이즈를 수정하지 못했습니다.')
        print(no_size_offset_files)


    return [
        '# 사이즈 오프셋 데이터가 없는 파일',
        pprint.pformat(no_size_offset_files, indent=4),
        ''
    ]


def build_image_overrides():
    for file in glob.glob(f'data/image/{PATCH_VERSION}/*.*'):
        file = file.split('/')[-1].split('\\')[-1]
        directory_n_file = file.replace('+', '/')
        *directory, file_name = directory_n_file.split('/')
        directory = '/'.join(directory)
        file_name = file_name.split('.')[0]
        wo_extension, _ = directory_n_file.split('.')

        os.makedirs(f'out/pakchunk0-Windows_P/{directory}', exist_ok=True)

        with open('tools/UE4-DDS-Tools-v0.6.1-Batch/src/_file_path_.txt', 'w') as f:
            f.write(f'{cwd}/archive/pack/vanilla_extracted/{GAME_VERSION}/{wo_extension}.uasset')
        subprocess.run([f'{cwd}/tools/UE4-DDS-Tools-v0.6.1-Batch/_3_inject.bat',
                        f'{cwd}/data/image/{PATCH_VERSION}/{file}'])
        
        shutil.move(f'tools/UE4-DDS-Tools-v0.6.1-Batch/injected/{file_name}.uasset',
                    f'out/pakchunk0-Windows_P/{wo_extension}.uasset')
        if os.path.exists(f'tools/UE4-DDS-Tools-v0.6.1-Batch/injected/{file_name}.ubulk'):
            shutil.move(f'tools/UE4-DDS-Tools-v0.6.1-Batch/injected/{file_name}.ubulk',
                        f'out/pakchunk0-Windows_P/{wo_extension}.ubulk')

    return []


def main():
    output = []

    output += build_io_store()  # 필요없는 pak 파일을 생성하기 때문에 먼저 호출한 후 뒤에 pak 파일을 덮어쓴다
    output += build_pak()

    with open(f'out/report-{PATCH_VERSION}.txt', 'w') as f:
        f.write('\n'.join(output))

    print(f'작업 완료. out/report-{PATCH_VERSION}.txt에 리포트를 생성했습니다.')


if __name__ == '__main__':
    cwd = os.getcwd().replace('\\', '/')
    main()
