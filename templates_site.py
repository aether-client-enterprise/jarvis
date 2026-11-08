# Templates de sites gerados pelo Jarvis (HTML puro, sem dependências)

_LEGENDA_PADRAO = {
    'romantico': 'Onde cada palavra vira um beijo no coração.',
    'cyberpunk': 'Conecte seus sonhos direto na rede.',
    'natureza': 'Respire fundo. A vida é verde e simples.',
    'espaco': 'Muito além do céu, onde os sonhos orbitam.',
}

_TITULO_PADRAO = {
    'romantico': 'Nosso Cantinho',
    'cyberpunk': 'NEO://City',
    'natureza': 'Trilha Verde',
    'espaco': 'Órbita Infinita',
}

_PARTICULA = {
    'romantico': ['💖', '💗', '🌹', '💞'],
    'cyberpunk': ['⚡', '🔷', '🌐', '✨'],
    'natureza': ['🍃', '🌿', '🍀', '🌸'],
    'espaco': ['⭐', '🌟', '✨', '🪐'],
}


def site_html(tema='romantico', titulo=None, legenda=None):
    import json
    titulo = titulo or _TITULO_PADRAO.get(tema, 'Site Jarvis')
    legenda = legenda or _LEGENDA_PADRAO.get(tema, 'Feito pelo Jarvis.')
    html = _TEMPLATE.replace('__TITULO__', titulo)
    html = html.replace('__LEGENDA__', legenda)
    html = html.replace('__TEMA__', tema)
    html = html.replace('__PARTICULA_JSON__', json.dumps(_PARTICULA.get(tema, _PARTICULA['romantico']), ensure_ascii=False))
    return html


_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITULO__</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { min-height: 100vh; font-family: 'Segoe UI', system-ui, sans-serif;
         display: flex; align-items: center; justify-content: center; overflow: hidden; position: relative; }
  /* ====== TEMAS ====== */
  body.romantico { background: linear-gradient(135deg, #ffd6ea 0%, #ff8fc7 45%, #ff5fa2 100%); color: #5b0f37; }
  body.cyberpunk { background: linear-gradient(160deg, #05070f 0%, #0a0f1e 55%, #131b33 100%); color: #e0f2ff; }
  body.natureza  { background: linear-gradient(135deg, #d9f2e0 0%, #8fd8a8 55%, #4fae74 100%); color: #1d4430; }
  body.espaco    { background: radial-gradient(1200px 700px at 70% 20%, #1b2447 0%, #060a1a 60%, #02040c 100%); color: #dfe9ff; }

  .card { position: relative; z-index: 2; text-align: center; padding: 70px 60px; max-width: 760px; border-radius: 28px;
          backdrop-filter: blur(10px); box-shadow: 0 30px 80px rgba(0,0,0,.30); }
  body.romantico .card { background: rgba(255,255,255,.55); border: 2px solid rgba(255,255,255,.8); }
  body.cyberpunk .card { background: rgba(10,15,30,.72); border: 1px solid #00d9ff88; box-shadow: 0 0 60px #00d9ff33, 0 30px 80px rgba(0,0,0,.6); }
  body.natureza .card  { background: rgba(255,255,255,.62); border: 2px solid rgba(255,255,255,.9); }
  body.espaco .card    { background: rgba(8,12,28,.6); border: 1px solid #7aa2ff55; box-shadow: 0 0 80px #4a6bff2e; }

  h1 { font-size: clamp(2rem, 5vw, 3.4rem); margin-bottom: 18px; line-height: 1.15; }
  body.romantico h1 { font-family: Georgia, 'Times New Roman', serif; text-shadow: 0 2px 18px #ffffffaa; }
  body.cyberpunk h1 { letter-spacing: 3px; text-shadow: 0 0 12px #00d9ff, 0 0 40px #00d9ff66; }
  body.natureza h1  { text-shadow: 0 2px 12px #ffffffaa; }
  body.espaco h1    { text-shadow: 0 0 14px #9db8ff, 0 0 50px #4a6bff55; }

  p.legenda { font-size: clamp(1rem, 2.4vw, 1.35rem); font-style: italic; opacity: .92; margin-bottom: 34px; line-height: 1.6; }

  button { padding: 15px 34px; border: none; border-radius: 999px; font-weight: 800; font-size: 1rem; cursor: pointer;
           transition: transform .15s ease, box-shadow .15s ease; }
  button:hover { transform: translateY(-2px) scale(1.03); }
  body.romantico button { background: linear-gradient(135deg, #ff2f86, #ff7eb0); color: #fff; box-shadow: 0 10px 26px #ff5fa266; }
  body.cyberpunk button { background: transparent; color: #00d9ff; border: 2px solid #00d9ff; box-shadow: 0 0 22px #00d9ff55, inset 0 0 14px #00d9ff22; }
  body.natureza  button { background: #2e8b57; color: #fff; box-shadow: 0 10px 26px #2e8b5744; }
  body.espaco    button { background: linear-gradient(135deg, #4a6bff, #a06bff); color: #fff; box-shadow: 0 10px 26px #4a6bff55; }

  #particles { position: fixed; inset: 0; z-index: 1; pointer-events: none; }
  .part { position: absolute; font-size: 22px; opacity: 0; animation: flutuar linear infinite; }
  @keyframes flutuar {
    0%   { transform: translateY(102vh) rotate(0deg) scale(.8); opacity: 0; }
    12%  { opacity: .95; }
    88%  { opacity: .85; }
    100% { transform: translateY(-8vh) rotate(360deg) scale(1.15); opacity: 0; }
  }
  footer { position: fixed; bottom: 12px; width: 100%; text-align: center; font-size: .78rem; opacity: .6; z-index: 2; }
</style>
</head>
<body class="__TEMA__">
  <div id="particles"></div>
  <div class="card">
    <h1>__TITULO__</h1>
    <p class="legenda">__LEGENDA__</p>
    <button onclick="chuva(18)">✨ Clique para a mágica</button>
  </div>
  <footer>Feito pelo Jarvis — assistente local</footer>
<script>
  const TEMA = '__TEMA__';
  const PARTICULAS = __PARTICULA_JSON__;

  // Chuva de partículas contínua e suave
  function criarPart(umaVez = false) {
    const p = document.createElement('span');
    p.className = 'part';
    p.textContent = PARTICULAS[Math.floor(Math.random() * PARTICULAS.length)];
    p.style.left = Math.random() * 100 + 'vw';
    p.style.fontSize = (14 + Math.random() * 20) + 'px';
    const dur = (6 + Math.random() * 6) + 's';
    p.style.animationDuration = dur;
    if (umaVez) { p.style.top = '-6vh'; }
    document.getElementById('particles').appendChild(p);
    setTimeout(() => p.remove(), 13000);
  }
  setInterval(() => criarPart(false), 700);

  // Explosão ao clicar no botão
  function chuva(qt) {
    for (let i = 0; i < qt; i++) setTimeout(criarPart, i * 90);
  }

  // Tema inicial: fermento de partículas já voando
  for (let i = 0; i < 12; i++) setTimeout(criarPart, i * 250);
</script>
</body>
</html>"""
