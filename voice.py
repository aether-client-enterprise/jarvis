# language: Python, file: jarvis/voice.py
# Reconhecimento de fala e síntese de voz para o Jarvis (Windows)
import speech_recognition as sr
import pyttsx3
import threading


class Voice:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 175)
        self._lock = threading.Lock()
        self._voices = self.engine.getProperty('voices')

        # Define voz em português por padrão, se disponível
        for v in self._voices:
            name = (v.name or "").lower()
            lid = (v.id or "").lower()
            if 'brazil' in name or 'portuguese' in name or 'pt-br' in lid or 'brazilian' in name:
                self.engine.setProperty('voice', v.id)
                break

    def speak(self, text, lang='auto'):
        """Fala o texto. Ajusta a voz pelo idioma se possível."""
        with self._lock:
            if lang == 'en' or lang == 'english':
                for v in self._voices:
                    name = (v.name or "").lower()
                    lid = (v.id or "").lower()
                    if 'english' in name or 'en-us' in lid or 'zira' in name or 'david' in name:
                        self.engine.setProperty('voice', v.id)
                        break
            elif lang == 'pt' or lang == 'portuguese':
                for v in self._voices:
                    name = (v.name or "").lower()
                    lid = (v.id or "").lower()
                    if 'brazil' in name or 'portuguese' in name or 'pt-br' in lid or 'brazilian' in name:
                        self.engine.setProperty('voice', v.id)
                        break
            self.engine.say(text)
            self.engine.runAndWait()

    def listen_once(self, timeout=5, phrase_time_limit=12):
        """
        Ouve uma fala pelo microfone.
        Retorna o texto reconhecido ou levanta exceção se não entender.
        """
        with self.microphone as source:
            # Ajuste rápido de ruído apenas uma vez por chamada
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        # Tenta português primeiro, depois inglês
        try:
            return self.recognizer.recognize_google(audio, language='pt-BR')
        except Exception:
            try:
                return self.recognizer.recognize_google(audio, language='en-US')
            except Exception:
                raise
