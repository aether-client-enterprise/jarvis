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

from jarvis import brain
from jarvis import creator


# ------------- EXECUÇÃO REAL do PC: abrir PROGRAMAS INSTALADOS, não "pesquisar" -------------
URI_APP = {
    'spotify': 'spotify:', 'discord': 'discord://', 'telegram': 'tg://',
    'whatsapp': 'whatsapp://', 'steam': 'steam://open/games', 'netflix': 'netflix://',
    'roblox': 'roblox://', 'teams': 'msteams:', 'zoom': 'zoomus://',
    'riot': 'riotclient://', 'valorant': 'riotclient://', 'league': 'riotclient://',
    'telegramdesktop': 'tg://',
}

APELIDOS_APP = {
    'vscode': 'visual studio code', 'vs code': 'visual studio code',
    'code': 'visual studio code', 'loja': 'microsoft store',
    'store': 'microsoft store', 'paint': 'paint', 'lunar': 'lunar client',
    'owl': 'owl client', 'libs': '', 'valorant': 'riot client',
    'league': 'league of legends', 'edge': 'microsoft edge',
    'chrome': 'google chrome', 'planilhas': 'excel', 'documento': 'word',
}


def _termos_de(termo):
    return [t for t in re.findall(r'[a-z0-9]{3,}', (termo or '').lower())]


