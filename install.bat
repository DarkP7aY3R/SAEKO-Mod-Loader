@echo off
setlocal
cd /d "%~dp0"

set "TRANSLATION_DIR="

if exist ".\translation\" set "TRANSLATION_DIR=%~dp0translation"
if exist ".\pl\" set "TRANSLATION_DIR=%~dp0pl"

if defined TRANSLATION_DIR (
    echo Found translation folder: %TRANSLATION_DIR%
    python .\tools\validate_translation.py --translation "%TRANSLATION_DIR%"
    if errorlevel 1 (
        echo.
        echo Translation validation failed. Fix CSV files or delete the translation folder to install only the loader.
        pause
        exit /b 1
    )

    python .\tools\install_dll_loader.py --install --dll "%~dp0saeko_mod_loader.dll" --config "%~dp0saeko_mod_loader.ini" --translation-dir "%TRANSLATION_DIR%" --mods-dir "%~dp0mods" --texture-packs-dir "%~dp0texture_packs"
) else (
    echo No .\translation or .\pl folder found. Installing loader, Mods menu, and bundled DLL mods only.
    echo Custom language templates can be generated later from the in-game Mods popup.
    python .\tools\install_dll_loader.py --install --dll "%~dp0saeko_mod_loader.dll" --config "%~dp0saeko_mod_loader.ini" --mods-dir "%~dp0mods" --texture-packs-dir "%~dp0texture_packs" --no-translation-copy
)

if errorlevel 1 (
    echo.
    echo Install failed. If the game was not detected, run:
    echo python .\tools\install_dll_loader.py --install --dll "%~dp0saeko_mod_loader.dll" --config "%~dp0saeko_mod_loader.ini" --mods-dir "%~dp0mods" --texture-packs-dir "%~dp0texture_packs" --game-dir "X:\SteamLibrary\steamapps\common\SAEKO Giantess Dating Sim" --no-translation-copy
    echo.
    echo If you already have translated CSV files, add:
    echo --translation-dir "X:\path\to\your\translation"
    pause
    exit /b 1
)

echo.
echo Installed. Start SAEKO from Steam.
pause
