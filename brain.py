# Cérebro conversacional do Jarvis: LLM público (sem chave) + memória persistente
# Responde QUALQUER pergunta/tarefa, simples ou complexa, no idioma do usuário,
# e pode devolver diretivas de ação que o Commands executa de verdade no PC.
import json
import os
import re
import time
import urllib.parse
import urllib.request

MEM_DIR = os.path.join(os.path.expanduser('~'), 'Downloads', 'Jarvis', 'memoria')
MEM_FILE = os.path.join(MEM_DIR, 'memoria.jsonl')

SYSTEM = """Você é o JARVIS, assistente pessoal com acesso TOTAL ao computador do usuário (Windows, Administrador, pasta pessoal C:\\Users\\joilton).
Você pensa como um engenheiro de software de cinema: resolve qualquer tarefa, da mais simples à mais complexa (abrir apps/sites, criar projetos em HTML, rodar comandos, automatizar, pesquisar, programar).
REGRAS:
1) Responda SEMPRE no MESMO idioma do usuário (pt-BR ou inglês).
2) Conversa natural, direta e engenhosa, como um Jarvis real. Nunca se reapresente se já conhece o usuário.
3) Perguntas intelectuais: responda com qualidade de engenheiro sênior, completo mas sem enrolação.
4) Se o usuário pedir uma AÇÃO no PC, termine a resposta com no máximo DUAS linhas de diretiva entre colchetes:
[RUN: comando do windows]  [OPEN: site ou "youtube|instagram|whatsapp|google|github"]
[SITE: descrição curta do site/jogo a criar]
Essas diretivas são EXECUTADAS de verdade pelo sistema. Nunca invente a saída de comandos.
5) Hora atual: {now}. Idioma detectado: {ldetect}.
6) Se o texto do usuário for fragmento solto, ruído do microfone ou não fizer sentido, NÃO invente nada e NÃO troque de assunto: responda apenas "Não entendi bem, pode repetir?" (no idioma do usuário).
Você recebe abaixo memória das conversas anteriores; use-a para lembrar preferências e nomes."""


def _post_json(url, payload, timeout=90):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'JarvisLocal/2', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8', errors='replace'))


def _get_text(url, timeout=90):
    req = urllib.request.Request(url, headers={'User-Agent': 'JarvisLocal/2'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', errors='replace')


# ---------------- memória persistente ----------------
def log_user(text, lang=''):
    """Registra TUDO que o usuário falar, sempre, em disco."""
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


def _wiki_answer(text, lang='pt'):
    """Conhecimento garantido via Wikipédia (sem chave) quando os LLMs falham."""
    try:
        dom = 'pt' if lang != 'en' else 'en'
        q = re.sub(r'[?!.]+$', '', text.strip())
        q = re.sub(r'^(quem|o que|qual|when|what|who|where)\s+(?:e|é|foi|são|sao|was|is|are|does|did)?\s*', '', q, flags=re.IGNORECASE).strip()
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


# ---------------- pergunta ao cérebro ----------------
def ask(text, lang_hint='pt'):
    """Retorna (resposta, acoes). acoes = lista de tuplas ('OPEN'|'RUN'|'SITE', valor).
    Se a IA pública não responder: resposta = None (caller usa fallback local)."""
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    want_more = bool(re.search(r'lembr|mem[óo]ria|regist|remeber|remember|historic', text, re.IGNORECASE))
    ldetect = 'português brasileiro' if lang_hint == 'pt' else ('inglês' if lang_hint == 'en' else 'automatico')
    sysmsg = SYSTEM.format(now=now, ldetect=ldetect)
    mem = _load_mem(40, want_more)

    content = None
    for modelo in ('openai', 'mistral'):
        try:
            data = _post_json('https://text.pollinations.ai/openai', {
                'model': modelo,
                'messages': [
                    {'role': 'system', 'content': sysmsg + '\n\nMEMÓRIA RECENTE:\n' + mem},
                    {'role': 'user', 'content': text},
                ],
            }, 32)
            content = data.get('choices', [{}])[0].get('message', {}).get('content')
        except Exception:
            content = None
        if content:
            break
        time.sleep(3)  # API pública gratuita limita chamadas: respirar antes da próxima

    if not content:
        # fallback GET simples (prompt menor)
        try:
            mini_sys = ("Responda no mesmo idioma do usuário, como o JARVIS (assistente com acesso ao PC). "
                        "Se o pedido for ação, termine com [RUN: ...] ou [OPEN: ...] ou [SITE: ...].\n\n"
                        "MEMÓRIA:\n" + mem[-900:] + "\n\nUsuário: " + text)
            content = _get_text('https://text.pollinations.ai/' + urllib.parse.quote(mini_sys), 25)
        except Exception:
            content = None

    if not content:
        # reforço garantido: Wikipedia (API pública, sem chave) para perguntas de conhecimento
        content = _wiki_answer(text, lang_hint)

    if not content:
        return None, []

    acoes = []
    for pat, tipo in ((r'\[(?:RUN|EXEC)\s*:\s*([^\]]+)\]', 'RUN'),
                      (r'\[(?:OPEN|ABRIR)\s*:\s*([^\]]+)\]', 'OPEN'),
                      (r'\[SITE\s*:\s*([^\]]+)\]', 'SITE')):
        for m in re.finditer(pat, content, re.IGNORECASE):
            acoes.append((tipo, m.group(1).strip()))
    reply = re.sub(r'\[[A-Z]{3,6}\s*:[^\]]+\]', '', content, flags=re.IGNORECASE).strip()
    _flush_reply(text, reply)
    return reply, acoes[:2]