def _lnk_do_menu(termos):
    """Procura o ATALHO do aplicativo no Menu Iniciar (Windows 10/11)."""
    pastas = [os.path.join(os.getenv('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
              r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs']
    for base in pastas:
        if not os.path.isdir(base):
            continue
        quase = None
        for root, _dirs, files in os.walk(base):
            for f in files:
                fl = f.lower()
                if not fl.endswith('.lnk') or 'uninstall' in fl:
                    continue
                if all(t in fl for t in termos):
                    return os.path.join(root, f)
                if quase is None and any(t in fl for t in termos):
                    quase = os.path.join(root, f)
        if quase:
            return quase
    return None


def _appid_startapps(termos):
    """Busca o AppID (UWP/Win32 moderno) e abre via shell:AppsFolder."""
    q = ' -or '.join(("$_.Name -like '*%s*'" % t.replace("'", "''")) for t in termos)
    if not q:
        return False
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-Command',
                              '(Get-StartApps | Where-Object { ' + q + ' } | '
                              'Select-Object -First 4 -ExpandProperty AppID)'],
                             capture_output=True, text=True, timeout=20)
    except Exception:
        return False
    for aid in (out.stdout or '').splitlines():
        aid = aid.strip()
        if aid and ' ' not in aid:
            subprocess.Popen(['explorer', 'shell:AppsFolder\\' + aid], close_fds=True)
            return True
    return False


def _executar_programa(chave, alvo_texto=''):
    """Tenta ABRIR O PROGRAMA DE VERDADE. True/False."""
    base = chave
    for k, v in APELIDOS_APP.items():
        if k in base and v:
            base = base.replace(k, v)

    # Spotify com pedido embutido (tocar/pesquisar X) usa o URI do app
    m = re.search(r'(?:spotify|musicas?|m[úu]sic[ao]s?)\s+(?:toc[arz]?|toca|toque?|play|coloca|p[ôo]e?s?|pesquis[ae]+|d[ée]?)\s+(?:um|a|o)?\s*(.+)', base)
    if not m:
        m = re.search(r'(?:spotify)\s+(?:playlist|lista)\s+(?:de|do|da|com|with)?\s*(.+)', base)
    if 'spotify' in base and m:
        try:
            os.startfile('spotify:search:' + urllib.parse.quote(m.group(1).strip()))
            return True
        except Exception:
            pass

    termos = _termos_de(base)
    # 1) esquema de URI do app (mais rápido e oficial)
    for k, uri in URI_APP.items():
        if k in base:
            try:
                os.startfile(uri if 'spotify' not in base else 'spotify:')
                return True
            except Exception:
                pass
    # 2) atalho no Menu Iniciar
    lnk = _lnk_do_menu(termos)
    if lnk:
        try:
            os.startfile(lnk)
            return True
        except Exception:
            pass
    # 3) AppID moderno via shell:AppsFolder
    if _appid_startapps(termos):
        return True
    return False


def _url_instagram(texto):
    """Instagram com intenção real: perfil, post, stories, mensagem."""
    t = texto or ''
    chave = t.lower()
    mperf = re.search(r'perfil\s+(?:@\s*)?(?:d[aeo]s?|dos?|das?)?\s*([A-Za-z0-9_.]{2,30})', t, re.IGNORECASE)
    mpost = re.search(r'(?:post|publica[çc][ãa]o)\s+([A-Za-z0-9_-]{5,30})', t, re.IGNORECASE)
    url = 'https://www.instagram.com'
    if re.search(r'\b(?:mensagem|dm|direct|conversa)', chave):
        m = re.search(r'(?:do|da|de|com|with|to)\s+(.+)', t, re.IGNORECASE)
        url = 'https://www.instagram.com/direct/inbox/'
        if m:
            url += '?q=' + urllib.parse.quote(m.group(1).strip())
    elif mperf:
        url = 'https://www.instagram.com/' + mperf.group(1).strip('.').lstrip('@') + '/'
    elif mpost:
        url = 'https://www.instagram.com/p/' + mpost.group(1) + '/'
    elif re.search(r'stor', chave):
        url = 'https://www.instagram.com/stories/'
    return url


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

    @staticmethod
    def _eh_criacao(lcmd):
        """True se o usuário está PEDINDO PARA CRIAR algo (qualquer tipo, simples ou complexo)."""
        if re.search(r'\b(abrir pasta|listar|executar)\b', lcmd):
            return False
        verbo = r'\b(cria(?:r|ç[ãa]o)?|crie|faz(?:er)?|fa[çc]a|gera(?:r)?|gere|monta(?:r)?|monte|' \
                r'desenvolv(?:a|er)|construa|construir|programe|make|create|build|develop|generate)\b'
        objetos = (r'\b(site|jogo|game|app|aplicativo|aplica[çc][ãa]o|p[áa]ginas?|web|sistema|bot|chatbot|'
                   r'script|c[óo]digo|programa|fun[çc][ãa]o|plataforma|lista|tabela|formul[áa]rio|'
                   r'calculadora|loja|portf[óo]lio|galeria|cron[ôo]metro|temporizador|timer|quiz|'
                   r'dashboard|painel|relat[óo]rio|banco|agenda|plano|template|layout|menu|banner|'
                   r'aventura|rpg|simulador|editor|conversor|ferramenta|projeto|portal)\b')
        # também aceita "criar algo / qualquer coisa" genérico
        generico = r'\b(algo|qualquer coisa)\b'
        if re.search(verbo, lcmd) and (re.search(objetos, lcmd) or re.search(generico, lcmd)):
            # proteção: SÓ engata se a frase É uma pergunta ("o que você faz?" /
            # "como funciona?"). Palavra 'como' no meio do pedido (pr "como fosse uma
            # loja real") NÃO bloqueia a criação.
            if lcmd.rstrip().endswith('?') or re.match(
                    r'\s*(o que|quem|qual|quais|quando|onde|por que|porque|tem|existe|'
                    r'você (sabe|pode me)|pode me dize[r]|what |why |how )', lcmd):
                return False
            return True
        return False

    @staticmethod
    def _pergunta_criacao(lcmd):
        """True se o usuário perguntou o que o Jarvis FEZ com criações passadas."""
        return bool(re.search(
            r'\b(o que voc[êe] (fez|criou|montou)|o que (fez|criou)|como (foi|ficou)|'
            r'(est[áa]|ficou) pronto|'
            r'onde (est[áa]|ficou|salvou|guardou) (o|a)? ?(projetos?|sites?|jogos?|apps?|cria[çc][õo]es?)|'
            r'(mostre|mostra|abre) (as |as minhas |minhas )?(cria[çc][õo]es?|projetos?|resultados?)|'
            r'(minhas|as) cria[çc][õo]es|meu[s]? projeto[s]?\b)', lcmd))

    def parse(self, text, hint_lang=None, via=None):
        raw = text
        if via == 'voz':
            try:
                corr = brain.correct_transcript(text)
                if corr and corr.strip() and corr.strip().lower() != text.strip().lower():
                    text = corr.strip()
            except Exception:
                pass
        low = text.strip().lower()
        if not low:
            lang = hint_lang or 'pt'
            return self._t("Diga um comando.", "Say a command.", lang), lang

        lang = hint_lang or self._detect_lang(text)
        now = time.time()

        # Registra TUDO que o usuário falar (memória persistente, bruto + corrigido)
        try:
            brain.log_user(text, lang)
            if via == 'voz' and raw != text:
                brain.log_user('[voz bruta] ' + raw, lang)
        except Exception:
            pass

        # Modo contínuo: se já ativado recentemente, não exige wake word novamente
        if now < self.active_until:
            cmd = text.strip()
        else:
            cmd = self._strip_wake(text)

        # Mantém modo contínuo por 30s após qualquer interação
        self.active_until = now + 30

        # Análise/leitura de imagem com IA de visão
        if re.search(r'\b(analis\w*|lei\w*|olh\w*|v[ée]|descrev\w*|observ\w*|interpret\w*)\b.*\b(imagens?|fotos?|prints?|screenshot|capturas?)\b', low) \
                or re.search(r'\b(imagens?|fotos?|prints?|screenshot|capturas?)\b.{0,30}\b(analis\w*|lei\w*|olh\w*|descrev\w*|observ\w*)\b', low):
            m_path = re.search(r'(?:[a-zA-Z]:)?[\\/][^"*?<>|]+?\.(?:png|jpe?g|jpe?g|webp|gif|bmp)', cmd, re.IGNORECASE)
            if m_path:
                resp_img = None
                try:
                    resp_img = brain.analyze_image(m_path.group(0).strip(), text)
                except Exception:
                    resp_img = None
                if resp_img:
                    return self._t('👁️ Análise da imagem:\n', '👁️ Image analysis:\n', lang) + resp_img, lang
                return self._t(
                    'Não consegui usar IA de visão agora. Abra ⚙️ IA e cadastre Groq/Gemini/OpenAI/Anthropic.'
                    ' Caminho verificado: ' + m_path.group(0),
                    'Vision AI unavailable. Add a free Groq/Gemini key in ⚙️ IA.',
                    lang), lang
            return self._t(
                'Me diga o caminho da imagem. Ex: analise a imagem C:\\Users\\joilton\\Downloads\\foto.png',
                'Give the image path, e.g.: analyze image C:\\...\\photo.png', lang), lang

        # Comandos específicos
        if re.match(r'^(abrir|abra|abre|abri|abrir[a-z]*|acessar|acesse|acessar|open|access)\s+', lcmd := cmd.lower()):
            alvo = re.sub(r'^(abrir|acessar|open|access)\s+', '', cmd, flags=re.IGNORECASE).strip()
            return self._abrir(alvo, lang), lang

        # CRIAÇÃO de qualquer coisa: agenda em segundo plano e responde CURTO (regra do dono:
        # só "confirmado"/"estou gerando"; na sequência o painel mostra onde o projeto ficou).
        if self._eh_criacao(lcmd):
            try:
                creator.fila_job(cmd, lang)
            except Exception:
                pass
            return self._t('✅ Confirmado. Estou gerando...',
                           '✅ Confirmed. Generating...', lang), lang

        # Depois que ele pergunta o que foi feito: resumo CURTO e fácil (onde ficou, como abrir)
        if self._pergunta_criacao(lcmd) and creator.tem_ultimo():
            return creator.resumo(lang), lang

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

        # Cérebro LLM: responde QUALQUER pergunta/tarefa (não depende de nada programado)
        # e pode devolver diretivas reais: [RUN: ...] [OPEN: ...] [SITE: ...]
        resposta, acoes = None, []
        try:
            resposta, acoes = brain.ask(text, lang)
        except Exception:
            resposta = None
        self.conversation_history.append({"user": text, "lang": lang})
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        if resposta:
            extras = []
            for tipo, valor in (acoes or [])[:2]:
                try:
                    if tipo == 'OPEN':
                        self._abrir(valor, lang)
                        extras.append("→ executado: " + valor)
                    elif tipo == 'RUN':
                        saida = (self.system_run(valor) or '').strip()
                        extras.append(f"→ comando `{valor}` executado:\n{saida[:700]}")
                    elif tipo == 'SITE':
                        extras.append(self._criar_html('criar site ' + valor, lang))
                except Exception as e:
                    extras.append('→ falha ao executar: ' + str(e))
            if extras:
                resposta = resposta + '\n\n' + '\n\n'.join(extras[:2])
            return resposta, lang

        # Fallback offline (sem internet): conversa local básica
        return self._chat_free(text, lang), lang

    def _abrir(self, alvo, lang):
        """Abre DE VERDADE: programa instalado > site oficial > Google (último recurso)."""
        alvo = (alvo or '').strip()
        alvo = re.sub(r'(?:o\s+|a\s+)?(?:site|pagina|p[áa]gina|p[áa]g|app|aplicativo|aplica[çc][ãa]o)\s+(?:do\s+|da\s+|de\s+|pel[oa]\s+|para\s+|pra\s+|to\s+)?\s*',
                      '', alvo, flags=re.IGNORECASE).strip()
        alvo = re.sub(r'^(?:o|a|os|as|meu|minha)\s+', '', alvo, flags=re.IGNORECASE).strip()

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
        chave = (alvo or '').lower()
        if chave in mapa:
            webbrowser.open(mapa[chave])
            return self._t(f"Abrindo {alvo} no navegador.", f"Opening {alvo} in browser.", lang)

        if 'youtube' in chave:
            resto = re.sub(r'\b(?:youtube|canais?|v[íi]deos?|perfil|p[áa]gina|abre?|abra|abri[rz]?|aberto)\b', ' ', alvo, flags=re.IGNORECASE)
            resto = re.sub(r'\b(?:o|a|os|as|um|uma|no|na|do|da|dos|das|de|para|pra|mim|por|com|sobre|meu|minha|tal)\b', ' ',
                           resto, flags=re.IGNORECASE).strip()
            resto = re.sub(r'\s+', ' ', resto)
            if resto:
                webbrowser.open('https://www.youtube.com/results?search_query=' + urllib.parse.quote(resto))
                return self._t(f"Abrindo YouTube: busca por {resto}.", f"Opening YouTube: search for {resto}.", lang)
            webbrowser.open('https://www.youtube.com')
            return self._t("Abrindo YouTube no navegador.", "Opening YouTube in browser.", lang)

        # ---- INSTAGRAM de verdade: perfil / post / stories / mensagem ----
        if 'instagram' in chave:
            url = _url_instagram(alvo)
            webbrowser.open(url)
            return self._t(f"Abrindo Instagram: {url}.", f"Opening Instagram: {url}.", lang)

        if 'whatsapp' in chave:
            m = re.search(r'(?:do|da|de|com|with|to)\s+(.+)', alvo, re.IGNORECASE)
            nome = m.group(1).strip() if m else ''
            url = 'https://web.whatsapp.com'
            if nome:
                url += '?search=' + urllib.parse.quote(nome)
            webbrowser.open(url)
            return self._t(f"Abrindo WhatsApp Web. Procure {nome} e envie a mensagem.",
                           f"Opening WhatsApp Web. Look for {nome} and send the message.", lang)

        # ---- PROGRAMA INSTALADO DE VERDADE (acesso total) ----
        if _executar_programa(chave, alvo):
            return self._t(f"Abri o programa {alvo}.", f"Opened the {alvo} app.", lang)

        # ---- URL direta (domínio que o usuário citou) ----
        m = re.search(r'(?:https?://)?(?:www\.)?[a-z0-9-]+\.[a-z]{2,}(?:/\S*)?', alvo, re.IGNORECASE)
        if m and ' ' not in m.group(0).strip():
            url = m.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            webbrowser.open(url)
            return self._t(f"Abrindo {url}.", f"Opening {url}.", lang)
        webbrowser.open('https://www.google.com/search?q=' + urllib.parse.quote(alvo))
        return self._t(f"Buscando {alvo} no Google.", f"Searching {alvo} on Google.", lang)

    def _criar_html(self, cmd, lang):
        """Diretiva [SITE: ...] do cérebro: agenda em segundo plano e usa a resposta curta."""
        try:
            creator.fila_job(cmd, lang)
        except Exception:
            pass
        return self._t('✅ Confirmado. Estou gerando...',
                       '✅ Confirmed. Generating...', lang)

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