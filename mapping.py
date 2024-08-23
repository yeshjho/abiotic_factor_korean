import os
import shutil


GAME_LOC = 'C:/Program Files (x86)/Steam/steamapps/common/AbioticFactor/AbioticFactor/Binaries/Win64'
INSTALL = False

if INSTALL:
    shutil.copytree('tools/UE4SS_v3.0.1/Mods/', f'{GAME_LOC}/Mods', dirs_exist_ok=True)
    shutil.copy2('tools/UE4SS_v3.0.1/dwmapi.dll', f'{GAME_LOC}/dwmapi.dll')
    shutil.copy2('tools/UE4SS_v3.0.1/UE4SS.dll', f'{GAME_LOC}/UE4SS.dll')
    shutil.copy2('tools/UE4SS_v3.0.1/UE4SS-settings.ini', f'{GAME_LOC}/UE4SS.UE4SS-settings.ini')
else:
    def remove_if_exists(file_name):
        if os.path.exists(file_name):
            os.remove(file_name)

    shutil.rmtree(f'{GAME_LOC}/Mods', ignore_errors=True)
    remove_if_exists(f'{GAME_LOC}/dwmapi.dll')
    remove_if_exists(f'{GAME_LOC}/UE4SS.dll')
    remove_if_exists(f'{GAME_LOC}/UE4SS-settings.ini')
    remove_if_exists(f'{GAME_LOC}/UE4SS.log')
    remove_if_exists(f'{GAME_LOC}/Mappings.usmap')
