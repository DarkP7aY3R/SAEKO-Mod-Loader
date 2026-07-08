@echo off
setlocal
cd /d "%~dp0"

set "TRANSLATION_DIR="

if exist ".\pl\" set "TRANSLATION_DIR=%~dp0pl"
if exist ".\translation\" set "TRANSLATION_DIR=%~dp0translation"

if defined TRANSLATION_DIR (
    echo Found translation folder: %TRANSLATION_DIR%
    python .\tools\validate_translation.py --translation "%TRANSLATION_DIR%"
    if errorlevel 1 (
        echo.
        echo Translation validation failed. Fix CSV files or delete the translation folder to install only the loader.
        pause
        exit /b 1
    )

    python .\tools\install_dll_loader.py --install --dll "%~dp0saeko_mod_loader.dll" --config "%~dp0saeko_mod_loader.ini" --translation-dir "%TRANSLATION_DIR%"
) else (
    echo No .\translation or .\pl folder found. Installing loader without copying CSV files.
    echo You can generate templates in-game or install later with --translation-dir.
    python .\tools\install_dll_loader.py --install --dll "%~dp0saeko_mod_loader.dll" --config "%~dp0saeko_mod_loader.ini" --no-translation-copy
)

if errorlevel 1 (
    echo.
    echo Install failed. If the game was not detected, run:
    echo python .\tools\install_dll_loader.py --install --dll "%~dp0saeko_mod_loader.dll" --config "%~dp0saeko_mod_loader.ini" --game-dir "X:\SteamLibrary\steamapps\common\SAEKO Giantess Dating Sim" --no-translation-copy
    echo.
    echo If you already have translated CSV files, add:
    echo --translation-dir "X:\path\to\your\translation"
    pause
    exit /b 1
)

echo.
echo Installed. Start SAEKO from Steam.
pause
