import os
import sys
import ctypes

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
        text = voice.listen_once(timeout=4, phrase_time_limit=12)
        return {"text": text}
    except Exception as e:
        return {"text": "", "error": str(e)}


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
