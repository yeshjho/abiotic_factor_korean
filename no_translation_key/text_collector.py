import struct
import csv


VERSION = '0.9.0.11307'


def collect_compendium():
    """
    0E 00 00 00 44 54 5F 43 6F 6D 70 65 6E 64 69 75 6D 00 12 00 00 00 53 65 63 75 00 09 00 00 00 47 2E 41 2E 2E 00
         14     D  T  _  C  o  m  p  e  n  d  i  u  m  00 key_length   key_text   00 value_length  value_text   00
    """
    prefix = b'\x0E\x00\x00\x00DT_Compendium\x00'
    with open(fr'archive\pack\vanilla_extracted\{VERSION}'
              fr'\AbioticFactor\Content\Blueprints\DataTables\DT_Compendium.uasset', 'rb') as f:
        content = f.read()

        csv_file = open('out/DT_Compendium.csv', 'w', newline='')
        writer = csv.writer(csv_file)

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

            writer.writerow([key, value.replace('\r', '\\r').replace('\n', '\\n')])  # 엑셀 복붙용

            index = value_pos + value_length_bytes


def build_compendium():


if __name__ == '