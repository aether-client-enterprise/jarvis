import os
import sys
import ctypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from jarvis.voice import Voice
from jarvis.commands import Commands
from jarvis.fs import FS

HOST = "127.0.0.1"
PORT = 8765

app = FastAPI(title="Jarvis Local — Assistente com Acesso Total ao PC")
voice = Voice()
fs = FS()
commands = Commands(fs, voice)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

class ChatMessage(BaseModel):
    message: str
    lang: str | None = None

@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.post("/chat")
async def chat(msg: ChatMessage):
    reply, detected_lang = commands.parse(msg.message, hint_lang=msg.lang)
    try:
        voice.speak(reply[:300], lang=detected_lang)
    except Exception:
        pass
    return {"reply": reply, "lang": detected_lang}

@app.get("/system/info")
async def sys_info():
    return commands.system_info()

@app.post("/system/command")
async def sys_command(payload: dict):
    cmd = payload.get("cmd", "")
    return commands.system_run(cmd)

@app.get("/files/browse")
async def files_browse(path: str = ""):
    return fs.browse(path)

@app.post("/files/read")
async def files_read(payload: dict):
    path = payload.get("path", "")
    return fs.read(path)

@app.post("/files/write")
async def files_write(payload: dict):
    path = payload.get("path", "")
    content = payload.get("content", "")
    return fs.write(path, content)

@app.post("/files/delete")
async def files_delete(payload: dict):
    path = payload.get("path", "")
    return fs.delete(path)

@app.post("/voice/listen")
async def voice_listen():
    try:
        text = voice.listen_once(timeout=4, phrase_time_limit=10)
        return {"text": text}
    except Exception as e:
        return {"text": "", "error": str(e)}

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