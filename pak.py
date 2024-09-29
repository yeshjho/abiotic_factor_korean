import os
import subprocess


run_pak = True
VERSION = "0.9.1.11753"


cwd = os.getcwd().replace('\\', '/')

if run_pak:
    subprocess.run([f'{cwd}/tools/UnrealReZen_V01/UnrealReZen.exe',
                    f'--content-path',
                    f'{cwd}/out/pakchunk0-Windows_P',
                    f'--engine-version',
                    f'GAME_UE5_4',
                    f'--game-dir',
                    f'{cwd}/archive/pack/vanilla/{VERSION}',
                    f'--output-path',
                    f'{cwd}/out/pakchunk0-Windows_P.utoc'])
    if os.path.exists(f'oo2core_9_win64.dll'):
        os.remove('oo2core_9_win64.dll')
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
