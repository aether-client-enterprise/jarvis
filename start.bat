@echo off
chcp 65001 >nul
echo ========================================
echo Jarvis - Assistente Local
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado no PATH.
    echo.
    echo Instale o Python em: https://www.python.org/downloads/
    echo Durante a instalacao, MARQUE a opcao "Add Python to PATH".
    echo Depois reinicie o terminal e tente novamente.
    echo.
    pause
    exit /b 1
)

echo [1/2] Instalando dependencias principais...
pip install fastapi uvicorn
if %errorlevel% neq 0 (
    echo ERRO ao instalar dependencias principais.
    pause
    exit /b 1
)

echo.
echo [2/2] Instalando dependencias de voz (opcional)...
pip install SpeechRecognition pyttsx3 >nul 2>&1
pip install pyaudio >nul 2>&1
echo (dependencias de voz instaladas se disponiveis para sua versao do Python)

echo.
echo [3/3] Iniciando Jarvis...
echo Abra o navegador em: http://127.0.0.1:8765
echo Pressione CTRL+C para encerrar.
echo.
python main.py

pause
