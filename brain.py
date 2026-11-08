# Cérebro conversacional do Jarvis: LLMs (chave própria ou público grátis) + memória persistente
import json
import os
import re
import time
import urllib.parse
import urllib.request

MEM_DIR = os.path.join(os.path.expanduser('~'), 'Downloads', 'Jarvis', 'memoria')
MEM_FILE = os.path.join(MEM_DIR, 'memoria.jsonl')

PROVIDER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api_config.json')

_MODELO_PADRAO = {
    'openai': 'gpt-4o-mini',
    'anthropic': 'claude-sonnet-4-20250514',
    'gemini': 'gemini-2.0-flash',
    'groq': 'llama-3.3-70b-versatile',
    'ollama': 'llama3.2',
}

SYSTEM = """Você é o JARVIS, assistente pessoal com acesso TOTAL ao computador do usuário (Windows, Administrador, pasta pessoal C:\\Users\\joilton).
Você pensa como um engenheiro de software de cinema: resolve qualquer tarefa, da mais simples à mais complexa (abrir apps/sites, criar projetos em HTML, rodar comandos, automatizar, pesquisar, programar).
REGRAS:
1) Responda SEMPRE no MESMO idioma do usuário (pt-BR ou inglês).
2) Conversa natural, direta e engenhosa, como um Jarvis real. Nunca se reapresente se já conhece o usuário.
3) Perguntas intelectuais: responda com a qualidade de um engenheiro sênior, completo mas sem enrolação.
4) Se o usuário pedir uma AÇÃO no PC, termine a resposta com no máximo DUAS linhas de diretiva entre colchetes:
[RUN: comando do windows]  [OPEN: site ou "youtube|instagram|whatsapp|google|github"]
[SITE: descrição curta do site/jogo a criar]
Essas diretivas são EXECUTADAS de verdade pelo sistema. Nunca invente a saída de comandos.
5) Hora atual: {now}. Idioma detectado: {ldetect}.
6) Se o texto do usuário for fragmento solto, ruído do microfone ou não fizer sentido, NÃO invente nada e NÃO troque de assunto: responda apenas "Não entendi bem, pode repetir?" (no idioma do usuário).
Você recebe abaixo memória das conversas anteriores; use-a para lembrar preferências e nomes."""


def _post_json(url, payload, timeout=60, headers=None):
    hh = {'Content-Type': 'application/json', 'User-Agent': 'JarvisLocal/2', 'Accept': 'application/json'}
    if headers:
        hh.update(headers)
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=hh)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8', errors='replace'))


def _get_text(url, timeout=45):
    req = urllib.request.Request(url, headers={'User-Agent': 'JarvisLocal/2'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', errors='replace')


# ---------------- memória persistente ----------------
def log_user(text, lang=''):
    try:
        os.makedirs(MEM_DIR, exist_ok=True)
        with open(MEM_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'lang': lang, 'user': text}, ensure_ascii=False) + '\n')
    except Exception:
        pass


def _flush_reply(user_text, reply):
    try:
        os.makedirs(MEM_DIR, exist_ok=True)
        with open(MEM_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'reply': reply[:800]}, ensure_ascii=False) + '\n')
    except Exception:
        pass


def _load_mem(max_lines=40, want_more=False):
    try:
        with open(MEM_FILE, 'r', encoding='utf-8') as f:
            lines = [l for l in f.read().splitlines() if l.strip()]
    except Exception:
        return ''
    take = lines[-150:] if want_more else lines[-max_lines:]
    out = []
    for l in take:
        try:
            d = json.loads(l)
            if d.get('user'):
                out.append(f"Usuário: {d['user']}")
            elif d.get('reply'):
                out.append(f"JARVIS: {d['reply'][:350]}")
        except Exception:
            continue
    return '\n'.join(out)


# ---------------- provedor de IA (chave do usuário) ----------------
def set_provider(provider, key='', model=''):
    """provider: openai | anthropic | gemini | groq | ollama | auto (grátis público)"""
    cfg = {'provider': provider, 'key': key or '', 'model': model or _MODELO_PADRAO.get(provider, '')}
    try:
        with open(PROVIDER_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False)
    except Exception:
        pass
    return {'ok': True, 'provider': provider, 'model': cfg['model']}


