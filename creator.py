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


def _sel_do_html(html):
    """Extrai classes/ids REAIS do html: CSS e JS acertam os alvos de verdade."""
    cls, ids = [], []
    for c in re.findall(r'class="([^"]+)"', html or ''):
        for p in c.split():
            if p and p not in cls and len(p) < 30:
                cls.append(p)
    for i in re.findall(r'id="([^"]+)"', html or ''):
        if i and i not in ids:
            ids.append(i)
    return (' '.join('.' + c for c in cls[:40]), ' '.join('#' + i for i in ids[:14]))


_STOP = {'de', 'da', 'do', 'para', 'com', 'uma', 'um', 'que', 'voce', 'você', 'site',
         'quero', 'crie', 'criar', 'faca', 'faça', 'sobre', 'meu', 'minha', 'mim',
         'como', 'fosse', 'real', 'onde', 'pelo', 'ela', 'ele', 'nos', 'nas', 'dos',
         'das', 'aos', 'ate', 'até', 'e', 'ou', 'the', 'with', 'and', 'for', 'make'}


def _conteudo(prompt, meta, idioma):
    """Textos REAIS do tema em JSON pequeno — estágio pequeno funciona até no modelo público."""
    plano = json.dumps(meta, ensure_ascii=False)[:700] if isinstance(meta, dict) else ''
    out = brain.gerar_parte(
        "Você é REDATOR de conteúdo de sites premiados. Responda APENAS um JSON válido com as "
        "chaves: hero (objeto: titulo, texto, cta), destaques (lista de 8 objetos: titulo, "
        "texto com 1-2 frases, preco ('R$ 249,90' se fizer sentido, senão string vazia), "
        "img_desc_en (descrição CURTA em inglês da foto que ilustra o item)), sobre (objeto: "
        "titulo, texto, lista com 3 frases), depoimentos (lista de 3 objetos: nome, texto), "
        "final (objeto: titulo, texto). Textos REALISTAS e específicos do tema, no idioma do "
        "usuário, sem Lorem ipsum e sem frases genéricas de preencher.\nIdioma: " + idioma + ".",
        "PLANO: " + plano + "\nPROMPT ORIGINAL: " + prompt, 130, 3000)
    d = _parse_json(out)
    return d if isinstance(d, dict) else None


