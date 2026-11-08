# Template de jogo RPG 2D gerado pelo Jarvis (salvamento em disco ou localStorage)


def jogo_rpg_html(titulo='Aventura Jarvis', save_path=r'C:\Users\joilton\Downloads\Jarvis\criacoes\rpg_save.json'):
    html = _TEMPLATE.replace('__TITULO__', titulo)
    html = html.replace('__SAVE_PATH__', save_path.replace('\\', '\\\\'))
    return html


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>__TITULO__</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0a0b0f; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; display: flex;
         flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; gap: 12px; }
  h1 { color: #00d9ff; letter-spacing: 2px; font-size: 1.6rem; text-shadow: 0 0 14px #00d9ff66; }
  canvas { border: 2px solid #00d9ff; background: #000; box-shadow: 0 0 40px #00d9ff33; image-rendering: pixelated; }
  .barra { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
  button { padding: 9px 16px; border-radius: 8px; border: 1px solid #2a2f3a; background: #141821;
           color: #00d9ff; cursor: pointer; font-weight: bold; }
  button:hover { background: #1e2330; }
  #msg { min-height: 20px; color: #ffd166; font-size: .9rem; }
  #toast { position: fixed; bottom: 14px; background: #141821; border: 1px solid #00d9ff; padding: 8px 14px;
           border-radius: 8px; opacity: 0; transition: opacity .3s; }
  /* ===== BATALHA ===== */
  #battle { position: fixed; inset: 0; display: none; align-items: center; justify-content: center;
            background: rgba(0,0,0,.75); z-index: 5; }
  #battle.on { display: flex; }
  .bcard { width: 460px; background: #10131c; border: 2px solid #ff3b5c; border-radius: 16px; padding: 22px;
           box-shadow: 0 0 60px #ff3b5c33; }
  .bcard h2 { color: #ff3b5c; margin-bottom: 12px; letter-spacing: 2px; }
  .hp { height: 14px; background: #23131a; border: 1px solid #443; border-radius: 8px; overflow: hidden; margin: 6px 0 14px; }
  .hp span { display: block; height: 100%; background: linear-gradient(90deg,#ff3b5c,#ff8fa3); }
  .bcard .acts { display: flex; gap: 10px; }
  .bcard button { border-color: #ff3b5c; color: #ff8fa3; }
  .bcard button:disabled { opacity: .4; cursor: wait; }
  .log { margin-top: 12px; font-size: .85rem; color: #cfd6e4; min-height: 48px; white-space: pre-line; }
</style>
</head>
<body>
  <h1>__TITULO__</h1>
  <div class="barra">
    <span>🛡️ Nv <b id="lvl">1</b></span><span>❤️ <b id="hpT">20/20</b></span><span>⭐ XP <b id="xp">0</b></span>
    <span>🧪 Poções <b id="pot">3</b></span><span>🗺️ Andar <b id="fl">1</b></span>
    <button onclick="salvar()">💾 Salvar</button><button onclick="carregar()">📂 Carregar</button><button onclick="zero()">🔄 Recomeçar</button>
  </div>
  <canvas id="cv" width="720" height="450"></canvas>
  <div id="msg">Setas/WASD para andar • Encoste no inimigo para batalhar • Chegue na escada 🟨 para descer o andar</div>
  <div id="toast"></div>
  <div id="battle"><div class="bcard">
    <h2>⚔️ Batalha!</h2>
    <div id="eNome">Goblin</div>
    <div class="hp"><span id="eHpBar" style="width:100%"></span></div>
    <div class="acts">
      <button id="bAtk" onclick="jog('atk')">🗡️ Atacar</button>
      <button id="bCur" onclick="jog('cur')">🧪 Curar</button>
      <button id="bRun" onclick="jog('run')">💨 Fugir</button>
    </div>
    <div class="log" id="blog"></div>
  </div></div>
<script>
const SAVE_PATH = "__SAVE_PATH__";
const TS = 30, COLS = 24, ROWS = 15;
const cv = document.getElementById('cv'), cx = cv.getContext('2d');
let mapa, herói, inimigos, escada, andar = 1, travado = false;

function novoAndar(f) {
  mapa = Array.from({length: ROWS}, (_y, y) => Array.from({length: COLS}, (_x, x) =>
    (y === 0 || y === ROWS-1 || x === 0 || x === COLS-1) ? '#' : (Math.random() < 0.12 ? '#' : '.')));
  herói = (herói && f > 0) ? { x: herói.x, y: herói.y } : { x: 3, y: 3 };
  if (!heroOk()) { herói = { x: 3, y: 3 }; limpar(3, 3); }
  do { escada = { x: COLS-3, y: ROWS-4 }; limpar(COLS-3, ROWS-4); limpar(COLS-3, ROWS-5); } while (false);
  inimigos = [];
  const n = 3 + Math.min(6, f);
  for (let i = 0; i < n; i++) {
    let p; let tent = 0;
    do { p = { x: 2 + Math.floor(Math.random()*(COLS-4)), y: 2 + Math.floor(Math.random()*(ROWS-4)) }; tent++; }
    while ((!pode(p.x, p.y) || muitoPerto(p)) && tent < 200);
    inimigos.push({ x: p.x, y: p.y,
      nome: ['Goblin', 'Orc', 'Esqueleto', 'Slime', 'Lorde Sombrio'][Math.floor(Math.random()*5)],
      hp: 6 + f*3, hpMax: 6 + f*3, atk: 2 + f });
  }
  andar = f;
}

function limpar(x, y) { if (mapa[y] && mapa[y][x]) mapa[y][x] = '.'; }
function pode(x, y) { return mapa[y] && mapa[y][x] === '.'; }
function heroOk() { return pode(herói.x, herói.y); }
function muitoPerto(p) { return Math.abs(p.x - herói.x) + Math.abs(p.y - herói.y) < 4; }

let st = { lvl: 1, hp: 20, hpMax: 20, atk: 3, xp: 0, pot: 3 };
novoAndar(1);

function hud() {
  lvl.textContent = st.lvl; hpT.textContent = st.hp + '/' + st.hpMax;
  xp.textContent = st.xp; pot.textContent = st.pot; fl.textContent = andar;
}

function desenhar() {
  cx.fillStyle = '#0a0b0f'; cx.fillRect(0, 0, cv.width, cv.height);
  for (let y = 0; y < ROWS; y++) for (let x = 0; x < COLS; x++) {
    cx.fillStyle = mapa[y][x] === '#' ? '#2b3242' : ((x + y) % 2 ? '#12333f' : '#0f2c37');
    cx.fillRect(x*TS, y*TS, TS, TS);
  }
  cx.fillStyle = '#ffd166'; cx.font = '18px sans-serif'; cx.fillText('🟨', escada.x*TS+3, escada.y*TS+22);
  cx.font = '20px sans-serif';
  inimigos.forEach(e => { cx.fillText('👾', e.x*TS+4, e.y*TS+23);
    cx.fillStyle = '#ff3b5c'; var w = Math.max(0, 26 * e.hp / e.hpMax); cx.fillRect(e.x*TS+2, e.y*TS-4, w, 3); });
  cx.fillText('🦸', herói.x*TS+4, herói.y*TS+23);
  hud();
}

function andarHeroi(dx, dy) {
  if (travado) return;
  const nx = herói.x + dx, ny = herói.y + dy;
  if (!pode(nx, ny)) return;
  herói.x = nx; herói.y = ny;
  const e = inimigos.find(i => i.x === nx && i.y === ny);
  if (e) return batalha(e);
  if (nx === escada.x && ny === escada.y) { novoAndar(andar + 1); msg('⬇️ Andar ' + andar + ' — mais difícil!'); }
  moverInimigos();
  desenhar();
}

function moverInimigos() {
  inimigos.forEach(e => {
    if (Math.random() < 0.6) {
      const d = [[1,0],[-1,0],[0,1],[0,-1]][Math.floor(Math.random()*4)];
      const nx = e.x + d[0], ny = e.y + d[1];
      if (pode(nx, ny) && !(nx === herói.x && ny === herói.y)) { e.x = nx; e.y = ny; }
    }
  });
}

// ================= BATALHA =================
let alvo = null, vezHeroi = true;
function batalha(e) {
  alvo = e; vezHeroi = true; blog.textContent = ''
  ; eNome.textContent = '⚔️ ' + e.nome + ' (atk ' + e.atk + ')';
  barra(); battle.classList.add('on'); travado = true; log('🦸 Você encontrou um ' + e.nome + '!');
}
function barra() { eHpBar.style.width = Math.max(0, 100 * alvo.hp / alvo.hpMax) + '%'; }
function log(t) { blog.textContent += t + '\n'; }
function jog(a) {
  if (!vezHeroi || !travado) return;
  if (a === 'atk') {
    const d = st.atk + Math.floor(Math.random()*4);
    alvo.hp -= d; log('🗡️ Você causou ' + d + ' de dano!');
    if (alvo.hp <= 0) return vitoria();
    vezHeroi = false; trava(true); barra(); desenhar();
    setTimeout(vezInimigo, 750);
  } else if (a === 'cur') {
    if (st.pot <= 0) { log('❌ Sem poções!'); return; }
    st.pot--; st.hp = Math.min(st.hpMax, st.hp + 12); hud(); log('🧪 Você se curou!'); vezHeroi = false; trava(true);
    setTimeout(vezInimigo, 750);
  } else {
    if (Math.random() < 0.6) { log('💨 Fugiu!'); setTimeout(fim, 600); }
    else { log('❌ Falhou a fuga!'); vezHeroi = false; trava(true); setTimeout(vezInimigo, 750); }
  }
}
function vezInimigo() {
  const d = alvo.atk + Math.floor(Math.random()*3);
  st.hp -= d; hud(); log('👾 ' + alvo.nome + ' atacou: -' + d + '!');
  if (st.hp <= 0) { st.hp = Math.floor(st.hpMax/2); herói = { x: 3, y: 3 }; limpar(3,3); log('💀 Você caiu... mas acordou no início'); fim(); return; }
  vezHeroi = true; trava(false); barra();
}
function vitoria() {
  log('🏆 Vitória! +' + (4 + andar*2) + ' XP');
  st.xp += 4 + andar*2;
  inimigos = inimigos.filter(i => i !== alvo);
  if (st.xp >= st.lvl * 20) { st.lvl++; st.hpMax += 4; st.hp = st.hpMax; st.atk++; log('🌟 Subiu para o Nv ' + st.lvl + '!'); }
  if (Math.random() < 0.4) { st.pot++; log('🧪 Dropou uma poção!'); }
  setTimeout(fim, 900);
}
function fim() { battle.classList.remove('on'); trava(false); alvo = null; hud(); desenhar(); }
function trava(b) { bAtk.disabled = bCur.disabled = bRun.disabled = b; }

// ================= SALVAR / CARREGAR =================
function salvar() {
  const dados = JSON.stringify({ st, andar, x: herói.x, y: herói.y });
  try { localStorage.setItem('rpg_jarvis', dados); } catch (e) {}
  fetch('http://127.0.0.1:8765/files/write', { method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ path: SAVE_PATH, content: dados }) })
    .then(r => r.json()).then(d => {
      toast(d.error ? '💾 Salvo localmente (disco falhou: ' + d.error + ')' : '💾 Salvo no disco: ' + (d.path || SAVE_PATH));
    }).catch(() => toast('💾 Salvo localmente (Jarvis offline)'));
}
function carregar() {
  fetch('http://127.0.0.1:8765/files/read', { method: 'POST',
    headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ path: SAVE_PATH }) })
    .then(r => r.json()).then(d => {
      if (d.content) { aplicar(d.content); toast('📂 Carregado do disco!'); }
      else throw 0;
    }).catch(() => {
      const l = localStorage.getItem('rpg_jarvis');
      if (l) { aplicar(l); toast('📂 Carregado do navegador'); }
      else toast('❌ Nenhum save encontrado');
    });
}
function aplicar(txt) {
  try { const d = JSON.parse(txt); st = d.st; andar = d.andar; herói = { x: d.x, y: d.y };
    novoAndar(andar); desenhar(); } catch (e) { toast('Save corrompido'); }
}
function zero() { st = { lvl: 1, hp: 20, hpMax: 20, atk: 3, xp: 0, pot: 3 }; novoAndar(1); desenhar(); toast('🔄 Novo jogo'); }

function toast(t) { const el = document.getElementById('toast'); el.textContent = t; el.style.opacity = 1;
  setTimeout(() => el.style.opacity = 0, 2600); }
function msg(t) { document.getElementById('msg').textContent = t; }

// ================= TECLADO + LOOP =================
const keys = {};
window.addEventListener('keydown', e => { keys[e.key] = true; if (e.key.startsWith('Arrow')) e.preventDefault(); });
window.addEventListener('keyup', e => keys[e.key] = false);
let cd = 0;
function loop(ts) {
  if (!travado && ts - cd > 140) {
    if (keys.ArrowUp || keys.w || keys.W) { andarHeroi(0, -1); cd = ts; }
    else if (keys.ArrowDown || keys.s || keys.S) { andarHeroi(0, 1); cd = ts; }
    else if (keys.ArrowLeft || keys.a || keys.A) { andarHeroi(-1, 0); cd = ts; }
    else if (keys.ArrowRight || keys.d || keys.D) { andarHeroi(1, 0); cd = ts; }
  }
  requestAnimationFrame(loop);
}
desenhar(); requestAnimationFrame(loop);
</script>
</body>
</html>"""
