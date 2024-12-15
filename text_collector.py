import os
import shutil
import struct
import csv
import subprocess

VERSION = '0.9.3.13049'


def collect_compendium():
    """
    0E 00 00 00 44 54 5F 43 6F 6D 70 65 6E 64 69 75 6D 00 12 00 00 00 .. .. .. .. 00 09 00 00 00 .. .. .. .. .. 00
         14     D  T  _  C  o  m  p  e  n  d  i  u  m  00 key_length   key_text   00 value_length  value_text   00
    """

    prefix = b'\x0E\x00\x00\x00DT_Compendium\x00'
    with open(f'archive/pack/vanilla_extracted/{VERSION}'
              f'/AbioticFactor/Content/Blueprints/DataTables/DT_Compendium.uasset', 'rb') as f:
        content = f.read()

        csv_file = open(f'out/DT_Compendium-{VERSION}.csv', 'w', newline='')
        writer = csv.writer(csv_file)

        csv_file2 = open(f'out/DT_Compendium-{VERSION}_no_pos.csv', 'w', newline='')
        writer2 = csv.writer(csv_file2)

        index = 0
        while True:
            index = content.find(prefix, index)
            if index == -1:
                break

            key_length_pos = index + len(prefix)
            key_length = struct.unpack_from('<i', content, key_length_pos)[0]
            is_key_ascii = key_length > 0
            key_length_bytes = key_length if is_key_ascii else -key_length * 2

            key_pos = key_length_pos + 4
            key_raw = struct.unpack_from(f'<{key_length_bytes - (1 if is_key_ascii else 2)}s', content, key_pos)[0]
            key = key_raw.decode('ascii' if is_key_ascii else 'utf-16')

            value_length_pos = key_pos + key_length_bytes
            value_length = struct.unpack_from('<i', content, value_length_pos)[0]
            is_value_ascii = value_length > 0
            value_length_bytes = value_length if is_value_ascii else -value_length * 2

            value_pos = value_length_pos + 4
            value_raw = struct.unpack_from(f'<{value_length_bytes - (1 if is_value_ascii else 2)}s', content, value_pos)[0]
            value = value_raw.decode('ascii' if is_value_ascii else 'utf-16')

            writer.writerow([value_pos, key, value.replace('\r', '\\r').replace('\n', '\\n')])
            writer2.writerow([key, value.replace('\r', '\\r').replace('\n', '\\n')])

            index = value_pos + value_length_bytes


def build_compendium():
    """
     0    1    2  3   4
    파일,오프셋,키,원문,번역
    """

    path = 'AbioticFactor/Content/Blueprints/DataTables/DT_Compendium.uasset'
    shutil.rmtree('out/pakchunk0-Windows_P/', ignore_errors=True)
    os.makedirs('/'.join(f'out/pakchunk0-Windows_P/{path}'.split('/')[:-1]), exist_ok=True)
    shutil.copy2(f'archive/pack/vanilla_extracted/{VERSION}/{path}',
                 f'out/pakchunk0-Windows_P/{path}')

    with open(f'out/pakchunk0-Windows_P/{path}', 'rb') as f:
        data = f.read()

    rows = []
    with (open(f'data/binary_override/{VERSION}.csv', newline='') as f):
        reader = csv.reader(f, delimiter='\t')
        for file, byte_offset, key, original, translated, *_ in reader:
            if file == 'DT_Compendium':
                rows.append([int(byte_offset), translated.replace('\\r', '\r').replace('\\n', '\n')])
    rows.sort(key=lambda x: x[0])

    total_offset = 0
    for byte_offset, translated in rows:
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

    size_offset = 0x2753
    expected_read_size = struct.unpack_from('<i', data, size_offset)[0]
    data = data[:size_offset] + struct.pack('<i', expected_read_size + total_offset) + data[size_offset + 4:]

    with open(f'out/pakchunk0-Windows_P/{path}', 'wb') as f:
        f.write(data)

    cwd = os.getcwd().replace('\\', '/')
    if not os.path.exists(f'archive/manifest/{VERSION}.manifest'):
        subprocess.run([f'{cwd}/tools/UEcastoc-1.0.1/cpp/main.exe',
                        f'manifest',
                        f'{cwd}/archive/pack/vanilla/pakchunk0-Windows-{VERSION}.utoc',
                        f'{cwd}/archive/pack/vanilla/pakchunk0-Windows-{VERSION}.ucas',
                        f'{cwd}/archive/manifest/{VERSION}.manifest'])

    subprocess.run([f'{cwd}/tools/UEcastoc-1.0.1/cpp/main.exe',
                    f'pack',
                    f'{cwd}/out/pakchunk0-Windows_P',
                    f'{cwd}/archive/manifest/{VERSION}.manifest',
                    f'{cwd}/out/pakchunk0-Windows_P',
                    f'None'])
    os.remove('out/pakchunk0-Windows_P.pak')


if __name__ == '__main__':
    collect_compendium()
