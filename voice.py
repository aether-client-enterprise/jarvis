# language: Python, file: jarvis/voice.py
# Ouvinte CONTÍNUO em thread própria (resposta imediata quando você para de falar)
# + síntese de voz interrompível + troca de voz salva em voice_config.json
import difflib
import json
import os
import threading
import time
from collections import deque

import speech_recognition as sr
import pyttsx3

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voice_config.json')

WAKE_TOKENS = ['ok jarvis', 'hey jarvis', 'jarvis', 'oi jarvis', 'e ai jarvis']


class Voice:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6        # reage logo que você para de falar
        try:
            self.recognizer.non_speaking_duration = 0.35
        except Exception:
            pass
        self.microphone = sr.Microphone()
        self._ambient_done = False

        engine = pyttsx3.init()
        self._voices = engine.getProperty('voices')
        del engine  # a fala usa motor próprio por thread

        self.config = {'voice_id': None, 'rate': 185}
        self._load_config()
        if not self.config.get('voice_id'):
            self.config['voice_id'] = self._pick_voice('pt')
            self._save_config()

        # ---------- ouvinte contínuo ----------
        self._texts = deque(maxlen=8)            # [(ts, texto)]
        self._speak_thread = None
        self._speaking_flag = False
        self.mic_ok = False
        self._listener = threading.Thread(target=self._listen_loop, daemon=True)
        self._listener.start()

    # ================= ESCUTA CONTÍNUA =================
    def _listen_loop(self):
        """Abre o microfone UMA vez e fica escutando para sempre.
        Cada fala reconhecida entra na fila; /voice/listen só pega da fila."""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.7)
                self._ambient_done = True
                self.mic_ok = True
                while True:
                    try:
                        audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=12)
                    except Exception:
                        time.sleep(0.3)
                        continue
                    texto = self._recognize(audio)
                    if not texto:
                        continue
                    if self.is_speaking():
                        # durante a fala do Jarvis: só interrupção com wake word (evita eco de si mesmo)
                        if self._is_wake_text(texto):
                            self.stop_speaking()
                            self._push(texto)
                        continue
                    self._push(texto)
        except Exception:
            self.mic_ok = False  # sem microfone: endpoints avisam

    def _recognize(self, audio):
        try:
            return self.recognizer.recognize_google(audio, language='pt-BR')
        except Exception:
            try:
                return self.recognizer.recognize_google(audio, language='en-US')
            except Exception:
                return ''

    def _push(self, texto):
        with self._lock_texts:
            self._texts.append((time.time(), texto.strip()))

    _lock_texts = threading.Lock()

    def _is_wake_text(self, texto):
        low = texto.lower().strip()
        if any(w in low for w in WAKE_TOKENS):
            return True
        # flexível: "ok jackson", "hey jarbas" etc. contam como wake
        tk = low.split()
        for i, w in enumerate(tk):
            close = difflib.get_close_matches(w, ['jarvis'], n=1, cutoff=0.7)
            if close and i > 0 and tk[i - 1] in ('ok', 'hey', 'oi', 'ola', 'olá', 'e', 'ei'):
                return True
            if close and i == 0:
                return True
        return False

    def wait_for_text(self, wait=7):
        """Bloqueia até chegar uma fala reconhecida (ou devolve vazio). Só textos recentes (<10s)."""
        limite = time.time() + wait
        while time.time() < limite:
            with self._lock_texts:
                agora = time.time()
                while self._texts and (self._texts[0][0] < agora - 10 or self._texts[0][1] is None):
                    self._texts.popleft()
                if self._texts:
                    _, t = self._texts.popleft()
                    return t
            time.sleep(0.05)
        return ''

    def listen_once(self, timeout=4, phrase_time_limit=12):
        """Compatibilidade: espera um texto novo da fila do ouvinte contínuo."""
        return self.wait_for_text(wait=max(3, timeout))

    # ================= CONFIG DE VOZ =================
    def _voice_props(self, v):
        return ((v.name or '') + ' ' + (v.id or '')).lower()

    def _pick_voice(self, lang):
        alvos = ['brazil', 'portuguese', 'pt-br'] if lang == 'pt' else ['english', 'en-us', 'zira', 'david']
        for v in self._voices:
            p = self._voice_props(v)
            if any(a in p for a in alvos):
                return v.id
        return None

    def list_voices(self):
        return [{'id': v.id, 'name': v.name or v.id} for v in self._voices]

    def _load_config(self):
        try:
            if os.path.exists(CONFIG):
                with open(CONFIG, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.config.update({k: data[k] for k in ('voice_id', 'rate') if k in data})
        except Exception:
            pass

    def _save_config(self):
        try:
            with open(CONFIG, 'w', encoding='utf-8') as f:
                json.dump({'voice_id': self.config.get('voice_id'), 'rate': self.config.get('rate', 185)}, f,
                          ensure_ascii=False)
        except Exception:
            pass

    def select_voice(self, voice_id, rate=None):
        if voice_id:
            if not any(v.id == voice_id for v in self._voices):
                return {'error': 'Voz não encontrada'}
            self.config['voice_id'] = voice_id
        if rate:
            try:
                self.config['rate'] = max(100, min(300, int(rate)))
            except Exception:
                pass
        self._save_config()
        return {'ok': True, 'voice_id': self.config['voice_id'], 'rate': self.config['rate']}

    # ================= FALA (thread própria + interrompível) =================
    def speak(self, text, lang='auto'):
        self.stop_speaking()
        t = threading.Thread(target=self._speak_job, args=(text, lang), daemon=True)
        self._speak_thread = t
        t.start()

    def _speak_job(self, text, lang):
        self._speaking_flag = True
        self._last_engine = None
        try:
            engine = pyttsx3.init()
            self._last_engine = engine
            voice_id = self.config.get('voice_id') or self._pick_voice(lang if lang in ('pt', 'en') else 'pt')
            if voice_id:
                engine.setProperty('voice', voice_id)
            try:
                engine.setProperty('rate', int(self.config.get('rate', 185)))
            except Exception:
                pass
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass
        finally:
            self._last_engine = None
            self._speaking_flag = False
            time.sleep(0.15)  # entre o fim da fala e a retomada da escuta (evita capturar o final do som)

    def is_speaking(self):
        return bool(getattr(self, '_speaking_flag', False))

    def stop_speaking(self):
        eng = getattr(self, '_last_engine', None)
        if eng is not None:
            try:
                eng.stop()
            except Exception:
                pass
