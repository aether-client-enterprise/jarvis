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


def _call_provider(cfg, sysmsg, mem, text):
    prov = cfg.get('provider')
    model = cfg.get('model') or _MODELO_PADRAO.get(prov, '')
    key = cfg.get('key') or ''
    if prov in ('openai', 'groq', 'ollama'):
        url = {'openai': 'https://api.openai.com/v1/chat/completions',
               'groq': 'https://api.groq.com/openai/v1/chat/completions',
               'ollama': 'http://localhost:11434/v1/chat/completions'}[prov]
        headers = {'Authorization': 'Bearer ' + key} if prov != 'ollama' else {}
        d = _post_json(url, {'model': model,
                             'messages': [{'role': 'system', 'content': sysmsg + '\n\nMEMÓRIA RECENTE:\n' + mem},
                                          {'role': 'user', 'content': text}],
                             'max_tokens': 1500}, 90, headers)
        return (d.get('choices', [{}])[0].get('message', {}) or {}).get('content')
    if prov == 'anthropic':
        d = _post_json('https://api.anthropic.com/v1/messages',
                       {'model': model, 'max_tokens': 1500,
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
            'generationConfig': {'maxOutputTokens': 1500}}, 90)
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

    # 4) Último reforço: Wikipédia para qualquer frase
    if not content:
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