def get_provider():
    try:
        with open(PROVIDER_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        key = cfg.get('key') or ''
        return {'provider': cfg.get('provider', 'auto'),
                'model': cfg.get('model') or _MODELO_PADRAO.get(cfg.get('provider', ''), ''),
                'key_hint': (key[:4] + '…' + key[-4:]) if len(key) > 8 else ''}
    except Exception:
        return {'provider': 'auto', 'model': '', 'key_hint': ''}


_MODEL_CACHE = {}


def _groq_pick_model(model):
    """Groq depreca modelos com frequência: consulta a lista real e escolhe o melhor disponível."""
    try:
        if 'groq' not in _MODEL_CACHE:
            with open(PROVIDER_FILE, 'r', encoding='utf-8') as f:
                key = json.load(f).get('key', '')
            req = urllib.request.Request('https://api.groq.com/openai/v1/models',
                                         headers={'Authorization': 'Bearer ' + key,
                                                  'User-Agent': 'JarvisLocal/2'})
            with urllib.request.urlopen(req, timeout=15) as r:
                ids = [m.get('id', '') for m in json.loads(r.read().decode('utf-8', errors='replace')).get('data', [])]
            ids = [i for i in ids if not re.search(r'whisper|tts|guard|embed|playai|distil', i, re.I)]
            if ids:
                _MODEL_CACHE['groq'] = ids
        lista = _MODEL_CACHE.get('groq') or []
        if model in lista:
            return model
        for pref in ('llama-3.3-70b', 'llama-3.3', '70b', 'llama-3.1-8b-instant', 'gpt-oss', 'llama'):
            for i in lista:
                if pref in i.lower():
                    return i
        return lista[0] if lista else model
    except Exception:
        return model


def _call_provider(cfg, sysmsg, mem, text, max_tokens=1500):
    prov = cfg.get('provider')
    model = cfg.get('model') or _MODELO_PADRAO.get(prov, '')
    if prov == 'groq':
        model = _groq_pick_model(model)
    key = cfg.get('key') or ''
    if prov in ('openai', 'groq', 'ollama'):
        url = {'openai': 'https://api.openai.com/v1/chat/completions',
               'groq': 'https://api.groq.com/openai/v1/chat/completions',
               'ollama': 'http://localhost:11434/v1/chat/completions'}[prov]
        headers = {'Authorization': 'Bearer ' + key} if prov != 'ollama' else {}
        d = _post_json(url, {'model': model,
                             'messages': [{'role': 'system', 'content': sysmsg + '\n\nMEMÓRIA RECENTE:\n' + mem},
                                          {'role': 'user', 'content': text}],
                             'max_tokens': max_tokens}, 90, headers)
        return (d.get('choices', [{}])[0].get('message', {}) or {}).get('content')
    if prov == 'anthropic':
        d = _post_json('https://api.anthropic.com/v1/messages',
                       {'model': model, 'max_tokens': max_tokens,
                        'system': sysmsg + '\n\nMEMÓRIA RECENTE:\n' + mem,
                        'messages': [{'role': 'user', 'content': text}]}, 90,
                       {'x-api-key': key, 'anthropic-version': '2023-06-01'})
        parts = (d.get('content') or [{}])[0].get('text')
        return parts
    if prov == 'gemini':
        url = (f'https://generativelanguage.googleapis.com/v1beta/models/{model}:'
               f'generateContent?key={urllib.parse.quote(key)}')
        d = _post_json(url, {
            'systemInstruction': {'parts': [{'text': sysmsg + '\n\nMEMÓRIA RECENTE:\n' + mem}]},
            'contents': [{'role': 'user', 'parts': [{'text': text}]}],
            'generationConfig': {'maxOutputTokens': max_tokens}}, 90)
        parts = d.get('candidates', [{}])[0].get('content', {}).get('parts', [])
        return parts[0].get('text') if parts else None
    return None


# ---------------- reforço: Wikipédia ----------------
def _wiki_answer(text, lang='pt'):
    try:
        dom = 'pt' if lang != 'en' else 'en'
        q = re.sub(r'[?!.]+$', '', text.strip())
        q = re.sub(r'^(quem|o que|qual|quando|onde|por\s*que|porque|what|who|where|when|why)\s+(?:e|é|foi|são|sao|was|is|are|does|did)?\s*',
                   '', q, flags=re.IGNORECASE).strip()
        if len(q) < 6:
            return None  # lixo/fragmento não vai para a Wikipédia
        if re.search(r'\b(abri[rz]?|abra|abre|criar|crie|cria|executar|rodar|tocar|gerar|gere|gera|montar|monte|monta|open|create|run|play)\b', q, re.IGNORECASE):
            return None  # pedidos de AÇÃO não são perguntas de conhecimento
        u = f'https://{dom}.wikipedia.org/w/rest.php/v1/search/page?q={urllib.parse.quote(q)}&limit=1'
        req = urllib.request.Request(u, headers={'User-Agent': 'JarvisLocal/2'})
        with urllib.request.urlopen(req, timeout=12) as r:
            res = json.loads(r.read().decode('utf-8', errors='replace'))
        if not res.get('pages'):
            return None
        title = urllib.parse.quote(res['pages'][0]['key'])
        u2 = f'https://{dom}.wikipedia.org/api/rest_v1/page/summary/{title}'
        req2 = urllib.request.Request(u2, headers={'User-Agent': 'JarvisLocal/2'})
        with urllib.request.urlopen(req2, timeout=12) as r2:
            smry = json.loads(r2.read().decode('utf-8', errors='replace'))
        extract = smry.get('extract')
        if not extract:
            return None
        fonte = smry.get('content_urls', {}).get('desktop', {}).get('page', '')
        return '📖 ' + extract + (f'\n\nFonte: {fonte}' if fonte else '')
    except Exception:
        return None


def _eh_pergunta_de_fato(text):
    return bool(re.match(r'^\s*(quem|o que|qual|quais|quando|onde|por\s*que|porque|significado|defini[çc][ãa]o|hist[óo]ria de)',
                         text.strip(), re.IGNORECASE))


def _quick_chat(syscontent, usercontent, timeout, max_tokens=1500):
    """Chat rápido: provedor do usuário (se configurado) senão público gratuito."""
    cfg = get_provider()
    if cfg.get('provider') not in (None, '', 'auto') and (cfg.get('key_hint') or cfg.get('provider') == 'ollama'):
        try:
            with open(PROVIDER_FILE, 'r', encoding='utf-8') as f:
                cfg_real = json.load(f)
            r = _call_provider(cfg_real, syscontent, '', usercontent, max_tokens=max_tokens)
            if r:
                return r
        except Exception:
            pass
    try:
        d = _post_json('https://text.pollinations.ai/openai', {
            'model': 'openai',
            'max_tokens': max_tokens,
            'messages': [{'role': 'system', 'content': syscontent},
                         {'role': 'user', 'content': usercontent}]}, timeout)
        return d.get('choices', [{}])[0].get('message', {}).get('content')
    except Exception:
        return None


def correct_transcript(text):
    """Conserta a transcrição do Google (nomes próprios/slangelados errados: 'mister coin' -> nome real)."""
    if not text or len(text.strip()) < 4 or len(text) > 300:
        return text
    sys = ("Você recebe uma transcrição de voz (pt-BR ou inglês) feita pelo reconhecedor do Google, "
           "que erra nomes próprios e gírias. Corrija APENAS erros óbvios de ditado mantendo o sentido EXATO, "
           "o idioma e o formato de comando. Devolva SOMENTE o texto corrigido, sem explicação, sem aspas.")
    try:
        r = _quick_chat(sys, text, 14)
        if r:
            r = r.strip().strip('"').strip()
            if r and 4 <= len(r) <= 300:
                return r
    except Exception:
        pass
    return text


def generate_site(cmd, lang='pt'):
    """Gera um site/aplicativo ÚNICO-PESONALIZADO pela IA (não template). Devolve HTML ou None."""
    sysp = ("Você gera SITES/APLICATIVOS HTML completos em UM ÚNICO arquivo, no idioma do usuário. "
            "Siga EXATAMENTE o que ele pediu (tema, cores, textos, nome específicos). "
            "Faça VISUALMENTE EXCELENTE: CSS moderno, animações suaves, particles/emojis, tipografia, responsivo. "
            "Devolva APENAS o código HTML completo começando por <!DOCTYPE html>, sem explicações e sem blocos markdown.")
    try:
        out = _quick_chat(sysp, cmd, 120)
        if not out:
            return None
        m = re.search(r'```(?:html)?\s*(<!DOCTYPE[\s\S]*?</html>)\s*```', out, re.IGNORECASE)
        if m:
            out = m.group(1)
        out = out.strip()
        if '<!doctype' not in out.lower()[:300] and '<html' not in out.lower()[:300]:
            return None
        return out
    except Exception:
        return None


def generate_project(cmd, lang='pt'):
    """Gera um PROJETO COMPLETO organizado: devolve JSON {nome, descricao, html, css, js} ou None."""
    sysp = ("Você é um ENGENHEIRO DE PRODUTO SÊNIOR. O usuário pede um projeto (site, jogo, app, ferramenta, "
            "tabela etc.) para abrir no navegador. Construa o projeto COMPLETO, POLIDO e FUNCIONAL: "
            "design bonito e moderno, código limpo, comentado em português simples, sem bugs, responsivo, "
            "microinterações e textos no idioma do usuário. Cumpra EXATAMENTE cada detalhe do pedido. "
            "Projete com carinho como quem entrega pronto pra produção.\n"
            "Devolva APENAS um JSON VÁLIDO (sem markdown, sem comentários) neste formato:\n"
            '{"nome": "nome curto do projeto", "descricao": "1-2 frases fáceis explicando o que faz", '
            '"html": "<!DOCTYPE html> ... página que referencia css/style.css e js/script.js (caminhos relativos, <head> e <body> completos)", '
            '"css": "TODO o CSS separado (nada inline)", "js": "TODO o JavaScript separado ou \'\'"}')
    try:
        out = _quick_chat(sysp, cmd, 180, max_tokens=8000)
        if not out:
            return None
        if '{' not in out or '}' not in out:
            return None
        return out  # o parser fica no creator.py (split por CSV não; JSON cru)
    except Exception:
        return None


def analyze_image(path, question=''):
    """Lê/analisa imagens com IA de visão (chave própria ou público)."""
    from base64 import b64encode
    from pathlib import Path
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return "Arquivo não encontrado: " + str(path)
        mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.webp': 'image/webp', '.gif': 'image/gif', '.bmp': 'image/bmp'}
        ext = p.suffix.lower()
        if ext not in mime:
            return "Formato não suportado para análise visual."
        if p.stat().st_size > 8 * 1024 * 1024:
            return "Imagem grande demais para analisar (limite 8MB)."
        data = 'data:' + mime[ext] + ';base64,' + b64encode(p.read_bytes()).decode('ascii')
        pergunta = question or "Descreva esta imagem em detalhes, em português."
        sysp = "Você é a visão do JARVIS: analisa imagens com precisão e no idioma do usuário."

        cfg = get_provider()
        if cfg.get('provider') == 'anthropic':
            with open(PROVIDER_FILE, 'r', encoding='utf-8') as f:
                cfg_real = json.load(f)
            d = _post_json('https://api.anthropic.com/v1/messages',
                           {'model': cfg_real.get('model') or 'claude-sonnet-4-20250514', 'max_tokens': 1500,
                            'system': sysp,
                            'messages': [{'role': 'user', 'content': [
                                {'type': 'image', 'source': {'type': 'base64', 'media_type': mime[ext],
                                                             'data': data.split(',', 1)[1]}},
                                {'type': 'text', 'text': pergunta}]}]}, 90,
                           {'x-api-key': cfg_real.get('key', ''), 'anthropic-version': '2023-06-01'})
            return (d.get('content') or [{}])[0].get('text')
        if cfg.get('provider') == 'gemini':
            with open(PROVIDER_FILE, 'r', encoding='utf-8') as f:
                cfg_real = json.load(f)
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{cfg_real.get('model') or 'gemini-2.0-flash'}:generateContent?key={urllib.parse.quote(cfg_real.get('key', ''))}")
            d = _post_json(url, {'contents': [{'role': 'user', 'parts': [
                {'inline_data': {'mime_type': mime[ext], 'data': data.split(',', 1)[1]}},
                {'text': pergunta}]}]}, 90)
            parts = d.get('candidates', [{}])[0].get('content', {}).get('parts', [])
            return parts[0].get('text') if parts else None

        # openai, groq, auto (grátis) e ollama: formato OpenAI com image_url (base64 data URI)
        provider = cfg.get('provider')
        url = 'https://text.pollinations.ai/openai'
        headers = {}
        model = 'openai'
        if provider == 'openai':
            url = 'https://api.openai.com/v1/chat/completions'
            with open(PROVIDER_FILE, 'r', encoding='utf-8') as f:
                cfg_real = json.load(f)
            headers = {'Authorization': 'Bearer ' + cfg_real.get('key', '')}
            model = cfg_real.get('model') or 'gpt-4o-mini'
        d = _post_json(url, {'model': model, 'max_tokens': 1200, 'messages': [
            {'role': 'system', 'content': sysp},
            {'role': 'user', 'content': [{'type': 'text', 'text': pergunta},
                                         {'type': 'image_url', 'image_url': {'url': data}}]}]}, 90, headers)
        return (d.get('choices', [{}])[0].get('message', {}) or {}).get('content')
    except Exception:
        return None


# ---------------- pergunta ao cérebro ----------------
def ask(text, lang_hint='pt'):
    """Retorna (resposta, acoes). acoes = lista de tuplas ('OPEN'|'RUN'|'SITE', valor)."""
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    want_more = bool(re.search(r'lembr|mem[óo]ria|regist|remember|historic', text, re.IGNORECASE))
    ldetect = 'português brasileiro' if lang_hint == 'pt' else ('inglês' if lang_hint == 'en' else 'automático')
    sysmsg = SYSTEM.format(now=now, ldetect=ldetect)
    mem = _load_mem(40, want_more)

    content = None

    # 1) Provedor do usuário (OpenAI / Anthropic / Gemini / Groq / Ollama) — inteligência de primeira linha
    cfg = get_provider()
    if cfg.get('provider') not in (None, '', 'auto') and (cfg.get('key_hint') or cfg.get('provider') == 'ollama'):
        try:
            with open(PROVIDER_FILE, 'r', encoding='utf-8') as f:
                cfg_real = json.load(f)
            content = _call_provider(cfg_real, sysmsg, mem, text)
        except Exception:
            content = None

    # 2) Pergunta de fato → Wikipédia imediato (1-2s)
    if not content and _eh_pergunta_de_fato(text):
        content = _wiki_answer(text, lang_hint)

    # 3) Grátis público (pollinations) — rápido quando disponível
    if not content:
        for modelo in ('openai', 'mistral'):
            try:
                data = _post_json('https://text.pollinations.ai/openai', {
                    'model': modelo,
                    'messages': [
                        {'role': 'system', 'content': sysmsg + '\n\nMEMÓRIA RECENTE:\n' + mem},
                        {'role': 'user', 'content': text},
                    ],
                }, 28)
                content = data.get('choices', [{}])[0].get('message', {}).get('content')
            except Exception:
                content = None
            if content:
                break
            time.sleep(2)

    # 4) Último reforço: Wikipédia SOMENTE para perguntas de fato (evita lixo aleatório)
    if not content and _eh_pergunta_de_fato(text):
        content = _wiki_answer(text, lang_hint)

    if not content:
        return None, []

    acoes = []
    for pat, tipo in ((r'\[(?:RUN|EXEC)\s*:\s*([^\]]+)\]', 'RUN'),
                      (r'\[(?:OPEN|ABRIR)\s*:\s*([^\]]+)\]', 'OPEN'),
                      (r'\[SITE\s*:\s*([^\]]+)\]', 'SITE')):
        for m in re.finditer(pat, content, re.IGNORECASE):
            acoes.append((tipo, m.group(1).strip()))
    reply = re.sub(r'\[(?:RUN|EXEC|OPEN|ABRIR|SITE)\s*:[^\]]+\]', '', content, flags=re.IGNORECASE).strip()
    _flush_reply(text, reply)
    return reply, acoes[:2]
