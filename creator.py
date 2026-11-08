# Gerenciador de criações do Jarvis: qualquer pedido de projeto (site/jogo/app/...)
# vira TAREFA em segundo plano — responde "confirmado" na hora, trabalha devagar e
# entrega projeto ORGANIZADO EM PASTAS, e anota onde ficou para contar depois (resumo curto).
import json
import os
import random
import re
import threading
import time
import unicodedata
import urllib.parse
from datetime import datetime
from pathlib import Path

from jarvis import brain

RAIZ = Path.home() / 'Downloads' / 'Jarvis' / 'Projetos'
ESTADO_FILE = RAIZ / 'criacoes.json'

_trava = threading.Lock()
_tarefas = {}


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


def _vigia():
    """Jobs 'fazendo' há mais de 15 min (thread morta/travada) viram erro e saem do loop."""
    limite_ms = 25 * 60 * 1000
    agora_ms = int(time.time() * 1000)
    mudou = False
    with _trava:
        for t in _tarefas.values():
            if t.get('status') == 'fazendo':
                try:
                    if agora_ms - int(t.get('id', '0')) > limite_ms:
                        t['status'] = 'erro'
                        t['erro'] = 'geração passou do tempo — peça "tenta de novo" para eu refazer'
                        mudou = True
                except Exception:
                    pass
        if mudou:
            _salvar()


def tem_ultimo():
    """Há qualquer registro (gerando, pronto ou erro)? Para dar resumo imediato."""
    return bool(_tarefas)


def status():
    """Lista resumida para o endpoint /criacoes (a HUD mostra quando ficar pronto)."""
    _vigia()
    itens = sorted(_tarefas.values(), key=lambda t: t.get('id', ''), reverse=True)
    return {'projetos': [{'id': t['id'], 'nome': t.get('nome'), 'status': t.get('status'),
                          'pasta': t.get('pasta'), 'resumo': t.get('resumo'),
                          'erro': t.get('erro')} for t in itens[:8]]}


def resumo(lang='pt'):
    """Resumo CURTO e fácil do que o Jarvis fez (só quando perguntam o que ele fez)."""
    _vigia()
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


# ---------------- imagens por IA (grátis, sem chave): a foto vira O QUE VOCÊ PEDIU ----------------
IMG_URL = 'https://image.pollinations.ai/prompt/'


def _img(descricao_en, w=800, h=600, seed=None):
    s = seed if seed is not None else random.randint(1, 999999)
    return f"{IMG_URL}{urllib.parse.quote(descricao_en)}?width={w}&height={h}&nologo=true&seed={s}"


