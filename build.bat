@echo off
setlocal
py -m pip install --upgrade pip
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name Borderlands2ModEditor app\main.py
echo.
echo Build finished. EXE should be in dist\Borderlands2ModEditor.exe
pause
