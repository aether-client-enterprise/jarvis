# language: Python, file: jarvis/voice.py
# Reconhecimento de fala + síntese de voz interrompível + troca de voz (Jarvis)
import json
import os
import threading

import speech_recognition as sr
import pyttsx3

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voice_config.json')


class Voice:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.microphone = sr.Microphone()
        self._mic_busy = threading.Event()
        self._ambient_done = False

        engine = pyttsx3.init()
        self._voices = engine.getProperty('voices')
        del engine  # fala usa engine próprio por thread

        self.config = {'voice_id': None, 'rate': 185}
        self._load_config()
        if not self.config.get('voice_id'):
            self.config['voice_id'] = self._pick_voice('pt')
            self._save_config()

    # ---------- utilidades ----------
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
        """Escolhe a voz salva em voice_config.json (persiste entre reinícios)."""
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

    # ---------- escuta ----------
    def listen_once(self, timeout=4, phrase_time_limit=12):
        """Ouve uma fala. Ajuste de ruído de ambiente só na primeira vez (mais rápido)."""
        if self._last_engine is not None:
            self.stop_speaking()  # barge-in: usuário falou, pare a voz atual
        self._mic_busy.set()
        try:
            with self.microphone as source:
                if not self._ambient_done:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                    self._ambient_done = True
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        finally:
            self._mic_busy.clear()
        try:
            return self.recognizer.recognize_google(audio, language='pt-BR')
        except Exception:
            try:
                return self.recognizer.recognize_google(audio, language='en-US')
            except Exception:
                return ''

    # ---------- fala (thread própria + interrompível) ----------
    def speak(self, text, lang='auto'):
        """Fala em background. Nova fala corta a anterior na hora."""
        self.stop_speaking()
        t = threading.Thread(target=self._speak_job, args=(text, lang), daemon=True)
        self._speak_thread = t
        t.start()

    def _speak_job(self, text, lang):
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

    def stop_speaking(self):
        """Interrompe a fala atual imediatamente."""
        eng = getattr(self, '_last_engine', None)
        if eng is not None:
            try:
                eng.stop()
            except Exception:
                pass
