@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Создание ярлыка «AI Academy» на рабочем столе...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_desktop_shortcut.ps1"
if errorlevel 1 (
    echo Ошибка при создании ярлыка.
    pause
    exit /b 1
)
pause