def _gerar_projeto_bem(prompt, lang):
    """Pipeline de ALTA QUALIDADE em etapas (nível Lovable/Claude Code):
    1 PLANO → 2 HTML → 3 CSS → 4 JS. Cada etapa é uma resposta de texto puro cheia,
    o que evita JSON quebrado e entrega MUITO mais código e capricho."""
    idioma = 'português do Brasil' if (lang or 'pt') != 'en' else 'English'
    meta = _parse_json(brain.gerar_parte(
        "Você é o ARQUITETO de produto. Planeja sites/apps de nível LOVABLE. "
        "Responda APENAS um JSON válido com as chaves: nome (curto, criativo), "
        "descricao (1-2 frases fáceis no idioma do usuário), secoes (lista de seções/páginas), "
        "paleta (3-5 cores hex harmoniosas), vibe (1 frase: clima visual, tipografia, movimento), "
        "imagens (lista de 2-5 descrições EM INGLÊS curtas para fotos do tema, ex: 'white sneaker "
        "product photo studio background'), funcional (lista de 3-6 funções JS necessárias).",
        "Projeto pedido: " + prompt, 90, 800)) or {}

    nome = (meta.get('nome') or 'Projeto Jarvis').strip()[:60]
    descricao = (meta.get('descricao') if isinstance(meta, dict) else '') or prompt[:160]
    paleta = meta.get('paleta') if isinstance(meta, dict) else None
    secoes = meta.get('secoes') if isinstance(meta, dict) else None
    vibe = meta.get('vibe') if isinstance(meta, dict) else ''
    imagens = (meta.get('imagens') if isinstance(meta, dict) else None) or []
    lista_img = '; '.join(imagens[:5])
    fundos = [{'desc': d, 'url': _img(d), 'mini': _img(d, 400, 300)} for d in imagens[:5]]

    # ---------- HTML ----------
    sys_html = (
        "Você é um ENGENHEIRO FRONT-END SÊNIOR (nível LOVABLE / Claude Code). Gere o "
        "index.html COMPLETO do projeto pedido. REGRAS DE OURO: "
        "1) HTML5 semântico; <head> com <link rel='stylesheet' href='css/style.css'> e "
        "<script src='js/script.js' defer></script>; fonte do Google Fonts que combine com a vibe; "
        "2) TODAS as imagens usam EXATAMENTE URLs deste formato (IA de imagem grátis, SEM unsplash "
        "e SEM picsum): https://image.pollinations.ai/prompt/<DESCRICAO-EM-INGLES-URL-ENCODED>"
        "?width=800&height=600&nologo=true&seed=1 — mude a descrição para o que a foto deve "
        "mostrar (produto, hero, personagens...) e varie o seed= para cada foto diferente; "
        "alt em português; "
        "3) Estrutura caprichada: header fixo com navegação + logo, hero IMPACTANTE com título "
        "grande e chamada, seções em cards com espaço em branco bom, rodapé completo; "
        "4) Use ids/classes SEMÂNTICAS que o CSS e o JS vão consumir; "
        "5) Textos REAIS do tema (nada de Lorem ipsum) no idioma do usuário. "
        f"Devolva APENAS o código HTML completo. Idioma: {idioma}. "
        "6) MÍNIMO 200 linhas: TODAS as seções do plano com conteúdo REAL e DENSOS, "
        "com no mínimo 8 <img> em URLs no formato do item 2. "
        "7) NUNCA escreva frases de explicação: só código do <DOCTYPE> até </html>.")
    pedido_html = (f"PLANO APROVADO:\n{json.dumps(meta, ensure_ascii=False)}\n"
                   f"PEDIDO ORIGINAL: {prompt}")
    html = brain.gerar_parte(sys_html, pedido_html, 170, 8000) or ''
    if len(html) < 2500 or 'pollinations' not in html or html.lower().count('<img') < 6:
        urls = '\n'.join(f'<img src="{f["url"]}" alt="{d[:80]}">'
                         for d, f in zip(imagens, fundos) if isinstance(f, dict))
        html2 = brain.gerar_parte(
            sys_html + " SUA ANTERIOR RESPOSTA FOI CURTA E SEM IMAGENS. Refaça COMPLETO: no mínimo "
            "200 linhas, todas as seções DENSAS e estas URLs de imagem obrigatórias (copie-as nas <img>):\n"
            + urls + "\n" + pedido_html, 170, 8000) or ''
        if len(html2) > len(html):
            html = html2
    if not html or 'html' not in html.lower()[:400]:
        return None

    # ---------- CSS ----------
    sys_css = (
        "Você é um DESIGNER + front-end sênior (nível LOVABLE/award-winning). Escreva o "
        "css/style.css COMPLETO do projeto. OBRIGATÓRIO: variáveis de cores (paleta informada), "
        "reset, tipografia expressiva (clamps fluidos), header fixo com blur/glass, hero com "
        "gradiente em camadas e formas suaves, cards com sombras em camadas + arredondamentos "
        "generosos, hover states com microinterações (transform, transition cubic-bezier), "
        "animações de entrada (@keyframes, IntersectionObserver-ready classes .revela), "
        "scrollbar estilizada, dark elegante quando a paleta pedir, TOTALMENTE responsivo "
        "(breakpoints 1024/768/480), e detalhes: botões com brilho, badges, gradientes de texto. "
        "ZERO conteúdo visual de 2010: nada de bordas cinzas sólidas, nada de tabelas. "
        "MÍNIMO 200 linhas reais de CSS. Devolva APENAS o CSS.")
    css_resumo = (json.dumps(paleta, ensure_ascii=False) if paleta else '') + ' | ' + vibe
    pedido_css = f"PALETA/VIBE: {css_resumo}\nPEDIDO: {prompt}"
    css = brain.gerar_parte(sys_css, pedido_css, 170, 8000) or ''
    if len(css) < 3000 or '--' not in css:
        css2 = brain.gerar_parte(
            sys_css + " SUA ANTERIOR RESPOSTA FOI CURTA/POBRE. Entrega técnica completa nível "
            "Lovable, mínimo 220 linhas, todas as classes usadas pelo HTML do projeto.",
            pedido_css, 170, 8000) or ''
        if len(css2) > len(css):
            css = css2
    if '{' not in css:
        css = brain.gerar_parte(
            'Escreva CSS moderno e BONITO (variáveis, gradientes, glass, animações, responsivo) '
            'para o site descrito. Devolva APENAS o CSS.',
            f"Site: {(meta.get('vibe') if isinstance(meta, dict) else '') or prompt}", 120, 6000) or ''

    # ---------- JS ----------
    sys_js = (
        "Você é um ENGINHEIRO JS sênior. Escreva o js/script.js COMPLETO e FUNCIONAL do projeto. "
        "Requisitos: vanilla JS moderno, organizado em seções comentadas, sem dependências; "
        "tudo que a página promete tem que FUNCIONAR (carrinho, filtros, busca, formulário com "
        "validação, jogo com teclado/toque, salvar em localStorage, render de listas a partir de "
        "arrays de dados dinâmicos, contadores, modal, toast). Inclua sempre: revela-on-scroll "
        "(IntersectionObserver), botão 'voltar ao topo' e estados decarregamento suaves. "
        "Devolva APENAS o JavaScript.")
    pedido_js = (f"SECOES/FUNCIONALIDADES: {json.dumps((meta.get('secoes') if isinstance(meta, dict) else []) + (meta.get('funcional') if isinstance(meta, dict) else []), ensure_ascii=False)}\n"
                 f"PEDIDO: {prompt}")
    js = brain.gerar_parte(sys_js + " No mínimo 150 linhas reais, com dados de exemplo coerentes.",
                           pedido_js, 150, 6000) or ''
    if len(js) < 1500:
        js2 = brain.gerar_parte(sys_js + " SUA ANTERIOR FOI CURTA. Entrega completa: mínimo 180 "
                                "linhas, todas as funções do pedido implementadas de verdade.",
                                pedido_js, 150, 6000) or ''
        if len(js2) > len(js):
            js = js2

    return {'nome': nome, 'descricao': descricao, 'html': html, 'css': css, 'js': js,
            'offline': False, 'fundos': fundos}


