@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller==6.22.3
python -m PyInstaller --noconfirm --onefile --windowed --name MewgenicsSandboxMenu --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.Qt3DCore --exclude-module PySide6.QtMultimedia --exclude-module PySide6.QtQml --exclude-module PySide6.QtQuick main.py
echo.
echo Built: dist\MewgenicsSandboxMenu.exe
