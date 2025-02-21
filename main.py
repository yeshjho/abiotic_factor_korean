import json
import csv
import os
import shutil
import subprocess
import struct
import glob
import pprint
import bisect


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
헤더: 파일 경로\t바이트 오프셋\t엑스트라\t원문\t번역본
엑스트라가 NO_FSTRING이면 fstring 치환이 아닌, 일반 바이너리 덮어쓰기를 수행.
원문은 엑스트라가 NO_FSTRING일 때만 필요.
주의: \r, \n 일부러 \\r, \\n으로 바꿔둠. 되돌려서 넣어야 함.
주의: 바이트 오프셋은 실제 텍스트의 시작 오프셋임. 사이즈는 앞에서 찾아야 함.

# 이미지 덮어쓰는 파일
data/image/[버전]/이미지+까지+경로
"""


GAME_VERSION = "0.9.3.13049"
PATCH_VERSION = "1.2.1"


def visualize_whitespace(text: str):
    return text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def inline_whitespace(text: str):
    return text.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')


def parse_offset(offset: str):
    if offset.startswith('0x'):
        return int(offset[2:], 16)
    elif offset.endswith('h'):
        return int(offset[:-1], 16)
    else:
        return int(offset)


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

            if original.strip() != en_file[namespace][key].strip():
                original_not_matching.append(
                    (namespace_n_key, visualize_whitespace(en_file[namespace][key]), visualize_whitespace(original))
                )

            if translated:
                if namespace not in translated_file:
                    translated_file[namespace] = {}
                translated_file[namespace][key] = inline_whitespace(translated)
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


    extra = []
    with (open(f'data/ko-extra-{PATCH_VERSION}.csv', newline='') as f):
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            extra.append(row)
    extra.append(['6752A04747EF09B5E7C078AD8860A0EC', '{originaltext} | EARLY ACCESS',
                  f'{{originaltext}} | EARLY ACCESS | 한국어 패치 v{PATCH_VERSION}'])

    for row in extra:
        if len(row) != 3:
            continue

        namespace_n_key, original, translated = row
        split = namespace_n_key.split('/')
        namespace = ''
        if len(split) == 2:
            namespace, key = split
        else:
            key = namespace_n_key

        if namespace not in translated_file:
            translated_file[namespace] = {}
        translated_file[namespace][key] = inline_whitespace(translated) if translated else original

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
        '[\n' + '\n'.join([f'  (\n    {repr(k)},\n    {repr(org)},\n    {repr(mis)}\n  ),'
                           for k, org, mis in original_not_matching]) + '\n]'
        ''
    ]


def build_io_store(skip_binary_overrides: bool, skip_images: bool):
    if skip_binary_overrides and skip_images:
        return []

    shutil.rmtree('out/pakchunk0-Windows_P/', ignore_errors=True)
    shutil.copytree('ucas_template', 'out/pakchunk0-Windows_P')


    output = []
    if not skip_binary_overrides:
        output += build_binary_overrides()
    if not skip_images:
        output += build_image_overrides()

    print('IOStore 파일 생성 중...')
    subprocess.run([f'{cwd}/tools/UnrealReZen_V01/UnrealReZen.exe',
                    f'--content-path',
                    f'{cwd}/out/pakchunk0-Windows_P',
                    f'--engine-version',
                    f'GAME_UE5_4',
                    f'--game-dir',
                    f'{cwd}/archive/pack/vanilla/{GAME_VERSION}',
                    f'--output-path',
                    f'{cwd}/out/pakchunk0-Windows_P.utoc'])
    if os.path.exists(f'oo2core_9_win64.dll'):
        os.remove('oo2core_9_win64.dll')

    return output


def overwrite_fstring(data, offset, new_text, does_offset_points_size):
    size_offset = offset - (0 if does_offset_points_size else 4)
    original_length = struct.unpack_from('<i', data, size_offset)[0]
    original_length_bytes = original_length if original_length > 0 else -original_length * 2

    is_translated_ascii = new_text.isascii()
    new_length = (len(new_text) + 1) * (1 if is_translated_ascii else -1)
    new_length_bytes = (len(new_text) + 1) * (1 if is_translated_ascii else 2)
    new_text = (new_text.encode('ascii') + b'\x00') if is_translated_ascii \
        else new_text.encode('utf-16')[2:] + b'\x00\x00'

    data[size_offset:size_offset + 4] = bytearray(struct.pack('<i', new_length))
    data[size_offset + 4:size_offset + 4 + original_length_bytes] = bytearray(new_text)

    return data, original_length_bytes, new_length_bytes


def datatable_override(file, data, pairs):
    size_offset_map = {
        'AbioticFactor/Content/Blueprints/DataTables/DT_Compendium.uasset': 0x2e60
    }

    byte_difference = 0
    for byte_offset, extra, original, translated in pairs:
        offset_to_use = byte_offset + byte_difference
        if extra == "NO_FSTRING":
            overwrite_data = bytearray.fromhex(translated)
            original_length_bytes = len(bytearray.fromhex(original))
            data[offset_to_use:offset_to_use + original_length_bytes] = overwrite_data
            new_length_bytes = len(overwrite_data)
        else:
            data, original_length_bytes, new_length_bytes = overwrite_fstring(data, offset_to_use, translated, False)
        byte_difference += new_length_bytes - original_length_bytes

    if file in size_offset_map:
        size_offset = size_offset_map[file]
        expected_read_size = struct.unpack_from('<i', data, size_offset)[0]
        data[size_offset:size_offset + 4] = bytearray(struct.pack('<i', expected_read_size + byte_difference))
        return True, data
    else:
        return False, data


def default_uobject_override(file, data, pairs):
    map_entry_size = 72

    header_size, map_offset, entries_offset = struct.unpack_from('<xxxxIxxxxxxxxxxxxxxxxxxxxxxxxii', data)
    map_entry_count = (entries_offset - map_offset) // map_entry_size

    class MapEntry:
        def __init__(self, index, offset, size):
            self.index = index
            self.offset = offset
            self.size = size

            self.new_offset = offset
            self.new_size = size

    map_entries = []
    for i in range(map_entry_count - 1):
        entry_offset, entry_size = struct.unpack_from('<QQ', data, map_offset + i * map_entry_size)
        map_entries.append(MapEntry(i, header_size + entry_offset, entry_size))

    entry_offset, entry_size = struct.unpack_from('<QQ', data, map_offset + (map_entry_count - 1) * map_entry_size)
    map_entries.append(MapEntry(map_entry_count - 1, header_size + entry_offset, entry_size))
    last_entry_address = header_size + entry_offset + entry_size - 1

    map_entries.sort(key=lambda x: x.offset)  # 이미 오프셋 기준으로 정렬돼 있지만 혹시 모르니

    total_byte_difference = 0
    total_byte_difference_outside = 0
    prev_entry_index = 0
    for byte_offset, extra, original, translated in pairs:
        if byte_offset > last_entry_address:
            offset_to_use = byte_offset + total_byte_difference + total_byte_difference_outside
            if extra == "NO_FSTRING":
                overwrite_data = bytearray.fromhex(translated)
                original_length_bytes = len(bytearray.fromhex(original))
                data[offset_to_use:offset_to_use + original_length_bytes] = overwrite_data
                new_length_bytes = len(overwrite_data)
            else:
                data, original_length_bytes, new_length_bytes = \
                    overwrite_fstring(data, offset_to_use, translated, False)
            total_byte_difference_outside += new_length_bytes - original_length_bytes
            continue

        entry_index = bisect.bisect_left(map_entries, byte_offset, key=lambda x: x.offset)
        for i in range(prev_entry_index, entry_index):
            map_entries[i].new_offset += total_byte_difference
        prev_entry_index = entry_index

        offset_to_use = byte_offset + total_byte_difference
        if extra == "NO_FSTRING":
            overwrite_data = bytearray.fromhex(translated)
            original_length_bytes = len(bytearray.fromhex(original))
            data[offset_to_use:offset_to_use + original_length_bytes] = overwrite_data
            new_length_bytes = len(overwrite_data)
        else:
            data, original_length_bytes, new_length_bytes = overwrite_fstring(data, offset_to_use, translated, False)
        size_difference = new_length_bytes - original_length_bytes
        total_byte_difference += size_difference
        map_entries[entry_index - 1].new_size += size_difference

    for i in range(prev_entry_index, map_entry_count):
        map_entries[i].new_offset += total_byte_difference

    for map_entry in map_entries:
        offset = map_offset + map_entry.index * map_entry_size
        data[offset:offset + 16] = bytearray(struct.pack('<QQ', map_entry.new_offset - header_size, map_entry.new_size))

    return True, data



def build_binary_overrides():
    file_overriders = [
        (lambda x: any([e in x for e in ('DT_Compendium',)]), datatable_override),
        (lambda x: True, default_uobject_override),
    ]

    pairs_per_file = {}
    with open(f'data/binary_override/{PATCH_VERSION}.csv', newline='') as f:
        reader = csv.reader(f, delimiter='\t')
        for file, byte_offset, extra, original, translated in reader:
            if file not in pairs_per_file:
                pairs_per_file[file] = []
            pairs_per_file[file].append((byte_offset, extra, original, translated))

    files_no_fixes = []

    for file, pairs in pairs_per_file.items():
        pairs = [(parse_offset(byte_offset), extra, original, inline_whitespace(translated))
                 for byte_offset, extra, original, translated in pairs]
        pairs.sort(key=lambda x: x[0])  # 오프셋 순으로 정렬

        with open(f'archive/pack/vanilla_extracted/{GAME_VERSION}/{file}', 'rb') as f:
            data = bytearray(f.read())

        for pred, overrider in file_overriders:
            if pred(file):
                did_success, data = overrider(file, data, pairs)
                if not did_success:
                    files_no_fixes.append(file)
                break

        os.makedirs('/'.join(f'out/pakchunk0-Windows_P/{file}'.split('/')[:-1]), exist_ok=True)
        with open(f'out/pakchunk0-Windows_P/{file}', 'wb') as f:
            f.write(bytes(data))

    if files_no_fixes:
        print('[경고] 다음 파일들의 후처리에 실패했습니다. 게임 실행 시 에러가 날 수 있습니다.')
        print(files_no_fixes)


    return [
        '# 후처리에 실패한 파일',
        pprint.pformat(files_no_fixes, indent=4),
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
    SKIP_PAK = False
    SKIP_BINARY_OVERRIDES = False
    SKIP_IMAGES = False

    if os.path.exists('out/pakchunk0-Windows_P.pak'):
        os.remove('out/pakchunk0-Windows_P.pak')
    if os.path.exists('out/pakchunk0-Windows_P.utoc'):
        os.remove('out/pakchunk0-Windows_P.utoc')
    if os.path.exists('out/pakchunk0-Windows_P.ucas'):
        os.remove('out/pakchunk0-Windows_P.ucas')

    output = []

    output += build_io_store(SKIP_BINARY_OVERRIDES, SKIP_IMAGES)  # 필요없는 pak 파일을 생성하기 때문에 먼저 호출한 후 뒤에 pak 파일을 덮어쓴다
    if not SKIP_PAK:
        output += build_pak()

    pak_out_dir = f'out/abiotic_korean_{GAME_VERSION}_{PATCH_VERSION}/AbioticFactor/Content/Paks'
    shutil.rmtree(f'out/abiotic_korean_{GAME_VERSION}_{PATCH_VERSION}/', ignore_errors=True)
    shutil.copytree('patch_template', f'out/abiotic_korean_{GAME_VERSION}_{PATCH_VERSION}')
    if os.path.exists('out/pakchunk0-Windows_P.pak'):
        shutil.move('out/pakchunk0-Windows_P.pak', f'{pak_out_dir}/pakchunk0-Windows_P.pak')
    if os.path.exists('out/pakchunk0-Windows_P.utoc'):
        shutil.move('out/pakchunk0-Windows_P.utoc', f'{pak_out_dir}/pakchunk0-Windows_P.utoc')
    if os.path.exists('out/pakchunk0-Windows_P.ucas'):
        shutil.move('out/pakchunk0-Windows_P.ucas', f'{pak_out_dir}/pakchunk0-Windows_P.ucas')
    shutil.make_archive(f'out/abiotic_korean_{GAME_VERSION}_{PATCH_VERSION}',
                        'zip',
                        f'out/abiotic_korean_{GAME_VERSION}_{PATCH_VERSION}')

    with open(f'out/report-{PATCH_VERSION}.txt', 'w') as f:
        f.write('\n'.join(output))

    print(f'작업 완료. out/report-{PATCH_VERSION}.txt에 리포트를 생성했습니다.')


if __name__ == '__main__':
    cwd = os.getcwd().replace('\\', '/')
    main()