def _montar_html(nome, descricao, meta, conteudo, imagens, lang, prompt=''):
    """HTML mestre montado LOCALMENTE: nunca raso, nunca sem imagens, seções completas."""
    en = (lang or 'pt') == 'en'
    L = ({'ini': 'Início', 'dest': 'Destaques', 'sob': 'Sobre',
          'busca': 'Busque por nome ou tema…', 'add': 'Adicionar', 'fin': 'Finalizar',
          'car': 'Carrinho', 'tot': 'Total', 'dep': 'O que dizem sobre',
          'topo': '↑ Voltar ao topo', 'cta': 'Explorar agora'}
         if not en else
         {'ini': 'Home', 'dest': 'Highlights', 'sob': 'About',
          'busca': 'Search by name or theme…', 'add': 'Add to cart', 'fin': 'Checkout',
          'car': 'Cart', 'tot': 'Total', 'dep': 'What they say',
          'topo': '↑ Back to top', 'cta': 'Explore now'})
    base = [b for b in imagens if isinstance(b, str) and b.strip()] or \
        ['premium minimalist product photography, high detail']
    c = conteudo if isinstance(conteudo, dict) else {}

    hero = c.get('hero') if isinstance(c.get('hero'), dict) else {}
    h_tit, h_txt = hero.get('titulo') or nome, hero.get('texto') or descricao
    h_cta = hero.get('cta') or L['cta']

    dst = [d for d in (c.get('destaques') or []) if isinstance(d, dict)][:8]
    if len(dst) < 6:
        paux = [w.capitalize() for w
                in re.findall(r'[a-zà-ú]{4,}', (prompt or '').lower()) if w not in _STOP]
        for i in range(8 - len(dst)):
            desc = base[(len(dst) + i) % len(base)]
            tit = (paux[(len(dst) + i) % len(paux)] if paux
                   else desc.split(',')[0].split(' on ')[0].strip().capitalize())
            if any(x.get('titulo') == tit for x in dst):
                tit += ' ' + str(i + 1)
            dst.append({'titulo': tit, 'texto': descricao, 'preco': '',
                        'img_desc_en': desc})

    sob = c.get('sobre') if isinstance(c.get('sobre'), dict) else {}
    sob_tit = sob.get('titulo') or L['sob']
    sob_txt = sob.get('texto') or descricao
    sob_lst = [x for x in (sob.get('lista') or []) if isinstance(x, str)][:4]
    dep = [d for d in (c.get('depoimentos') or []) if isinstance(d, dict)][:3]
    fin = c.get('final') if isinstance(c.get('final'), dict) else {}
    fin_tit, fin_txt = fin.get('titulo') or nome, fin.get('texto') or descricao

    img_hero = _img(base[0], 1100, 760, seed=3)
    img_sobre = _img(base[1 % len(base)], 800, 640, seed=5)
    img_cta = _img(base[2 % len(base)], 1000, 520, seed=9)

    cards = []
    for i, d in enumerate(dst[:8]):
        tit = str(d.get('titulo') or f'{L["dest"]} {i + 1}')
        txt = str(d.get('texto') or descricao)
        pre = str(d.get('preco') or '').strip()
        imgd = d.get('img_desc_en') or base[i % len(base)]
        img = _img(imgd, 600, 450, seed=11 + i)
        preco = f'<span class="preco">{pre}</span>' if pre else ''
        cards.append(
            f'<article class="card revela" data-nome="{tit.lower()}">\n'
            f'  <div class="card-img"><img src="{img}" alt="{tit}" loading="lazy"></div>\n'
            f'  <div class="card-corpo"><h3>{tit}</h3><p>{txt}</p>'
            f'<div class="card-pe{"" if pre else " sem-preco"}">{pre}'
            f'<button class="btn-comprar" data-item="{tit}">{L["add"]}</button></div>'
            f'</div>\n</article>')

    depo = []
    for i, d in enumerate(dep):
        depo.append(
            f'<figure class="depoimento revela">\n'
            f'  <img src="{_img("portrait of happy person, natural light", 120, 120, seed=21 + i)}" alt="cliente">\n'
            f'  <blockquote>“{d.get("texto") or descricao[:120]}”</blockquote>\n'
            f'  <figcaption>{d.get("nome") or "Cliente"}</figcaption>\n</figure>')

    sobre_li = '\n'.join(f'<li class="revela">{x}</li>' for x in sob_lst)

    # fmt:off
    html = (
        '<!DOCTYPE html>\n'
        f'<html lang="{"en" if en else "pt-BR"}" data-padrao="1">\n<head>\n'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{nome}</title><meta name="description" content="{descricao[:150]}">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">\n'
        '<link rel="stylesheet" href="css/style.css">\n'
        '<script src="js/script.js" defer></script>\n</head>\n<body>\n'
        f'<header class="topo"><a class="logo" href="#inicio">✦ {nome}</a>\n'
        f'<nav><a href="#destaques">{L["dest"]}</a><a href="#sobre">{L["sob"]}</a></nav>\n'
        f'<button id="btn-carrinho" class="btn-carrinho">🛒 {L["car"]} <span id="conta-itens">0</span></button></header>\n'
        f'<section class="hero" id="inicio">\n  <div class="hero-txt">\n'
        f'    <span class="badge">{descricao[:80]}</span>\n'
        f'    <h1>{h_tit}</h1><p>{h_txt}</p>\n'
        f'    <div class="hero-cta"><a class="btn" href="#destaques">{h_cta}</a>'
        f'<a class="btn-fantasma" href="#sobre">{L["sob"]}</a></div>\n</div>\n'
        f'  <img class="hero-img" src="{img_hero}" alt="{nome}">\n</section>\n'
        f'<section class="busca-barra"><input id="busca" type="search" placeholder="{L["busca"]}" aria-label="busca"></section>\n'
        f'<section class="grade-secao" id="destaques"><h2>{L["dest"]}</h2>\n'
        f'  <div id="grade" class="grade">\n{chr(10).join(cards)}\n</div></section>\n'
        f'<section class="sobre" id="sobre">\n  <img class="sobre-img" src="{img_sobre}" alt="{sob_tit}">\n'
        f'  <div class="sobre-txt"><h2>{sob_tit}</h2><p>{sob_txt}</p><ul>{sobre_li}</ul></div>\n</section>\n'
        + (f'<section class="depoimentos" id="depoimentos"><h2>{L["dep"]}</h2>{chr(10).join(depo)}</section>\n'
           if depo else '') +
        f'<section class="cta-final"><div class="cta-card revela">\n'
        f'  <img src="{img_cta}" alt="{fin_tit}">\n'
        f'  <div><h2>{fin_tit}</h2><p>{fin_txt}</p><a class="btn" href="#destaques">{L["cta"]}</a></div>\n'
        f'</div></section>\n'
        f'<footer class="rodape"><strong>{nome}</strong><span>{nome} · feito no seu PC pelo Jarvis ✦</span></footer>\n'
        f'<aside id="carrinho" class="carrinho"><div class="carrinho-topo">\n'
        f'  <strong>{L["car"]}</strong><button id="fechar-carrinho" class="fechar">✕</button></div>\n'
        f'  <ul id="itens-carrinho"></ul>\n'
        f'  <div class="carrinho-pe"><span>{L["tot"]}: <strong id="total-carrinho">0</strong></span>'
        f'<button id="finalizar" class="btn">{L["fin"]}</button></div>\n</aside>\n'
        f'<button id="topo-btn" class="topo-btn" title="{L["topo"]}">↑</button>\n'
        '</body></html>')
    # fmt:on
    return html


