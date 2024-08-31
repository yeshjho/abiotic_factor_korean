import os
import subprocess


run_pak = False
VERSION = "0.9.0.11307"


cwd = os.getcwd().replace('\\', '/')

if run_pak:
    subprocess.run([f'{cwd}/tools/repak_cli-x86_64-pc-windows-msvc/repak.exe',
                    f'pack',
                    f'{cwd}/out/pakchunk0-Windows_P'])
else:
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
