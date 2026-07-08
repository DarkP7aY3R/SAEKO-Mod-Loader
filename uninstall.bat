@echo off
setlocal
cd /d "%~dp0"

python .\tools\install_dll_loader.py --uninstall
if errorlevel 1 (
    echo.
    echo Uninstall failed. If the game was not detected, run:
    echo python .\tools\install_dll_loader.py --uninstall --game-dir "X:\SteamLibrary\steamapps\common\SAEKO Giantess Dating Sim"
    pause
    exit /b 1
)

echo.
echo Restored original EXE.
pause
