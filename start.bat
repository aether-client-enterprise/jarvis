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
    pause
    exit /b 1
)

python -X utf8 -u "%~dp0main.py" > "%~dp0console.log" 2>&1
echo ExitCode=%errorlevel%
echo (a saida completa do servidor esta em console.log na pasta do Jarvis)
pause