_CSS_PADRAO = """/* Estilo padrão Jarvis — elegante mesmo sem IA de CSS */
:root{--bg:#0b0f1a;--fg:#eef2ff;--su:#6c5cff;--su2:#a15cff;--card:#121931;--tx2:#9fb0d0}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:'Outfit',system-ui,sans-serif;background:var(--bg);color:var(--fg);line-height:1.65}
.topo{position:fixed;inset:0 0 auto;z-index:20;display:flex;gap:22px;align-items:center;justify-content:space-between;padding:14px 28px;background:rgba(11,15,26,.72);backdrop-filter:blur(14px)}
.topo nav{display:flex;gap:20px}.topo nav a{color:var(--fg);text-decoration:none;font-weight:600;opacity:.85}
.topo nav a:hover{opacity:1;transform:translateY(-2px)}
.logo{font-weight:800;font-size:1.15rem;text-decoration:none;color:var(--fg);background:linear-gradient(135deg,var(--su),var(--su2));-webkit-background-clip:text;background-clip:text;color:transparent}
.btn-carrinho{border:0;cursor:pointer;padding:10px 18px;border-radius:999px;font-weight:700;background:linear-gradient(135deg,var(--su),var(--su2));color:#fff;box-shadow:0 10px 26px rgba(108,92,255,.4)}
.hero{max-width:1120px;margin:0 auto;padding:150px 28px 60px;display:grid;grid-template-columns:1.05fr .95fr;gap:44px;align-items:center}
.badge{display:inline-block;padding:6px 14px;border-radius:999px;border:1px solid rgba(255,255,255,.2);font-size:.75rem;color:var(--tx2);margin-bottom:14px}
.hero h1{font-size:clamp(2.6rem,6vw,4.3rem);line-height:1.04;background:linear-gradient(135deg,#fff,#b3bcff);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{color:var(--tx2);margin:18px 0 26px;max-width:46ch}
.hero-cta{display:flex;gap:14px}
.btn{display:inline-block;padding:14px 30px;border-radius:999px;background:linear-gradient(135deg,var(--su),var(--su2));color:#fff;font-weight:700;text-decoration:none;box-shadow:0 14px 34px rgba(108,92,255,.42)}
.btn:hover{transform:translateY(-3px) scale(1.02)}
.btn-fantasma{padding:14px 24px;border-radius:999px;border:1px solid rgba(255,255,255,.25);color:var(--fg);text-decoration:none}
.hero-img,.sobre-img,.cta-card img{width:100%;border-radius:24px;box-shadow:0 30px 80px rgba(0,0,0,.45)}
.busca-barra{max-width:640px;margin:10px auto;padding:10px 28px}
#busca{width:100%;padding:14px 22px;border-radius:999px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.06);color:var(--fg);outline:none}
.grade-secao{max-width:1120px;margin:40px auto;padding:20px 28px}
.grade-secao h2,.sobre h2{font-size:clamp(1.7rem,3.4vw,2.4rem);margin-bottom:22px}
.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:26px}
.card{background:var(--card);border-radius:22px;overflow:hidden;box-shadow:0 14px 40px rgba(0,0,0,.35);transition:.35s cubic-bezier(.2,.7,.2,1)}
.card:hover{transform:translateY(-8px) scale(1.015);box-shadow:0 26px 60px rgba(108,92,255,.25)}
.card img{width:100%;height:210px;object-fit:cover}
.card-corpo{padding:18px}
.card-corpo p{color:var(--tx2);font-size:.92rem;margin:8px 0 14px}
.card-pe{display:flex;justify-content:space-between;align-items:center;gap:10px}
.preco{font-weight:800;font-size:1.05rem}
.btn-comprar{border:0;cursor:pointer;padding:10px 18px;border-radius:999px;font-weight:700;background:linear-gradient(135deg,var(--su),var(--su2));color:#fff}
.sobre{max-width:1020px;margin:60px auto;display:grid;grid-template-columns:.9fr 1.1fr;gap:40px;padding:30px 28px;align-items:center}
.sobre ul{margin:16px 0 0 18px;color:var(--tx2)}
.depoimentos{max-width:1020px;margin:50px auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;padding:20px 28px}
.depoimento{background:var(--card);border-radius:22px;padding:24px;text-align:center;box-shadow:0 14px 40px rgba(0,0,0,.35)}
.depoimento img{width:64px;height:64px;border-radius:50%;object-fit:cover;margin-bottom:12px}
.cta-final{max-width:1120px;margin:60px auto;padding:20px 28px}
.cta-card{display:grid;grid-template-columns:1fr 1fr;gap:30px;align-items:center;background:var(--card);border-radius:26px;padding:26px;box-shadow:0 24px 60px rgba(0,0,0,.4)}
.rodape{padding:40px;text-align:center;color:var(--tx2);display:grid;gap:6px}
.carrinho{position:fixed;top:0;right:-420px;width:min(380px,92vw);height:100dvh;background:var(--card);z-index:30;transition:right .4s cubic-bezier(.2,.7,.2,1);display:flex;flex-direction:column;padding:20px;box-shadow:-20px 0 60px rgba(0,0,0,.5)}
.carrinho.aberto{right:0}
.carrinho-topo{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.fechar{background:none;border:0;color:var(--fg);font-size:1.3rem;cursor:pointer}
#itens-carrinho{list-style:none;overflow:auto;flex:1;display:grid;gap:10px;align-content:start}
#itens-carrinho li{background:rgba(255,255,255,.05);border-radius:14px;padding:12px 14px;display:flex;justify-content:space-between}
.carrinho-pe{display:flex;justify-content:space-between;align-items:center;margin-top:14px}
.topo-btn{position:fixed;right:22px;bottom:22px;border:0;width:48px;height:48px;border-radius:50%;cursor:pointer;font-size:1.2rem;background:linear-gradient(135deg,var(--su),var(--su2));color:#fff;box-shadow:0 12px 30px rgba(108,92,255,.45)}
.revela{opacity:0;transform:translateY(26px);transition:all .7s cubic-bezier(.2,.7,.2,1)}
.revela.on{opacity:1;transform:none}
@media(max-width:900px){.hero,.sobre,.cta-card{grid-template-columns:1fr}.topo nav{display:none}}
"""

