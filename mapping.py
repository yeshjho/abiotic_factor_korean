import os
import shutil


GAME_LOC = 'C:/Program Files (x86)/Steam/steamapps/common/AbioticFactor/AbioticFactor/Binaries/Win64'
INSTALL = False

# Ctrl + Numpad 6
if INSTALL:
    shutil.copytree('tools/UE4SS_v3.0.1/ue4ss/', f'{GAME_LOC}/ue4ss', dirs_exist_ok=True)
    shutil.copy2('tools/UE4SS_v3.0.1/version.dll', f'{GAME_LOC}/version.dll')
else:
    def remove_if_exists(file_name):
        if os.path.exists(file_name):
            os.remove(file_name)

    shutil.rmtree(f'{GAME_LOC}/ue4ss', ignore_errors=True)
    remove_if_exists(f'{GAME_LOC}/version.dll')
