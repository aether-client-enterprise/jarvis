import os
import sys
import ctypes
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from jarvis.voice import Voice
from jarvis.commands import Commands
from jarvis.fs import FS
from jarvis import brain

HOST = "127.0.0.1"
PORT = 8765

app = FastAPI(title="Jarvis Local — Assistente com Acesso Total ao PC")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # jogos/sites criados em file:// poderão salvar no disco
    allow_methods=["*"],
    allow_headers=["*"],
)

voice = Voice()
fs = FS()
commands = Commands(fs, voice)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class ChatMessage(BaseModel):
    message: str
    lang: str | None = None


class VoiceSelect(BaseModel):
    voice_id: str = ""
    rate: int | None = None


# endpoints em def (não-async) rodam em threadpool: nada trava a resposta.

@app.get("/")
def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/chat")
def chat(msg: ChatMessage):
    reply, detected_lang = commands.parse(msg.message, hint_lang=msg.lang)
    voice.speak(reply[:400], lang=detected_lang)  # fala em background; resposta volta instantânea
    return {"reply": reply, "lang": detected_lang}


# ---------- voz ----------
@app.get("/voice/voices")
def voice_voices():
    return {"voices": voice.list_voices(), "voice_id": voice.config.get("voice_id"),
            "rate": voice.config.get("rate")}


@app.post("/voice/select")
def voice_select(v: VoiceSelect):
    return voice.select_voice(v.voice_id, v.rate)


@app.post("/voice/stop")
def voice_stop():
    voice.stop_speaking()
    return {"ok": True}


@app.post("/voice/listen")
def voice_listen():
    try:
        limite = time.time() + 6
        while not voice.mic_ok and time.time() < limite:
            time.sleep(0.25)
        if not voice.mic_ok:
            return {"text": "", "error": "microfone indisponível"}
        text = voice.wait_for_text(wait=7)
        return {"text": text}
    except Exception as e:
        return {"text": "", "error": str(e)}


@app.get("/voice/state")
def voice_state():
    return {"speaking": voice.is_speaking()}


@app.get("/system/metrics")
def system_metrics():
    cpu = mem = None
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
    except Exception:
        pass
    import shutil
    try:
        du = shutil.disk_usage(os.path.expanduser("~"))
        disk = round(100 * du.used / du.total) if du.total else None
    except Exception:
        disk = None
    return {"cpu": cpu, "mem": mem, "disk": disk}


@app.get("/api/weather")
def api_weather(city: str = ""):
    import json as _json
    try:
        import urllib.request
        from urllib.parse import quote as _q
        lat = lon = None
        local = (city or "").strip()
        if not local:
            try:
                with urllib.request.urlopen("https://ipapi.co/json/", timeout=6) as r:
                    ip = _json.loads(r.read().decode())
                local = ip.get("city") or ""
                lat = ip.get("latitude")
                lon = ip.get("longitude")
            except Exception:
                local = "São Paulo"  # fallback: geolocalização por IP falhou
        if lat is None or lon is None:
            u = f"https://geocoding-api.open-meteo.com/v1/search?name={_q(local)}&count=1&language=pt&format=json"
            with urllib.request.urlopen(u, timeout=6) as r:
                g = _json.loads(r.read().decode())
            if g.get("results"):
                lat = g["results"][0]["latitude"]
                lon = g["results"][0]["longitude"]
                local = g["results"][0].get("name") or local
        if lat is None or lon is None:
            return {"error": "local nao encontrado"}
        u2 = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        with urllib.request.urlopen(u2, timeout=6) as r:
            w = _json.loads(r.read().decode())["current_weather"]
        cod = w.get("weathercode", 0)
        desc = {0: "céu limpo", 1: "quase limpo", 2: "parcial", 3: "nublado", 45: "névoa", 48: "névoa",
                51: "chuvisco", 53: "chuvisco", 55: "chuvisco", 61: "chuva", 63: "chuva", 65: "chuva forte",
                71: "neve", 73: "neve", 75: "neve", 80: "pancadas", 81: "pancadas", 82: "pancadas",
                95: "tempestade", 96: "tempestade", 99: "tempestade"}
        emoji = {0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️", 51: "🌦️", 53: "🌦️", 55: "🌦️",
                 61: "🌧️", 63: "🌧️", 65: "🌧️", 71: "❄️", 73: "❄️", 75: "❄️", 80: "🌧️", 81: "🌧️",
                 82: "🌧️", 95: "⛈️", 96: "⛈️", 99: "⛈️"}
        return {"cidade": local, "temp": round(w.get("temperature", 0)),
                "vento": round(w.get("windspeed", 0)),
                "desc": desc.get(cod, "clima"), "emoji": emoji.get(cod, "🌡️")}
    except Exception as e:
        return {"error": str(e)}


# ---------- cérebro (provedor de IA) ----------
@app.get("/brain/config")
def brain_config():
    return brain.get_provider()


class BrainConfig(BaseModel):
    provider: str
    key: str = ""
    model: str = ""


@app.post("/brain/config")
def brain_set(v: BrainConfig):
    return brain.set_provider(v.provider, v.key, v.model)


# ---------- sistema / arquivos ----------
@app.get("/system/info")
def sys_info():
    return commands.system_info()


@app.post("/system/command")
def sys_command(payload: dict):
    cmd = payload.get("cmd", "")
    return commands.system_run(cmd)


@app.get("/files/browse")
def files_browse(path: str = ""):
    return fs.browse(path)


@app.post("/files/read")
def files_read(payload: dict):
    return fs.read(payload.get("path", ""))


@app.post("/files/write")
def files_write(payload: dict):
    return fs.write(payload.get("path", ""), payload.get("content", ""))


@app.post("/files/delete")
def files_delete(payload: dict):
    return fs.delete(payload.get("path", ""))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relaunch_as_admin():
    script = os.path.abspath(__file__)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)
    sys.exit(0)


if __name__ == "__main__":
    if not is_admin():
        print("[!] Jarvis precisa de Administrador para acesso total ao PC. Relançando como admin...")
        relaunch_as_admin()
    print(f"[*] Jarvis rodando em http://{HOST}:{PORT}")
    print("[*] Wake word: 'ok jarvis' ou 'hey jarvis'")
    print("[*] Idiomas: português, inglês e detecção automática")
    uvicorn.run(app, host=HOST, port=PORT)
