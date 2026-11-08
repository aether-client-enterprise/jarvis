# Gerenciador de criações do Jarvis: qualquer pedido de projeto (site/jogo/app/...)
# vira TAREFA em segundo plano — responde "confirmado" na hora, trabalha devagar e
# entrega projeto ORGANIZADO EM PASTAS, e anota onde ficou para contar depois (resumo curto).
import json
import os
import re
import threading
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from jarvis import brain
from jarvis.templates_site import site_html

RAIZ = Path.home() / 'Downloads' / 'Jarvis' / 'Projetos'
ESTADO_FILE = RAIZ / 'criacoes.json'

_trava = threading.Lock()
_tarefas = {}

TEMA = [('romantic|amor|namora|cora[çc][ãa]o|beijo', 'romantico'),
        ('natureza|floresta|verde|jardim|planta', 'natureza'),
        ('espac|galaxis?|galaxia|estrela|cosmos', 'espaco')]


def _carregar():
    try:
        with open(ESTADO_FILE, 'r', encoding='utf-8') as f:
            for k, v in json.load(f).items():
                _tarefas[str(k)] = v
    except Exception:
        pass


def _salvar():
    try:
        os.makedirs(RAIZ, exist_ok=True)
        with open(ESTADO_FILE, 'w', encoding='utf-8') as f:
            json.dump(_tarefas, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


_carregar()


def _slug(nome):
    s = unicodedata.normalize('NFKD', (nome or '')).encode('ascii', 'ignore').decode('ascii')
    s = re.sub(r'[^a-z0-9]+', '-', s.strip().lower()).strip('-')
    s = re.sub(r'-{2,}', '-', s)
    return (s[:38] or 'projeto') + '_' + datetime.now().strftime('%d%m%Y-%H%M')


def fila_job(prompt, lang='pt'):
    """Agenda a criação; devolve id. O trabalho roda em thread e NÃO trava a resposta."""
    jd = {'id': str(int(time.time() * 1000)),
          'prompt': (prompt or '')[:4000],
          'lang': lang or 'pt',
          'status': 'fazendo',
          'nome': 'projeto',
          'pasta': '',
          'resumo': '',
          'erro': ''}
    with _trava:
        _tarefas[jd['id']] = jd
        _salvar()
    threading.Thread(target=_executar, args=(jd['id'],), daemon=True).start()
    return jd['id']


def tem_ultimo():
    """Há qualquer registro (gerando, pronto ou erro)? Para dar resumo imediato."""
    return bool(_tarefas)


def status():
    """Lista resumida para o endpoint /criacoes (a HUD mostra quando ficar pronto)."""
    itens = sorted(_tarefas.values(), key=lambda t: t.get('id', ''), reverse=True)
    return {'projetos': [{'id': t['id'], 'nome': t.get('nome'), 'status': t.get('status'),
                          'pasta': t.get('pasta'), 'resumo': t.get('resumo'),
                          'erro': t.get('erro')} for t in itens[:8]]}


def resumo(lang='pt'):
    """Resumo CURTO e fácil do que o Jarvis fez (só quando perguntam o que ele fez)."""
    itens = sorted(_tarefas.values(), key=lambda t: t.get('id', ''), reverse=True)
    prontos = [t for t in itens if t.get('status') == 'pronto']
    fazendo = [t for t in itens if t.get('status') == 'fazendo']
    erros = [t for t in itens if t.get('status') == 'erro']

    if not itens:
        if lang == 'en':
            return "I haven't created anything yet. Ask me to build something and I'll tell you where it is."
        return "Ainda não criei nada por aqui. Me peça pra criar algo que eu gero e te mostro onde ficou."

    def linha(t):
        if t['status'] == 'pronto':
            return f"✔ {t['nome']} — criado em \"{t['pasta']}\" · abra o index.html"
        if t['status'] == 'fazendo':
            return f"⏳ {t['nome']} — ainda estou gerando..."
        return f"⚠️ {t['nome']} — deu problema: {t.get('erro') or '?'}"

    linhas = [linha(t) for t in fazendo] + [linha(t) for t in (prontos + erros)[:2]]
    msg = '\n'.join(linhas)
    if lang != 'en' and erros:
        msg += "\nSe algum deu erro, fale \"tenta de novo\" e eu tento por outro jeito."
    return msg


def _parse_json(out):
    s = re.sub(r'```(?:json)?', '', out or '').replace('```', '').strip()
    try:
        return json.loads(s)
    except Exception:
        pass
    m = re.search(r'\{[\s\S]*\}', s)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def _ler_projeto_da_ia(prompt, lang):
    """Pede à IA o projeto em partes (html/css/js) e devolve dict ou None."""
    try:
        out = brain.generate_project(prompt, lang)
        if not out:
            return None
        d = _parse_json(out)
        if not d:
            return None
        html = (d.get('html') or '').strip()
        css = (d.get('css') or '').strip()
        if not html or '<html' not in html.lower() or not css:
            return None
        return {'nome': (d.get('nome') or 'Projeto Jarvis').strip()[:60],
                'descricao': (d.get('descricao') or '').strip(),
                'html': html if '<!doctype' in html.lower()[:250] else '<!DOCTYPE html>\n' + html,
                'css': css, 'js': (d.get('js') or '').strip(), 'offline': False}
    except Exception:
        return None


def _executar(jid):
    """Thread de trabalho: gera o projeto COMPLETO, organizado em pastas, e registra onde ficou."""
    with _trava:
        job = _tarefas.get(jid)
    if not job:
        return
    try:
        # --- 1) Conteúdo ---
        proj = _ler_projeto_da_ia(job['prompt'], job.get('lang', 'pt'))
        if not proj:
            html = None
            try:
                html = brain.generate_site(job['prompt'], job.get('lang', 'pt'))
            except Exception:
                html = None
            if not html:
                baixo = job['prompt'].lower()
                tema = 'cyberpunk'
                for rx, t in TEMA:
                    if re.search(rx, baixo):
                        tema = t
                        break
                html = site_html(tema)
            proj = {'nome': 'Projeto Jarvis (uma página)',
                    'descricao': 'Sem IA disponível no momento: ficou em página única, mas funcionando.',
                    'html': html, 'css': '', 'js': '', 'offline': True}

        # --- 2) Pastas organizadas ---
        pasta = RAIZ / _slug(proj['nome'])
        pasta.mkdir(parents=True, exist_ok=True)
        for sub in ('css', 'js', 'assets'):
            (pasta / sub).mkdir(exist_ok=True)

        html, css, js = proj['html'], proj['css'], proj['js']
        if css:
            html = re.sub(r'<style[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
            html = html.replace('</head>', '  <link rel="stylesheet" href="css/style.css">\n</head>') \
                if '</head>' in html else html + '\n<link rel="stylesheet" href="css/style.css">'
        if js:
            html = re.sub(r'\s*<script>[\s\S]*?</script>\s*(?=</body>|</html>)', '\n', html, flags=re.IGNORECASE)
            html = html.replace('</body>', '  <script src="js/script.js"></script>\n</body>') \
                if '</body>' in html else html + '\n<script src="js/script.js"></script>'

        (pasta / 'index.html').write_text(html, encoding='utf-8')
        if css:
            (pasta / 'css' / 'style.css').write_text(css, encoding='utf-8')
        (pasta / 'js' / 'script.js').write_text(js or '// lógica do projeto (vazia)\n', encoding='utf-8')
        (pasta / 'assets' / '.gitkeep').touch()
        readme = (
            f"# {proj['nome']}\n"
            f"Criado pelo **Jarvis** em {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            f"## O que é\n{proj['descricao'] or job['prompt'][:220]}\n\n"
            "## Como está organizado\n"
            "- `index.html` → é A PÁGINA (abra este em duplo clique)\n"
            "- `css/style.css` → todo o visual\n"
            "- `js/script.js` → toda a lógica\n"
            "- `assets/` → imagens e arquivos extras\n\n"
            "## Como usar\n"
            "Abra o `index.html` em qualquer navegador. Nada de instalação."
        )
        (pasta / 'README.md').write_text(readme, encoding='utf-8')

        # --- 3) Registra onde ficou ---
        with _trava:
            job.update({'nome': proj['nome'],
                        'pasta': str(pasta),
                        'resumo': f"{proj['nome']} — pronto em \"{pasta}\" · abra o index.html",
                        'status': 'pronto', 'erro': ''})
            _salvar()
        try:
            brain.log_user('[jarvis] Criei o projeto: ' + job['resumo'], job.get('lang', 'pt'))
        except Exception:
            pass
    except Exception as e:
        with _trava:
            job.update({'status': 'erro', 'erro': str(e)[:180], 'resumo': '',
                        'nome': job.get('nome') or 'projeto'})
            _salvar()
