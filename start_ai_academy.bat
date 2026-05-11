@echo off
setlocal

cd /d "%~dp0"

echo [AI Academy] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python не найден. Установите Python 3.11+ и добавьте в PATH.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [AI Academy] Создание виртуального окружения .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo Не удалось создать виртуальное окружение.
        pause
        exit /b 1
    )
)

echo [AI Academy] Установка/обновление зависимостей...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
call ".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 (
    echo Ошибка установки зависимостей.
    pause
    exit /b 1
)

echo [AI Academy] Запуск приложения...
echo Откройте в браузере: http://127.0.0.1:5000
call ".venv\Scripts\python.exe" "app.py"

echo Приложение остановлено.
pause