_CSS_REFORCO = """/* Reforço Jarvis: grade, responsividade, revelação */
.grade,.depoimentos{display:grid;gap:24px}
.grade{grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
.depoimentos{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.hero,.sobre{display:grid;align-items:center;gap:40px}
.hero{grid-template-columns:1.05fr .95fr}
.sobre{grid-template-columns:.9fr 1.1fr}
.revela{opacity:0;transform:translateY(26px);transition:all .7s cubic-bezier(.2,.7,.2,1)}
.revela.on{opacity:1;transform:none}
button,.btn,.btn-comprar{cursor:pointer;font-weight:700}
:root{--su:#6c5cff;--su2:#a15cff}
@media(max-width:900px){.hero,.sobre{grid-template-columns:1fr}.topo div,nav{display:none}}
@media(max-width:480px){.grade{grid-template-columns:1fr;padding:0 12px}}
"""

_JS_PADRAO = """/* Lógica padrão Jarvis — carrinho, busca, revelação e topo */
(function () {
  'use strict';
  var $ = function (s) { return document.querySelector(s); };
  var $$ = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };

  // busca filtra cards
  var busca = $('#busca'), cards = $$('.card');
  if (busca && cards.length) {
    busca.addEventListener('input', function () {
      var q = busca.value.toLowerCase();
      cards.forEach(function (c) {
        var alvo = (c.getAttribute('data-nome') || c.textContent || '').toLowerCase();
        c.style.display = alvo.indexOf(q) > -1 ? '' : 'none';
      });
    });
  }

  // carrinho
  var itens = [];
  var cart = $('#carrinho'), lista = $('#itens-carrinho'),
      tot = $('#total-carrinho'), cnt = $('#conta-itens'),
      abre = $('#btn-carrinho'), fecha = $('#fechar-carrinho'), fin = $('#finalizar');
  function render() {
    if (!lista) return;
    lista.innerHTML = itens.length
      ? itens.map(function (i) {
          return '<li><span>' + i + '</span><button class="tirar" data-tirar="' + i + '">✕</button></li>';
        }).join('')
      : '<li>Nenhum item ainda.</li>';
    if (cnt) cnt.textContent = String(itens.length);
    if (tot) tot.textContent = String(itens.length) + ' item(s)';
    var foca = achados();
  }
  function achados() { return null; }
  document.addEventListener('click', function (e) {
    var add = e.target.closest('[data-item]');
    if (add) { itens.push(add.getAttribute('data-item')); render(); if (cart) cart.classList.add('aberto'); }
    var tir = e.target.closest('[data-tirar]');
    if (tir) {
      var v = tir.getAttribute('data-tirar'), ix = itens.indexOf(v);
      if (ix > -1) { itens.splice(ix, 1); render(); }
    }
  });
  if (abre) abre.addEventListener('click', function () { if (cart) cart.classList.add('aberto'); });
  if (fecha) fecha.addEventListener('click', function () { if (cart) cart.classList.remove('aberto'); });
  if (fin) fin.addEventListener('click', function () {
    if (!itens.length) return;
    itens = []; render(); if (cart) cart.classList.remove('aberto');
  });

  // revelação ao rolar
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (x) {
        if (x.isIntersecting) { x.target.classList.add('on'); io.unobserve(x.target); }
      });
    }, { threshold: .12 });
    $$('.revela').forEach(function (el) { io.observe(el); });
  } else {
    $$('.revela').forEach(function (el) { el.classList.add('on'); });
  }

  // voltar ao topo
  var topo = $('#topo-btn');
  if (topo) topo.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
})();
"""


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
    conteudo = _conteudo(prompt, meta, idioma) or {}
    html = brain.gerar_parte(sys_html, pedido_html, 170, 8000) or ''

    def _passa(h):
        return (len(h) >= 2500 and 'pollinations' in h and h.lower().count('<img') >= 6
                and 'html' in h.lower()[:400])

    if not _passa(html):
        urls = '\n'.join(f'<img src="{f["url"]}" alt="{d[:80]}">'
                         for d, f in zip(imagens, fundos) if isinstance(f, dict))
        html2 = brain.gerar_parte(
            sys_html + " SUA ANTERIOR RESPOSTA FOI CURTA E SEM IMAGENS. Refaça COMPLETO: no mínimo "
            "200 linhas, todas as seções DENSAS e estas URLs de imagem obrigatórias (copie-as nas <img>):\n"
            + urls + "\n" + pedido_html, 170, 8000) or ''
        if _passa(html2):
            html = html2
    if not _passa(html):
        # contrato de qualidade: template mestre LOCAL — nunca raso, nunca sem imagens
        html = _montar_html(nome, descricao, meta, conteudo, imagens, lang, prompt)

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
    cls_txt, ids_txt = _sel_do_html(html)
    pedido_css = (f"PALETA/VIBE: {css_resumo}\nPEDIDO: {prompt}\n"
                  f"CLASSES/IDS que o HTML usa (estile TUDO): {cls_txt} {ids_txt}")
    css = brain.gerar_parte(sys_css, pedido_css, 170, 8000) or ''
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
    if len(css) < 900 or '{' not in css:
        css = _CSS_PADRAO
    elif 'data-padrao="1"' in html and not all(s in css for s in ('@media', 'grid', 'revela')):
        css += '\n' + _CSS_REFORCO

    # ---------- JS ----------
    sys_js = (
        "Você é um ENGINHEIRO JS sênior. Escreva o js/script.js COMPLETO e FUNCIONAL do projeto. "
        "Requisitos: vanilla JS moderno, organizado em seções comentadas, sem dependências; "
        "tudo que a página promete tem que FUNCIONAR (carrinho, filtros, busca, formulário com "
        "validação, jogo com teclado/toque, salvar em localStorage, render de listas a partir de "
        "arrays de dados dinâmicos, contadores, modal, toast). Inclua sempre: revela-on-scroll "
        "(IntersectionObserver), botão 'voltar ao topo' e estados decarregamento suaves. "
        "Devolva APENAS o JavaScript.")
    funcs = json.dumps((meta.get('secoes') if isinstance(meta, dict) else [])
                       + (meta.get('funcional') if isinstance(meta, dict) else []),
                       ensure_ascii=False)
    pedido_js = (f"SECOES/FUNCIONALIDADES: {funcs}\nPEDIDO: {prompt}\n"
                 f"IDs/CLASSES do HTML: {ids_txt} {cls_txt}")
    if 'data-padrao="1"' in html:
        pedido_js += (
            "\nLIGAÇÕES OBRIGATÓRIAS: busca #busca filtra .card filtrando por data-nome; "
            "adicionar ao carrinho = botões [data-item] (texto do item); aside#carrinho recebe "
            "classe .aberto p/ abrir; lista #itens-carrinho, remover [data-tirar], total "
            "#total-carrinho, contador #conta-itens, abrir #btn-carrinho, fechar "
            "#fechar-carrinho, finalizar #finalizar; .revela ganha .on no IntersectionObserver; "
            "#topo-btn rola ao topo.")
    js = brain.gerar_parte(sys_js + " No mínimo 150 linhas reais, com dados de exemplo coerentes.",
                           pedido_js, 150, 6000) or ''
    if len(js) < 1500:
        js2 = brain.gerar_parte(sys_js + " SUA ANTERIOR FOI CURTA. Entrega completa: mínimo 180 "
                                "linhas, todas as funções do pedido implementadas de verdade.",
                                pedido_js, 150, 6000) or ''
        if len(js2) > len(js):
            js = js2
    if len(js) < 900 or ('function' not in js and '=>' not in js
                         and 'addEventListener' not in js):
        js = _JS_PADRAO

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
