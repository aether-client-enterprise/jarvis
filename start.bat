@echo off
chcp 65001 >nul
title Jarvis - Assistente Local
echo ========================================
echo JARVIS - Assistente Local com acesso total
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
pip install fastapi uvicorn psutil --quiet
if %errorlevel% neq 0 (
    echo AVISO: falhou instalar dependencias (tentando prosseguir se ja estao ok)...
)

echo.
echo [2/2] Instalando dependencias de voz (opcional)...
pip install SpeechRecognition pyttsx3 pyaudio --quiet 2>nul
echo (dependencias de voz instaladas se disponiveis para sua versao do Python)

echo.
echo [3] Iniciando Jarvis...
echo Interface: http://127.0.0.1:8765
echo HTTP Windows pode pedir a confirmacao de ADMIN (aceite p/ acesso total).
echo Pressione CTRL+C para encerrar.
echo.
python -X utf8 main.py

pause
