Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Jarvis — Assistente Local" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PY_EXE = Get-Command python -ErrorAction SilentlyContinue
if (-not $PY_EXE) { $PY_EXE = Get-Command py -ErrorAction SilentlyContinue }
if (-not $PY_EXE) { $PY_EXE = Get-Command python3 -ErrorAction SilentlyContinue }

if (-not $PY_EXE) {
    Write-Host "ERRO: Python não encontrado." -ForegroundColor Red
    Write-Host "Instale em: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Durante a instalação, MARQUE 'Add Python to PATH'." -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host "[1/2] Instalando dependências principais..." -ForegroundColor Yellow
& $PY_EXE -m pip install fastapi uvicorn
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO ao instalar dependências principais." -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host ""
Write-Host "[2/2] Instalando dependências de voz (opcional)..." -ForegroundColor Yellow
& $PY_EXE -m pip install SpeechRecognition pyttsx3 -ErrorAction SilentlyContinue
& $PY_EXE -m pip install pyaudio -ErrorAction SilentlyContinue
Write-Host "(Dependências de voz instaladas se disponíveis para sua versão do Python.)" -ForegroundColor Gray

Write-Host ""
Write-Host "[3/3] Iniciando Jarvis..." -ForegroundColor Yellow
Write-Host "Abra o navegador em: http://127.0.0.1:8765" -ForegroundColor Green
Write-Host "Pressione CTRL+C para encerrar." -ForegroundColor Green
Write-Host ""
& $PY_EXE main.py
