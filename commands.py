# language: Python, file: jarvis/commands.py
# Intérprete de comandos e conversa livre do Jarvis
import webbrowser
import urllib.parse
import os
import re
import subprocess
import platform
import sys
import time
from pathlib import Path

from jarvis.templates_site import site_html
from jarvis.templates_rpg import jogo_rpg_html


class Commands:
    def __init__(self, fs, voice=None):
        self.fs = fs
        self.voice = voice
        self.wake_words = ['ok jarvis', 'hey jarvis', 'jarvis', 'oi jarvis', 'e ai jarvis']
        self.conversation_history = []  # memória curta
        self.active_until = 0  # modo contínuo após wake word (segundos)

    def _strip_wake(self, text):
        low = text.strip().lower()
        for w in self.wake_words:
            if low.startswith(w):
                return text[len(w):].strip()
        return text.strip()

    def _detect_lang(self, text):
        t = text.lower()
        pt_words = ['que', 'e', 'de', 'a', 'o', 'em', 'para', 'com', 'por', 'não', 'sim', 'abra', 'criar', 'ler',
                    'executar', 'site', 'arquivo', 'pasta', 'sistema', 'jogo', 'mensagem', 'conversa',
                    'instagram', 'youtube', 'whatsapp', 'facebook', 'google', 'olá', 'oi', 'tudo bem', 'como',
                    'você', 'quem', 'o que']
        en_words = ['the', 'and', 'of', 'a', 'to', 'in', 'for', 'with', 'not', 'yes', 'open', 'create', 'read',
                    'execute', 'site', 'file', 'folder', 'system', 'game', 'message', 'chat', 'instagram',
                    'youtube', 'whatsapp', 'facebook', 'google', 'hello', 'hi', 'jarvis', 'how', 'what', 'who',
                    'you', 'are', 'good', 'morning', 'afternoon', 'night']
        pt_score = sum(1 for w in pt_words if re.search(r'\b' + re.escape(w) + r'\b', t))
        en_score = sum(1 for w in en_words if re.search(r'\b' + re.escape(w) + r'\b', t))
        if pt_score > en_score:
            return 'pt'
        if en_score > pt_score:
            return 'en'
        return 'auto'

    def _t(self, pt, en, lang):
        return en if lang == 'en' else pt

    def parse(self, text, hint_lang=None):
        low = text.strip().lower()
        if not low:
            lang = hint_lang or 'pt'
            return self._t("Diga um comando.", "Say a command.", lang), lang

        lang = hint_lang or self._detect_lang(text)
        now = time.time()

        # Modo contínuo: se já ativado recentemente, não exige wake word novamente
        if now < self.active_until:
            cmd = text.strip()
        else:
            cmd = self._strip_wake(text)

        # Mantém modo contínuo por 30s após qualquer interação
        self.active_until = now + 30

        # Comandos específicos
        if re.match(r'^(abrir|acessar|open|access)\s+', lcmd := cmd.lower()):
            alvo = re.sub(r'^(abrir|acessar|open|access)\s+', '', cmd, flags=re.IGNORECASE).strip()
            return self._abrir(alvo, lang), lang

        if re.search(r'\b(cria(?:r)?|crie|cr[íi][ée]|faz(?:er)?|fa[çc]a|gera(?:r)?|gere|monta(?:r)?|monte|desenvolv[ea]|make|create|build)\b.{0,60}\b(site|jogo|game|app|aplicativo|aplica[çc][ãa]o|p[áa]gina|web)\b', lcmd):
            return self._criar_html(cmd, lang), lang

        if re.match(r'^(ler|ler arquivo|read|read file)\s+', lcmd):
            path = re.sub(r'^(ler|ler arquivo|read|read file)\s+', '', cmd, flags=re.IGNORECASE).strip()
            return self.fs.read(path), lang

        if re.match(r'^(listar|abrir pasta|list|open folder)\s+', lcmd):
            path = re.sub(r'^(listar|abrir pasta|list|open folder)\s+', '', cmd, flags=re.IGNORECASE).strip()
            return self.fs.browse(path), lang

        if re.match(r'^(executar|cmd|run|execute)\s+', lcmd):
            comando = re.sub(r'^(executar|cmd|run|execute)\s+', '', cmd, flags=re.IGNORECASE).strip()
            return self.system_run(comando), lang

        if re.match(r'^(escrever|salvar|write)\s+', lcmd):
            return self._escrever_arquivo(cmd, lang), lang

        if any(w in lcmd for w in ['sistema', 'info do pc', 'processador', 'memória', 'system', 'pc info',
                                   'processor', 'memory']):
            return self.system_info(), lang

        if any(w in lcmd for w in ['buscar arquivo', 'procurar', 'search file', 'find']):
            q = re.sub(r'(buscar arquivo|procurar|search file|find)\s+', '', cmd, flags=re.IGNORECASE).strip()
            res = self.fs.search(q)
            lines = [self._t(f"Busca por '{q}':", f"Search for '{q}':", lang)]
            for it in res.get("results", [])[:50]:
                tag = "[DIR] " if it["is_dir"] else "[ARQ] "
                lines.append(f"{tag}{it['name']} — {it['path']}")
            return "\n".join(lines) if len(lines) > 1 else self._t("Nada encontrado.", "Nothing found.", lang), lang

        # Conversa livre (tipo ChatGPT) — fallback para qualquer outra coisa
        self.conversation_history.append({"user": text, "lang": lang})
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        return self._chat_free(text, lang), lang

    def _abrir(self, alvo, lang):
        mapa = {
            'youtube': 'https://www.youtube.com',
            'instagram': 'https://www.instagram.com',
            'facebook': 'https://www.facebook.com',
            'whatsapp': 'https://web.whatsapp.com',
            'twitter': 'https://x.com',
            'x': 'https://x.com',
            'google': 'https://www.google.com',
            'github': 'https://github.com',
        }
        chave = alvo.lower()
        if chave in mapa:
            webbrowser.open(mapa[chave])
            return self._t(f"Abrindo {alvo} no navegador.", f"Opening {alvo} in browser.", lang)

        if 'instagram' in chave or 'whatsapp' in chave:
            m = re.search(r'(?:do|da|de|com|with|to)\s+(.+)', alvo, re.IGNORECASE)
            nome = m.group(1).strip() if m else ''
            if 'instagram' in chave:
                url = 'https://www.instagram.com/direct/inbox/'
                if nome:
                    url += '?q=' + urllib.parse.quote(nome)
                webbrowser.open(url)
                return self._t(
                    f"Abrindo Instagram. Procure a conversa de {nome} e digite a mensagem.",
                    f"Opening Instagram. Look for {nome}'s conversation and type the message.",
                    lang
                )
            if 'whatsapp' in chave:
                url = 'https://web.whatsapp.com'
                if nome:
                    url += '?search=' + urllib.parse.quote(nome)
                webbrowser.open(url)
                return self._t(
                    f"Abrindo WhatsApp Web. Procure {nome} e envie a mensagem.",
                    f"Opening WhatsApp Web. Look for {nome} and send the message.",
                    lang
                )

        if '.' in alvo and not alvo.startswith('http'):
            url = 'https://' + alvo if not alvo.startswith('www.') else 'https://' + alvo
            webbrowser.open(url)
            return self._t(f"Abrindo {alvo}.", f"Opening {alvo}.", lang)
        webbrowser.open('https://www.google.com/search?q=' + urllib.parse.quote(alvo))
        return self._t(f"Buscando {alvo} no Google.", f"Searching {alvo} on Google.", lang)

    def _criar_html(self, cmd, lang):
        baixo = cmd.lower()
        eh_jogo = re.search(r'\b(jogo|game|plataforma|aventura)\b', baixo) and not re.search(r'\bsite\b', baixo)
        pasta = Path.home() / 'Downloads' / 'Jarvis' / 'criacoes'
        base = 'jogo_rpg_2d' if eh_jogo else 'site_jarvis'
        caminho = pasta / f"{base}_{int(time.time())}.html"
        try:
            if eh_jogo:
                conteudo = jogo_rpg_html()
                tipo = self._t('RPG 2D', 'RPG 2D', lang)
            else:
                tema = 'cyberpunk'
                if re.search(r'romantic|amor|namora|cora[çc][ãa]o|beijo|sigilo', baixo):
                    tema = 'romantico'
                elif re.search(r'natureza|floresta|verde|jardim|planta', baixo):
                    tema = 'natureza'
                elif re.search(r'espac|galaxis?|galaxia|estrela|cosmos', baixo):
                    tema = 'espaco'
                titulo = None
                m_t = re.search(r'(?:chamado|intitulado|titulo|t[íi]tulo)\s+["\']?([^"\'\.,;]+)', baixo)
                if m_t:
                    titulo = m_t.group(1).strip().title()
                legenda = None
                m_l = re.search(r'legenda\s+(?:[a-z]+\s+)?(?:[a-z]+\s+)?([a-z0-9â-ú\s]{1,80}?)(?=\s*[,;.]|$)', baixo)
                if m_l:
                    legenda = m_l.group(1).strip().capitalize()
                conteudo = site_html(tema, titulo, legenda)
                tipo = self._t(f"site (tema: {tema})", f"site (theme: {tema})", lang)
            result = self.fs.write(str(caminho), conteudo)
            if result.get('error'):
                return self._t(f"Erro ao criar: {result['error']}", f"Error creating: {result['error']}", lang)
            webbrowser.open('file:///' + str(caminho).replace('\\', '/'))
            if eh_jogo:
                extra = self._t(
                    " O jogo tem botão 💾 Salvar (grava em Downloads\\Jarvis\\criacoes\\rpg_save.json) e 📂 Carregar.",
                    " The game has 💾 Save (writes to Downloads\\Jarvis\\criacoes\\rpg_save.json) and 📂 Load."
                , lang)
            else:
                extra = ''
            return self._t(
                f"✔ {tipo} criado em {caminho} e aberto no navegador.{extra}",
                f"✔ {tipo} created at {caminho} and opened in browser.{extra}",
                lang
            )
        except Exception as e:
            return self._t(f"Erro ao criar: {e}", f"Error creating: {e}", lang)

    def _gerar_conteudo_html(self, cmd):
        baixo = cmd.lower()
        if 'jogo' in baixo or 'game' in baixo:
            return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Jogo do Jarvis</title>
  <style>
    body { background: #111; color: #fff; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    canvas { border: 2px solid #00d9ff; background: #000; cursor: crosshair; }
    h1 { color: #00d9ff; margin-bottom: 10px; }
    p { margin-bottom: 20px; }
  </style>
</head>
<body>
  <h1>Jogo do Jarvis</h1>
  <p>Use as setas ou WASD para mover o quadrado azul.</p>
  <canvas id="c" width="600" height="400"></canvas>
  <script>
    const cv = document.getElementById('c');
    const x = cv.getContext('2d');
    let p = { x: 300, y: 200 };
    const keys = {};
    window.onkeydown = e => keys[e.code] = true;
    window.onkeyup = e => keys[e.code] = false;
    function loop() {
      if (keys['ArrowLeft'] || keys['KeyA']) p.x -= 5;
      if (keys['ArrowRight'] || keys['KeyD']) p.x += 5;
      if (keys['ArrowUp'] || keys['KeyW']) p.y -= 5;
      if (keys['ArrowDown'] || keys['KeyS']) p.y += 5;
      p.x = Math.max(0, Math.min(cv.width - 40, p.x));
      p.y = Math.max(0, Math.min(cv.height - 40, p.y));
      x.clearRect(0, 0, 600, 400);
      x.fillStyle = '#00d9ff';
      x.fillRect(p.x, p.y, 40, 40);
      requestAnimationFrame(loop);
    }
    loop();
  </script>
</body>
</html>"""
        if 'site' in baixo or 'aplicativo' in baixo or 'app' in baixo:
            return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Projeto Jarvis</title>
  <style>
    body { background: #0a0b0f; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    h1 { color: #00d9ff; margin-bottom: 20px; }
    p { max-width: 500px; text-align: center; line-height: 1.6; margin-bottom: 30px; }
    button { padding: 14px 28px; border: none; border-radius: 10px; background: #00d9ff; color: #051017; font-weight: bold; cursor: pointer; font-size: 1rem; }
    button:hover { background: #33e3ff; }
  </style>
</head>
<body>
  <h1>Criado pelo Jarvis</h1>
  <p>Este site/aplicativo foi gerado pelo seu assistente local com acesso total ao seu PC.</p>
  <button onclick="alert('Jarvis funcionando perfeitamente!')">Testar Jarvis</button>
</body>
</html>"""
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Jarvis Local</title>
</head>
<body>
  <h1>Jarvis Local</h1>
  <p>Projeto gerado com sucesso pelo seu assistente.</p>
</body>
</html>"""

    def _escrever_arquivo(self, cmd, lang):
        m = re.match(r'(?:escrever arquivo|write file)\s+(.+?)\s+(?:conteudo|content)\s+(.+)$', cmd,
                     re.IGNORECASE | re.DOTALL)
        if not m:
            return self._t(
                "Use: escrever arquivo <caminho> conteudo <texto>\nEx: escrever arquivo C:\\ola.txt conteudo Olá, Jarvis!",
                "Use: write file <path> content <text>\nEx: write file C:\\ola.txt content Hello, Jarvis!",
                lang
            )
        path = m.group(1).strip()
        content = m.group(2).strip()
        return self.fs.write(path, content), lang

    def system_run(self, comando):
        try:
            r = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=120,
                               encoding='utf-8', errors='replace')
            out = r.stdout or ''
            err = r.stderr or ''
            rc = r.returncode
            result = f"Código de saída: {rc}\n"
            if out:
                result += f"SAÍDA:\n{out}\n"
            if err:
                result += f"ERRO:\n{err}\n"
            return result.strip() or "Executado sem saída."
        except Exception as e:
            return f"Erro ao executar: {e}"

    def system_info(self):
        return f"""Sistema: {platform.platform()}
Node: {platform.node()}
Processador: {platform.processor()}
Arquitetura: {platform.architecture()[0]}
Python: {sys.version.split()[0]}
Usuário: {os.getlogin()}"""

    def _chat_free(self, text, lang):
        """Conversa livre sem depender de comandos fixos, com memória curta."""
        t = text.lower()

        if any(w in t for w in ['olá', 'oi', 'bom dia', 'boa tarde', 'boa noite', 'hello', 'hi',
                                'good morning', 'good afternoon', 'good night']):
            resp = self._t("Olá! Sou o Jarvis, seu assistente local. Pode falar comigo normalmente.",
                           "Hi! I'm Jarvis, your local assistant. You can talk to me naturally.", lang)
        elif any(w in t for w in ['como você está', 'como vai', 'tudo bem', 'how are you', "how's it going"]):
            resp = self._t("Estou bem, obrigado! Pronto para ajudar no que precisar no seu computador.",
                           "I'm good, thanks! Ready to help with whatever you need on your computer.", lang)
        elif any(w in t for w in ['quem é você', 'o que você faz', 'who are you', 'what do you do']):
            resp = self._t("Sou o Jarvis, seu assistente pessoal instalado localmente no seu PC. Tenho acesso aos seus arquivos, posso abrir programas, sites, criar códigos HTML e conversar com você.",
                           "I'm Jarvis, your personal assistant installed locally on your PC. I have access to your files, can open programs and websites, create HTML code, and chat with you.", lang)
        elif any(w in t for w in ['obrigado', 'valeu', 'thanks', 'thank you']):
            resp = self._t("De nada! Estou aqui quando precisar.", "You're welcome! I'm here whenever you need me.", lang)
        elif any(w in t for w in ['sair', 'encerrar', 'tchau', 'bye', 'goodbye']):
            resp = self._t("Até mais! Estou aqui quando precisar.", "See you later! I'm here whenever you need me.", lang)
        elif any(w in t for w in ['hora', 'que horas', 'time', 'what time']):
            from datetime import datetime
            agora = datetime.now().strftime('%H:%M')
            resp = self._t(f"São {agora}.", f"It's {agora}.", lang)
        else:
            resp = self._t(
                f"Recebi: '{text}'. Posso ajudar com isso de alguma forma específica? Posso abrir sites, criar arquivos HTML, ler/escrever arquivos, executar comandos no terminal ou apenas conversar.",
                f"I received: '{text}'. How can I help specifically? I can open websites, create HTML files, read/write files, run terminal commands, or just chat.",
                lang
            )

        self.conversation_history.append({"jarvis": resp, "lang": lang})
        return resp