def _pagina_emergencia(prompt, lang):
    """Fallback DECENTE (nunca feio): página única caprichada com arte por IA e visual atual."""
    nome, _ = '//Projeto Jarvis', prompt[:80]
    img_hero = _img('elegant abstract gradient shapes premium product photography, soft light, '
                    'high detail', 1200, 700, seed=7)
    titulo = (prompt.strip().capitalize() or 'Projeto Jarvis')[:70]
    lang_en = (lang or 'pt') == 'en'
    fx = ('Estou com dificuldade de conexão com a IA de profundo agora — esta é uma versão '
          'elegante e estática; me peça "tenta de novo" e eu gero a versão completa e interativa.'
          if lang_en else
          'Conexão com a IA profunda indisponível agora — esta é uma versão elegante e estática; '
          'me peça "tenta de novo" e eu gero a versão completa e interativa.')
    html = f"""<!DOCTYPE html>
<html lang="{'en' if lang_en else 'pt-BR'}">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titulo}</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<header class="topo"><span class="logo">✦ {titulo[:24]}</span><button class="btn-topo" onclick="document.getElementById('cta').scrollIntoView({{behavior:'smooth'}})">Explorar</button></header>
<section class="hero">
  <div class="hero-txt"><h1>{titulo}</h1><p>{fx}</p><a id="cta" class="btn" href="#info">Ver projeto</a></div>
  <img class="hero-img" src="{img_hero}" alt="arte do projeto gerada por IA">
</section>
<section class="info" id="info"><h2>Sobre este projeto</h2><p class="ped">{titulo}</p></section>
<footer>Gerado pelo Jarvis ✦</footer>
</body></html>"""
    css = """*{margin:0;padding:0;box-sizing:border-box}html{scroll-behavior:smooth}
body{font-family:'Outfit',sans-serif;color:#1c2030;background:#f4f6ff;overflow-x:hidden}
.topo{position:fixed;inset:0 0 auto;display:flex;justify-content:space-between;align-items:center;
 padding:14px 28px;background:rgba(255,255,255,.65);backdrop-filter:blur(14px);z-index:9}
.logo{font-weight:800;font-size:1.1rem;letter-spacing:.5px}
.btn-topo{border:0;padding:10px 22px;border-radius:999px;background:linear-gradient(135deg,#6c5cff,#a15cff);
 color:#fff;font-weight:600;cursor:pointer;box-shadow:0 10px 24px rgba(108,92,255,.35)}
.hero{min-height:92vh;display:grid;grid-template-columns:1.1fr .9fr;gap:44px;align-items:center;
 max-width:1120px;margin:0 auto;padding:120px 28px 40px}
.hero-txt h1{font-size:clamp(2.4rem,6vw,4.4rem);font-weight:800;line-height:1.05;
 background:linear-gradient(135deg,#1d1f4e,#6c5cff);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero-txt p{margin:20px 0 26px;color:#4c5375;font-size:1.1rem;line-height:1.7;max-width:46ch}
.btn{display:inline-block;padding:15px 34px;border-radius:999px;background:linear-gradient(135deg,#6c5cff,#a15cff);
 color:#fff;text-decoration:none;font-weight:700;box-shadow:0 14px 34px rgba(108,92,255,.4);transition:.25s}
.btn:hover{transform:translateY(-3px) scale(1.03)}
.hero-img{width:100%;border-radius:26px;box-shadow:0 30px 80px rgba(29,31,78,.25);animation:flut 9s ease-in-out infinite}
@keyframes flut{50%{transform:translateY(-14px)}}
.info{max-width:900px;margin:0 auto;padding:70px 28px 60px;text-align:center}
.info h2{font-size:2rem;margin-bottom:14px}.ped{color:#4c5375;line-height:1.7}
footer{padding:34px;text-align:center;color:#8a90ad}
@media(max-width:860px){.hero{grid-template-columns:1fr;text-align:center}.hero-txt p{margin-inline:auto}}"""
    return {'nome': nome, 'descricao': titulo, 'html': html, 'css': css, 'js': '', 'offline': True}


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
        # --- 1) Conteúdo: em etapas de alta qualidade -> JSON simples -> site único -> emergência ---
        proj = _gerar_projeto_bem(job['prompt'], job.get('lang', 'pt'))
        if not proj:
            proj = _ler_projeto_da_ia(job['prompt'], job.get('lang', 'pt'))
        if not proj:
            html = None
            try:
                html = brain.generate_site(job['prompt'], job.get('lang', 'pt'))
            except Exception:
                html = None
            if html:
                proj = {'nome': 'Projeto Jarvis', 'descricao': job['prompt'][:160],
                        'html': html, 'css': '', 'js': '', 'offline': False}
            else:
                proj = _pagina_emergencia(job['prompt'], job.get('lang', 'pt'))

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
        (pasta / 'css' / 'style.css').write_text(css or '/* estilo padrão: projeto em página única */', encoding='utf-8')
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
