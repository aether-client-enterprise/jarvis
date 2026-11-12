/* =====================================================
   Twich Fake — motor da treta (chat vivo, raids, viewers)
   Teclas do mestre: P = painel · B = revelar treta
   ===================================================== */
'use strict';

/* ---------- banco de personagens ---------- */
var USERS = ['XandaoGamer', 'peladinho47', 'JujuGamer', 'Marotinho', 'TiaKeke', 'oFabinho', 'ZeDoPao', 'RataBokeh88',
  'loiroo_do_hype', 'SharkBR', 'buegirl', 'Doodlez', 'xXx_mitinho', 'VenceRasoVovo', 'AutoGrossa', 'PixelPete',
  'BossDoLoot', 'OzMario', 'kkiara', 'grounded_Goat', 'nayaraGG', 'FioraMain', 'BatataDoceGames', 'ZeSuperTrunfo',
  'Sketchword', 'NardoShipp', 'seuReginaldo', 'Malucao', 'TurboFernandinho', 'JAPONESDoPoe', 'Agnesaurio', 'chroma99',
  'luanaSportt', 'OnlycaPee', 'GabrielZEDUC', 'kpop_q_YT', 'EscolhidoDoMeta', 'RavenGG', 'BugAddict', 'Miniclash'];
var CORES = ['#ff6b6b', '#ffb31a', '#00e57d', '#4fc1ff', '#c79bff', '#ff7bd5', '#7dff6a', '#ffc0a3', '#9ff3ff'];
var FRASES = ['LEMURA GAAA \ud83d\udd25', 'kkkkkkkk perdeu play', 'A MACE NAO PEER', 'chat passa mal hoje viu',
  'primeiro comentario marcar presenca \u2728', 'gogogo go metas', '??', 'huehuehue \ud83d\ude02', 'classico tia Keke',
  'quase morre ali right', 'DANTIEE', 'OMG fato isso', '!! META FOI BATIDA?? \ud83c\udfaf', 'moderacao clean hoje',
  'nao acredito', 'GG EZ', '15k olha pessoal', 'bit bits bits \ud83d\udc99', 'KKKK pacotao', '\ud83d\ude02\ud83d\ude02\ud83d\ude02',
  'sem fan fake aqui', 'CHChat BOM BOM', 'vai dar errado \ud83d\ude2d', 'Eu que chamo', 'twitch nao aguenta',
  'mais um mais um', 'pai dos memes', 'cuidado mijo', 'RTX LIGADO??', 'melhor do server', 'o maluco e commit',
  'alguem joga valorant', 'SUBZINHO saindo \u2b50', 'sextou hoje \ud83e\udd2a', 'kkkk im dying', 'trola detectada',
  'fala meu nome no chat por favora', 'vivo vivo \ud83c\udfae', 'que ritual e esse', 'olha o wifi dele', 'noclip on',
  'freeze total travou', 'toma sub meu rei', 'coloca musica', 'apareceu o boss', 'ele n ve o chat \ud83d\ude05',
  'wake word rencontas?', 'uau que movimenta', 'mi primo viu isso \ud83c\udfa5', 'server down \ud83e\udd26'];
var DONATES = ['enviou 50 bits! \ud83d\udc99 POGGERS', 'presenteou 1 Sub Tier 1 \u2b50', 'doou 300 bits! FORCA AMIGO'];
var MOD_ACOES = ['cof solicit aang', 'Timeout \u00e0 $U (spam de link)', 'Ban \uc624b $U (flamewar)'];
var SIPES = ['Entrou no chat', 'Saiu do chat'];
var BADGES = { mod:{t:'\u2694',c:'badge-mod'}, sub:{t:'\u2605',c:'badge-sub'}, vip:{t:'\u25c6',c:'badge-vip'} };
var CANAIS = [
  ['Gaules', 'Just Chatting', 15400, 'gaules'], ['Cellbit', 'Just Chatting', 8120, 'cellbit'], ['Casimiro', 'Just Chatting', 12300, 'casimiro'],
  ['Nobru', 'Just Chatting', 3410, 'nobru'], ['Ibai', 'Just Chatting', 5400, 'ibai'], ['xQc', 'Just Chatting', 990, 'xqc'],
  ['Kai Cenat', 'IRL', 21050, 'kaicenat'], ['Ninja', 'Valorant', 6870, 'ninja'], ['Pokimane', 'Just Chatting', 4300, 'pokimane'],
  ['TheGrefg', 'Just Chatting', 5200, 'thegrefg'], ['Xokas', 'Just Chatting', 3900, 'xokas'], ['Auronplay', 'Minecraft', 4600, 'auronplay']
];

/* ---------- config ---------- */
var CONF = { nome: 'RaioGamer', titulo: 'RADANDO!! ATÉ A META — 🎯 HOT HARD (dia 7)', cat: 'Minecraft RPG',
  viewers: 15412, vel: 4, seg: 150000, meta: 30000, ritmo: 3, crescer: true, bannerImg: '', perfilImg: '', canalImg: '' };
try {
  var salvo = localStorage.getItem('twichfake_conf');
  if (salvo) { CONF = Object.assign(CONF, JSON.parse(salvo)); }
} catch (e) { /* pode ficar vazia */ }

function salvarConf() {
  try { localStorage.setItem('twichfake_conf', JSON.stringify(CONF)); } catch (e) { }
}

/* ---------- refs ---------- */
function $(id) { return document.getElementById(id); }
var elLive = $('canLive'), elMsgs = $('chatMsgs'), elInput = $('chatInput');
var elViews = $('viewCount'), elTimer = $('streamTimer'), elPpls = $('chatPpls');
var elNome = $('nomeStreamer'), elTitulo = $('tituloStream'), elAvatar = $('imgAvatar');
var elToasts = $('toasts'), elRaid = $('raidBanner'), elRaidTxt = $('raidTexto');
var elTrola = $('trolaBanner'), elMestre = $('mestre');

/* ---------- helpers ---------- */
function rnd(n) { return Math.floor(Math.random() * n); }
function pick(arr) { return arr[rnd(arr.length)]; }
function fmt(n) { return n.toLocaleString('pt-BR'); }
function tempo(s) {
  var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), seg = s % 60;
  return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m + ':' + (seg < 10 ? '0' : '') + seg;
}

var Som = null;
function beep(alt) {
  try {
    Som = Som || new (window.AudioContext || window.webkitAudioContext)();
    var o = Som.createOscillator(), g = Som.createGain();
    o.connect(g); g.connect(Som.destination);
    o.frequency.value = alt ? 880 : 520;
    g.gain.value = 0.05;
    o.start(); o.stop(Som.currentTime + 0.18);
  } catch (e) { }
}

/* ---------- chat ---------- */
function badgeHtml(u) {
  var p = rnd(100);
  if (p < 7) return '<span class="badge-msg badge-mod">' + BADGES.mod.t + '</span>';
  if (p < 30) return '<span class="badge-msg badge-sub">' + BADGES.sub.t + '</span>';
  if (p < 34) return '<span class="badge-msg badge-vip">' + BADGES.vip.t + '</span>';
  return '';
}

function pushMsg(html, classe) {
  if (!LiveOn && classe !== 'sistema') return;
  var d = document.createElement('div');
  d.className = 'mensagem' + (classe ? ' ' + classe : '');
  d.innerHTML = html;
  var pai = elMsgs;
  var embaixo = pai.scrollHeight - pai.scrollTop - pai.clientHeight < 90;
  pai.appendChild(d);
  while (pai.children.length > 120) pai.removeChild(pai.firstChild);
  if (embaixo) pai.scrollTop = pai.scrollHeight;
}

function chatTick() {
  if (!LiveOn) return;
  var p = rnd(100) < 6;
  if (p) {
    pushMsg('<span class="msg-txt">' + pick(DONATES) + '</span>', 'donate');
    beep(true); toast('\ud83d\udcb8 ' + pick(USERS) + ' ' + pick(DONATES));
    return;
  }
  p = rnd(100) < 4;
  if (p) {
    var u2 = pick(USERS);
    pushMsg('Timed out \u00e0 ' + u2 + ' (spam de link) por um mod', 'mod-acao');
    return;
  }
  p = rnd(100) < 4;
  if (p) { pushMsg(pick(USERS) + ' ' + pick(SIPES), 'sistema'); return; }

  var u = pick(USERS);
  var cor = CORES[rnd(CORES.length)];
  var txt = (Math.random() < 0.65 ? pick(CHAT_REAL) : pick(FRASES));
  pushMsg(badgeHtml(u) + '<b class="usuario" style="color:' + cor + '">' + u + '</b>: ' +
    '<span class="msg-txt">' + txt + '</span>');
}

var TimerChat = null;
function ligaChat() {
  if (TimerChat) clearInterval(TimerChat);
  var ms = Math.max(140, 1500 / CONF.vel);
  TimerChat = setInterval(chatTick, ms);
}

/* ---------- viewers: motor de CRESCIMENTO (nunca fica travado) ---------- */
var LiveV = parseInt(CONF.viewers, 10) || 15000;
var MetaV = parseInt(CONF.meta, 10) || 30000;
var Ritmo = (parseInt(CONF.ritmo, 10) >= 1) ? parseInt(CONF.ritmo, 10) : 3;
var CrescerAuto = (CONF.crescer !== false);
var FezMarcos = {};
var LiveOn = true;
var ViralMode = false;
var ModPerm = true; /* dono da live (streamer) tem mod; quem entra via link fica como viewer */
var Compart = false; /* streamer compartilhando tela (Ometv) no palco */
function updWait() {
  var ws = $('waitScreen');
  if (!ws) return;
  var show = !!(AuthUser && !ModPerm && !Compart);
  if (show) { $('waitAvatar').src = elAvatar.src; $('waitNome').textContent = CONF.nome; $('waitTxt').textContent = 'O transmiss\u00e3o est\u00e1 offline no momento... aguardem a pr\u00f3xima transmiss\u00e3o!'; ws.classList.remove('oculto'); }
  else { ws.classList.add('oculto'); }
}
function updHud() {
  var isViewer = !!(AuthUser && !ModPerm);
  var b1 = $('btnTela'), b2 = $('micBtn');
  if (b1) b1.style.display = isViewer ? 'none' : '';
  if (b2) b2.style.display = isViewer ? 'none' : '';
}
function updTopProfile() {
  var b = $('meuAvatar');
  if (!b) return;
  if (AuthUser && !ModPerm) {
    var seed = (AuthUser || '').toLowerCase().replace(/[^a-z0-9]/g, '') || 'raio';
    b.style.backgroundImage = 'url(' + avUrl('gamer portrait avatar, purple neon, stylized', seed.length * 7 + 99) + ')';
    b.style.backgroundSize = 'cover';
  }
}

function encerrarLive() {
  if (!LiveOn) return;
  LiveOn = false;
  pararTela();
  var off = $('offScreen');
  if (off) {
    $('offAvatar').src = elAvatar.src;
    $('offNome').textContent = CONF.nome;
    off.classList.remove('oculto');
  }
  var lp = $('livePill');
  if (lp) { lp.textContent = '\u2b13 OFFLINE'; lp.classList.add('off'); }
  pushMsg('A transmiss\u00e3o de ' + CONF.nome + ' acabou. Volte em breve \ud83d\ude4f', 'sistema');
  document.title = 'Twich';
  toast('\ud83d\udcf4 Live encerrada! (a galera vai chorar \ud83d\ude2d)');
}
function voltarLive() {
  if (LiveOn) return;
  LiveOn = true;
  var off = $('offScreen'); if (off) off.classList.add('oculto');
  var lp = $('livePill');
  if (lp) { lp.textContent = '\u25cf AO VIVO'; lp.classList.remove('off'); }
  document.title = CONF.nome + ' \u2014 AO VIVO';
  toast('\ud83d\udd34 AO VIVO de novo! A comunidade voltou');
}
$('mEncerrar').onclick = encerrarLive;
$('mVoltar').onclick = voltarLive;
$('mVoltar2').onclick = voltarLive;

setInterval(function () {
  if (!LiveOn) {
    elViews.textContent = '\u2014';
    elPpls.textContent = '\ud83d\udc65 offline';
    var mL = $('mLive'); if (mL) mL.textContent = fmt(LiveV);
    return;
  }
  if (CrescerAuto && LiveV < MetaV) {
    var passo = LiveV * 0.0075 * Ritmo + 14 + rnd(30) - 10;
    if (ViralMode) passo *= 5;
    if (LiveV > MetaV * 0.92) passo *= 0.45;
    LiveV = Math.max(LiveV + Math.round(passo), 50);
  }
  var v = LiveV + rnd(360) - 150;
  if (v < 60) v = 60 + rnd(120);
  elViews.textContent = fmt(v);
  elPpls.textContent = '\ud83d\udc65 ' + fmt(Math.floor(v * 0.32));
  var mL = $('mLive'); if (mL) mL.textContent = fmt(LiveV);
  [20000, 25000, 30000, 40000, 50000].forEach(function (m) {
    if (LiveV >= m && !FezMarcos[m]) {
      FezMarcos[m] = true;
      elRaidTxt.textContent = 'A LIVE EXPLODIU: ' + fmt(m) + ' ESPECTADORES!!';
      elRaid.classList.remove('oculto');
      setTimeout(function () { elRaid.classList.add('oculto'); }, 7000);
      toast('\ud83d\ude80 ' + fmt(m) + ' pessoas assistindo!');
      beep(true);
    }
  });
}, 2600);

/* ---------- relogio da stream ---------- */
var Segundos = 0;
setInterval(function () { if (!LiveOn) return; Segundos += 1; elTimer.textContent = tempo(Segundos); }, 1000);

/* ---------- toasts ---------- */
function toast(txt) {
  var d = document.createElement('div');
  d.className = 'toast';
  d.textContent = txt;
  elToasts.appendChild(d);
  setTimeout(function () { d.remove(); }, 5200);
}

/* ---------- Raid ---------- */
function raid() {
  var nome = pick(USERS);
  var n = 400 + rnd(2600);
  elRaidTxt.textContent = nome + ' trouxe ' + fmt(n) + ' pessoas!';
  elRaid.classList.remove('oculto');
  beep(true);
  setTimeout(function () { elRaid.classList.add('oculto'); }, 7000);
}

/* ---------- botoes ---------- */
$('btnSeguir').onclick = function () {
  toast('\u2764\ufe0f Agora voce segue ' + CONF.nome + '!');
  $('btnSeguir').textContent = '\u2764 Seguindo';
};
$('btnFollow').onclick = function () {
  toast('\u2b50 Sub Tier 1 ativado (parodia, claro)\u2026 (brincadeira!)');
  pushMsg('<b class="usuario" style="color:#c79bff">' + CONF.nome + '</b>: <span class="msg-txt">OBRIGADO PELO SUB AMIGO!! \ud83d\udc99</span>', 'donate');
  beep(true);
};

/* ---------- envio do chat ---------- */
var AuthUser = (function () { try { return localStorage.getItem('twichfake_auth') || ''; } catch (e) { return ''; } })();
function setAuthUser(n) { AuthUser = n || ''; try { localStorage.setItem('twichfake_auth', n); } catch (e) { } }
function abrirLogin() { $('loginPag').classList.remove('oculto'); $('loginUser').value = AuthUser; var lc = $('loginCanalNome'); if (lc) lc.textContent = CONF.nome; }
function loginOkFn() {
  var n = ($('loginUser').value || '').trim();
  if (!n) return;
  var pw = $('loginPw') ? ($('loginPw').value || '').trim() : '';
  setAuthUser(n);
  ModPerm = false;
  updHud();
  updTopProfile();
  updWait();
  $('loginPag').classList.add('oculto');
  elInput.placeholder = 'mandar mensagem...';
  toast('\ud83d\udc4b Entrada liberada, ' + n + '! (só assistindo por enquanto)');
  pushMsg('<b class="usuario" style="color:#8ea0ff">' + n + '</b>: <span class="msg-txt">entrou na live 👋</span>', 'sistema');
}
$('btnEntrar').onclick = abrirLogin;
$('loginOk').onclick = loginOkFn;

/* ---------- LINK DA LIVE (copiar pra mandar a galera entrar) ---------- */
function linkLive() {
  var base = (location.href || '').split('?')[0];
  var l = base + '?nick=' + encodeURIComponent((CONF.nome || 'RaioGamer'));
  var t = $('mLinkTxt'); if (t) t.value = l; return l;
}
$('mLink').onclick = function () {
  var l = linkLive();
  try { navigator.clipboard.writeText(l); } catch (e) { var ta = document.createElement('textarea'); ta.value = l; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); }
  toast('🔗 Link da live copiado! Envie pro amigo: ' + l);
};
var nickUrl = (function () { try { return new URLSearchParams(location.search || '').get('nick') || ''; } catch (e) { return ''; } })();
if (nickUrl) { $('loginUser').value = nickUrl; $('loginPag').classList.remove('oculto'); }
$('meuAvatar').onclick = function () {
  if (AuthUser) {
    var slug = AuthUser.toLowerCase().replace(/[^a-z0-9]/g, '') || 'raio';
    try { window.open('https://www.twitch.tv/' + encodeURIComponent(slug), '_blank'); return; } catch (e) { }
    return;
  }
  abrirPerfi();
};

var Likes = parseInt(CONF.likes, 10) || 128;
function curtir() { if (!ModPerm && !AuthUser) { toast('\ud83d\udca5 Apenas moderadores curtem aqui'); return; } Likes += 1; toast('\u2764\ufe0f ' + fmt(Likes) + ' curtidas! Obrigado(a), voce curtiu!'); beep(true); }
$('btnLike').onclick = curtir;
$('btnSubChat').onclick = function () {
  if (!ModPerm) { toast('\ud83d\udca5 Apenas moderadores inscrevem aqui'); return; }
  toast('\u2b50 Inscri\u00e7\u00e3o fake ativada! Obrigado pela par\u00f3dia, ' + (AuthUser || 'amigo') + '!');
  pushMsg(badgeHtml('x') + '<b class="usuario" style="color:#c79bff">' + (AuthUser || CONF.nome) + '</b>: <span class="msg-txt">OBRIGADO PELO SUB AMIGO!! \ud83d\udc99</span>', 'donate');
  beep(true);
};

function enviarLocal() {
  var t = elInput.value.trim();
  if (!t) return;
  if (!ModPerm && !AuthUser) { toast('🚫 Apenas moderadores podem falar na live'); return; }
  var nome = AuthUser || 'convidado_84';
  var cor = CORES[rnd(CORES.length)];
  pushMsg('<span class="badge-msg badge-voce">V</span><b class="usuario" style="color:' + cor + '">' + nome + '</b>: ' +
    '<span class="msg-txt">' + t.replace(/</g, '&lt;') + '</span>');
  elInput.value = '';
  var delay = 900 + rnd(2400);
  setTimeout(function () {
    var resp = pick(['kkkk resposta foda', 'verdade! @' + nome, 'concordo total', 'kkk kkk cala boca \ud83d\ude02']);
    pushMsg(badgeHtml('x') + '<b class="usuario" style="color:' + pick(CORES) + '">' + pick(USERS) + '</b>: <span class="msg-txt">' + resp + '</span>');
  }, delay);
}
$('chatSend').onclick = enviarLocal;
elInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') enviarLocal(); });

/* ---------- painel do mestre ---------- */
$('mNome').value = CONF.nome; $('mTitulo').value = CONF.titulo;
$('mCat').value = CONF.cat;
$('mVelocidade').value = CONF.vel;

function aplicou() {
  elNome.textContent = CONF.nome;
  elTitulo.textContent = CONF.titulo;
  document.title = CONF.nome + ' \u2014 AO VIVO';
  var cat = document.querySelector('.cat-stream a');
  if (cat) cat.textContent = CONF.cat;
  ligaChat();
}
aplicou();

$('mSalvar').onclick = function () {
  CONF.nome = ($('mNome').value || CONF.nome).trim();
  CONF.titulo = $('mTitulo').value || CONF.titulo;
  CONF.cat = $('mCat').value || CONF.cat;
  CONF.viewers = LiveV;
  CONF.vel = parseInt($('mVelocidade').value, 10) || 4;
  salvarConf(); aplicou();
  toast('\ud83d\udcbe Treta atualizada em tempo real!');
};
$('mRaid').onclick = raid;
$('mFechar').onclick = function () { elMestre.classList.add('oculto'); };
/* (elementos do layout antigo removidos no redesign igual-Twitch) */

document.addEventListener('keydown', function (e) {
  var tag = (e.target && e.target.tagName) || '';
  if (tag === 'INPUT' || tag === 'TEXTAREA') return;
  if (e.key === 'p' || e.key === 'P') { if (ModPerm) elMestre.classList.toggle('oculto'); }
  if (e.key === 'b' || e.key === 'B') elTrola.classList.toggle('oculto');
});

/* ---------- rail lateral de canais (igual Twitch) ---------- */
(function montarRail() {
  var rail = $('railAvatars');
  CANAIS.forEach(function (c, i) {
    var img = 'https://unavatar.io/twitch/' + encodeURIComponent(c[3] || c[0]) + '?fallback=false';
    var live = (i !== 2 && i !== 7);
    var b = document.createElement('button');
    b.className = 'rail-av';
    b.title = c[0] + (live ? ' \u2014 AO VIVO' : '');
    b.innerHTML = '<img src="' + img + '" alt="' + c[0] + '" onerror="this.onerror=null;this.src=\'' +
      avUrl('gamer portrait avatar, purple neon, stylized', i * 7 + 3) + '\'">' +
      (live ? '<span class="av-live">LIVE</span>' : '');
    b.onclick = function () {
      /* clique no streamer leva DIRETO pro twitch real (mantem o segredo da parodia) */
      try { window.open('https://www.twitch.tv/' + encodeURIComponent(c[3] || c[0]), '_blank'); return; } catch (e) { }
      CONF.nome = c[0]; CONF.cat = c[1]; CONF.viewers = Math.max(1200, c[2]);
      salvarConf(); aplicou();
      toast('\ud83c\udfa5 Trocou para ' + c[0] + ' ao vivo!');
    };
    rail.appendChild(b);
  });
  elAvatar.src = 'https://image.pollinations.ai/prompt/' + encodeURIComponent(
    'gamer portrait avatar, neon purple lighting, stylized character') + '?width=120&height=120&nologo=true&seed=5';
  $('meuAvatar').style.backgroundImage = 'url(' + elAvatar.src + ')';
  $('meuAvatar').style.backgroundSize = 'cover';
})();

/* ---------- canvas: "gameplay" ao vivo ---------- */
(function jogo() {
  var c = elLive, ctx = c.getContext('2d');
  var Hero = { x: 200, y: 300, dx: 1.7, dy: 1.0 };
  var Bots = [];
  for (var i = 0; i < 26; i++) Bots.push({ x: rnd(c.width), y: rnd(c.height), v: 0.6 + Math.random() * 2 });

  function frame() {
    ctx.fillStyle = '#0b0d12';
    ctx.fillRect(0, 0, c.width, c.height);
    var g = ctx.createRadialGradient(c.width / 2, c.height / 2, 40, c.width / 2, c.height / 2, 460);
    g.addColorStop(0, 'rgba(145,70,255,.16)'); g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, c.width, c.height);

    ctx.strokeStyle = 'rgba(255,255,255,.05)';
    for (var x = 0; x < c.width; x += 64) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, c.height); ctx.stroke(); }
    for (var y = 0; y < c.height; y += 64) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(c.width, y); ctx.stroke(); }

    ctx.fillStyle = '#ff4d4d';
    Bots.forEach(function (b) {
      b.x += b.v; if (b.x > c.width + 30) b.x = -30;
      ctx.beginPath(); ctx.arc(b.x, b.y, 5, 0, Math.PI * 2); ctx.fill();
    });

    Hero.x += Hero.dx * 2.1; Hero.y += Math.sin(Hero.x / 60) * 1.4;
    if (Hero.x > c.width - 40 || Hero.x < 40) Hero.dx *= -1;
    ctx.save();
    ctx.shadowColor = '#9146ff'; ctx.shadowBlur = 24;
    ctx.fillStyle = '#efeff1';
    ctx.fillRect(Hero.x - 9, Hero.y - 9, 18, 18);
    ctx.restore();

    requestAnimationFrame(frame);
  }
  frame();
})();

/* ---------- treta inicial ---------- */
ligaChat();
setInterval(function () { if (Math.random() < 0.35) raid(); }, 205000);
pushMsg('<span class="msg-txt">Bem-vindo ao AO VIVO de ' + CONF.nome + ' \ud83c\udfae</span>', 'sistema');

/* ---------- COMPARTILHAR A TELA REAL (seu Ometv vira a transmissao) ---------- */
function pararTela() {
  var vid = $('vidCompart');
  try {
    if (vid.srcObject) vid.srcObject.getTracks().forEach(function (t) { t.stop(); });
  } catch (e) { }
  vid.srcObject = null;
  vid.classList.add('oculto');
  if (document.fullscreenElement) { try { document.exitFullscreen(); } catch (e) { } }
  document.querySelector('.palco').classList.remove('share-on');
  $('btnTela').textContent = '\ud83d\udda5\ufe0f Compartilhar tela';
  Compart = false;
  updWait();
}

$('btnTela').onclick = function () {
  if (AuthUser && !ModPerm) { toast('🚫 Apenas o transmissor pode compartilhar a tela'); return; }
  var vid = $('vidCompart');
  if (vid.srcObject) { pararTela(); return; }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
    toast('\u26a0\ufe0f Captura de tela nao suportada neste modo. Abra em janela NORMAL do Chrome (sem Kiosk).');
    return;
  }
  navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 30 }, audio: false }).then(function (stream) {
    vid.srcObject = stream;
    vid.classList.remove('oculto');
    document.querySelector('.palco').classList.add('share-on');
    var pais = document.querySelector('.palco');
    try { if (pais.requestFullscreen) pais.requestFullscreen().catch(function () { }); } catch (e) { }
    $('btnTela').textContent = '\u23f9\ufe0f Parar transmiss\u00e3o';
    Compart = true;
    updWait();
    var trk = stream.getVideoTracks()[0];
    if (trk && trk.addEventListener) trk.addEventListener('ended', pararTela);
    toast('\ud83d\udda5\ufe0f Sua tela (Ometv) esta no ar como transmissao!');
    pushMsg('<b class="usuario" style="color:#4fc1ff">Sistema</b>: <span class="msg-txt">a transmissao esta sendo compartilhada \ud83c\udfa5</span>', 'sistema');
  }).catch(function () {
    toast('\u26a0\ufe0f Escolha a janela/aba do Ometv na lista. Se nada abrir: use janela NORMAL do Chrome (sem Kiosk).');
  });
};

/* ---------- CHAT QUE REAGE a live (Ometv: elogios, perguntas, zoacao, hype) ---------- */
var ELOG = ['linda demais \ud83d\ude0d', 'oi gata, vem pra live \ud83d\udc99', 'quem e essa aiii \ud83d\ude0d', 'a morena e top \ud83d\ude18',
  'charme demais homi rs', 'parabens pelo sorriso \ud83d\ude0d', 'essa live e o melhor lugar do br hoje', 'visual 10/10 \u2728',
  'a loira entende \ud83d\udc85', 'ain meu casa \ud83d\ude2d\u2764\ufe0f', 'vc e muito bem vindo aqui divoa', 'beijo pra ela tbm \ud83d\udc8b'];
var PERG = ['de onde vc e?', 'quantos anos vc tem?', 'vc esta sozinho a?', 'fala meu nome no oi \ud83d\ude33',
  'que hora e a no br?', 'vc usa oculos?', 'vc tem namorada? \ud83d\ude02', 'faz o famoso oi diva', 'casado ou solteiro? rs',
  'nome do seu discord?', 'vc mora sozinho?', 'essa e sua casa?'];
var ZOAR = ['KKKKKKKK O QUE FOI ISSO', 'zero tecnico esse a', 'tropheu kkkkk', 'a cara deletom levou view kkkk',
  'chat sempre zoa \ud83d\ude02', 'desisti de entender kkk', 'kkkk a reacao dele foi unica', ' KK miscelanea ca',
  'vou clipa essa kkk \ud83d\udcf8', 'combo mais erro kkk', 'o next dele nunca bate kkkk', 'ele fala rapido demais \ud83d\ude02'];
var HYPE = ['NEXT NEXT NEXT', 'GGGGG', 'POG \ud83d\ude31', 'LIVE LINDA', '15k on fire \ud83d\udd25', 'arma essa live \ud83d\udd25',
  'me segue aAi \ud83d\ude2d', 'subs no ar \u2b50', 'VAMO VAMO', 'clipa isso ja', 'hype train saindo', 'melhor live'];
var CTX = ['de onde vc e ?', 'vc ta vendo o chat?', 'oi pros brasileiros', 'ddiferente aquele a de tras \ud83d\ude05',
  'vc bebe? kkk', 'a sua internete ta boa?', 'mostro o tonguai hack', 'quantas pessoas eu trago \ud83d\ude0d',
  'vc fala ingles?', 'aka vamo numa outra chamada', 'ela apagou o next kkk', 'uaau o fundo do seu quarto',
  'vc e bem solucionado', 'poe uma musica a', 'oi da colombia ble', 'num sei se era linda ou a luze', 'vc gaia e nada \ud83d\ude05'];

function ondaMsgs(banco, total) {
  var i = 0;
  var t = setInterval(function () {
    if (i >= total) { clearInterval(t); return; }
    pushMsg(badgeHtml('x') + '<b class="usuario" style="color:' + pick(CORES) + '">' + pick(USERS) + '</b>: <span class="msg-txt">' + pick(banco) + '</span>');
    i++;
  }, 420);
}

/* IA (Pollinations, gratuita) gera reacoes a partir do que voce contar */
function reageIA() {
  var ctx = (lastFalado || ($('mCtx') && $('mCtx').value.trim()) || 'o streamer caiu de novo no next no Ometv');
  toast('\ud83e\udde0 Chamando a IA pra reagir ao momento...');
  var quando = new Date().toLocaleDateString('pt-BR', { weekday: 'long' }) + ', ' + new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  var sysp = 'Voce e o chat de uma live ao vivo estilo Twitch (PT-BR) transmitida AGORA: e ' + quando + '. O streamer esta AO VIVO e neste momento esta no site Ometv (conversas por video aleatoria) com o chat vendo a tela dele. ' +
    'Escreva 8 mensagens curtas de espectadores, UMA POR LINHA, sem numerar e sem aspas, com emojis, estilo live brasileira: ' +
    'perguntas (de onde esta, idade, nome), elogios (principalmente se aparecer mulher na tela), zoacao leve, hype (next, clipa, GG) e agencia da live (vai ter valorant hoje?). Reaja especificamente ao momento descrito.';
  fetch('https://text.pollinations.ai/openai', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: 'openai', messages: [{ role: 'system', content: sysp }, { role: 'user', content: 'Momento da live: ' + ctx }] })
  }).then(function (r) { return r.json(); }).then(function (d) {
    var txt = (d && d.choices && d.choices[0] && d.choices[0].message && d.choices[0].message.content) || '';
    var linhas = txt.split(/\n+/).map(function (s) { return s.trim(); }).filter(Boolean).slice(0, 9);
    if (!linhas.length) throw new Error('vazio');
    linhas.forEach(function (l, i) {
      setTimeout(function () {
        pushMsg(badgeHtml('x') + '<b class="usuario" style="color:' + pick(CORES) + '">' + pick(USERS) + '</b>: <span class="msg-txt">' + l.replace(/</g, '&lt;') + '</span>');
      }, i * 520);
    });
    toast('\ud83d\ude80 O chat viu mesmo o que rolou!');
  }).catch(function () {
    toast('\u26a0\ufe0f IA sem resposta, usando reacoes locais');
    ondaMsgs(CTX, 8);
  });
}

$('mIA').onclick = reageIA;
$('mW1').onclick = function () { ondaMsgs(ELOG, 8); };
$('mW2').onclick = function () { ondaMsgs(PERG, 8); };
$('mW3').onclick = function () { ondaMsgs(ZOAR, 8); };
$('mW4').onclick = function () { ondaMsgs(HYPE, 8); };

/* gatilhos por teclado 1/2/3/4 */
document.addEventListener('keydown', function (e) {
  var tag = (e.target && e.target.tagName) || '';
  if (tag === 'INPUT' || tag === 'TEXTAREA') return;
  if (e.key === '1') ondaMsgs(ELOG, 8);
  if (e.key === '2') ondaMsgs(PERG, 8);
  if (e.key === '3') ondaMsgs(ZOAR, 8);
  if (e.key === '4') ondaMsgs(HYPE, 8);
});

/* idle: chat sempre comentando a live como se visse a tela */
setInterval(function () {
  if (!LiveOn) return;
  if (Math.random() < 0.45) {
    pushMsg(badgeHtml('x') + '<b class="usuario" style="color:' + pick(CORES) + '">' + pick(USERS) + '</b>: <span class="msg-txt">' + pick(CTX) + '</span>');
  }
}, 6500);

/* seguidores novos e gifts */
setInterval(function () {
  if (!LiveOn) return;
  if (Math.random() < 0.35) pushMsg(pick(USERS) + ' seguiu o canal \ud83d\udc9c', 'sistema');
}, 8000);
setInterval(function () {
  if (Math.random() < 0.3) {
    var g = pick(USERS), n = 1 + rnd(4);
    pushMsg('<b class="usuario" style="color:#c79bff">' + g + '</b>: <span class="msg-txt">presenteou ' + n + ' sub(s) Tier 1 \u2b50</span>', 'donate');
    toast('\ud83c\udf81 ' + g + ' presenteou ' + n + ' sub(s)!');
    beep(true);
    if (Math.random() < 0.5) {
      var gh = $('hypeTrain');
      $('hypeIdx').textContent = 2 + rnd(8);
      gh.classList.remove('oculto');
      setTimeout(function () { gh.classList.add('oculto'); }, 9000);
    }
  }
}, 48000);

/* pinned */
setTimeout(function () { $('pinMsg').classList.remove('oculto'); }, 15000);
setInterval(function () {
  $('pinMsg').classList.remove('oculto');
  setTimeout(function () { $('pinMsg').classList.add('oculto'); }, 30000);
}, 110000);

/* pontos do canal (claim ) */
var MeusPontos = 0;
$('pillPontos').onclick = function () {
  MeusPontos += 50;
  $('pillPontos').classList.add('oculto');
  toast('\ud83c\udf81 Pontos do canal: +50 (total ' + MeusPontos + ')');
  setTimeout(function () { $('pillPontos').classList.remove('oculto'); }, 45000 + rnd(40000));
};

/* emotes reais estilo Twitch */
var EMOTES = [['Kappa', '\ud83d\ude0f'], ['LUL', '\ud83d\ude39'], ['Pog', '\ud83d\ude2e'], ['monkaS', '\ud83d\ude28'],
  ['EZClap', '\ud83d\udc4f'], ['KappaPride', '\ud83c\udf08'], ['PJSalt', '\ud83d\ude44'], ['FeelsGoodMan', '\ud83d\udc38'],
  ['4Head', '\ud83d\ude05'], ['VoHiYo', '\ud83c\udf8a'], ['BlessRNG', '\ud83d\ude4f'], ['BibleThump', '\ud83d\ude2d']];
(function grid() {
  var g = $('emoteGrid');
  EMOTES.forEach(function (e) {
    var d = document.createElement('div');
    d.className = 'emote-item';
    d.innerHTML = e[1] + '<span>' + e[0] + '</span>';
    d.onclick = function () {
      elInput.value = (elInput.value ? elInput.value + ' ' : '') + e[0] + ' ';
      elInput.focus();
    };
    g.appendChild(d);
  });
})();
$('chatEmote').onclick = function () { $('emoteGrid').classList.toggle('oculto'); };
$('btnGear').onclick = function () { toast('\u2699\ufe0f Chat: timestamps, men\u00e7\u00f5es, idioma... (parodia)'); };

/* lista de usuarios no chat */
$('chatPpls').onclick = function () {
  var jah = $('listaPop');
  if (jah) { jah.remove(); return; }
  var d = document.createElement('div');
  d.id = 'listaPop';
  d.className = 'lista-pop';
  var h = '<b>\ud83d\udc65 Espectadores no chat</b><hr>';
  for (var i = 0; i < 18; i++) {
    h += '<div>' + USERS[rnd(USERS.length)] + (i < 3 ? ' <span style="color:#00ad03">\u2713 mod</span>' : '') + '</div>';
  }
  d.innerHTML = h;
  document.querySelector('.chat').appendChild(d);
};

/* barra de controle do player */
var elPalco = document.querySelector('.palco');
$('volRange').oninput = function () { $('btnVol').textContent = (this.value == 0) ? '\ud83d\udd07' : '\ud83d\udd0a'; };
$('btnVol').onclick = function () { this.textContent = (this.textContent.indexOf('\ud83d\udd0a') > -1) ? '\ud83d\udd07' : '\ud83d\udd0a'; };
$('btnConf').onclick = function () { toast('\u2699\ufe0f Qualidade: 1080p60 (fonte) \u2014 desligar/oscutar: parodia'); };
$('btnTeatro').onclick = function () { document.body.classList.toggle('teatro'); };
$('btnFS').onclick = function () {
  if (document.fullscreenElement) document.exitFullscreen();
  else if (elPalco.requestFullscreen) elPalco.requestFullscreen();
};
$('btnPresente').onclick = function () {
  toast('\ud83c\udf81 Gift a Sub: escolha um do chat!');
  ondaMsgs(HYPE, 5);
};
$('btnCompart').onclick = function () {
  try { navigator.clipboard.writeText(location.href); } catch (e) { }
  toast('\ud83d\udd17 Link da live copiado! Manda pra galera');
};
$('btnMais').onclick = function () { toast('\u22ef Sobre \u00b7 Denunciar \u00b7 Widgets de canal'); };
$('btnSino').onclick = function () {
  $('btnSino').classList.toggle('on');
  if ($('btnSino').classList.contains('on')) toast('\ud83d\udd14 Notifica\u00e7\u00f5es de ' + CONF.nome + ' ativadas!');
};

/* ---------- ad-break (como no Twitch real) + hora no rodape do chat ---------- */
(function horaRodape() {
  var t2 = $('streamTimer2');
  setInterval(function () { if (t2) t2.textContent = elTimer.textContent; }, 1000);
})();
setTimeout(function () {
  var ad = $('adSlot');
  function adCiclo() {
    ad.classList.remove('oculto');
    toast('\ud83d\udcfa Ad break! (igual Twitch real \ud83d\ude02)');
    setTimeout(function () { ad.classList.add('oculto'); }, 22000);
  }
  setInterval(function () { if (Math.random() < 0.45) adCiclo(); }, 200000);
  adCiclo();
}, 80000);
$('btnChatMin').onclick = function () { document.body.classList.toggle('semchat'); };

/* =====================================================
   NIVEL 4: VOZ AO VIVO, FOTO POR IA e CRESCIMENTO
   ===================================================== */

/* ----- IA: o chat reage AO QUE VOCE FALA ----- */
var lastFalado = '';
function falaIA(texto) {
  var quando = new Date().toLocaleDateString('pt-BR', { weekday: 'long' }) + ', ' + new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  var sysp = 'Voce e o chat (PT-BR) de uma live Twitch AO VIVO, transmitida agora (' + quando + '). Ele esta transmitindo enquanto usa o site Ometv (conversas por video aleatoria) e o chat ve a tela. O streamer acabou de FALAR isto em voz alta: "' +
    texto + '". Escreva 6 mensagens curtas de espectadores, UMA POR LINHA, sem numerar e sem aspas, reagindo de verdade ao assunto ' +
    'que ele falou, como pessoas que estao assistindo: perguntando detalhes do que foi dito, rindo, elogiando quando couber ' +
    'principalmente se ele citou alguma mulher, e hype (clipa isso). Mencionar palavras especificas do que ele disse deixa tudo real.';
  fetch('https://text.pollinations.ai/openai', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: 'openai', messages: [{ role: 'system', content: sysp }, { role: 'user', content: 'Reaja curto, no clima de live:' }] })
  }).then(function (r) { return r.json(); }).then(function (d) {
    var txt = (d && d.choices && d.choices[0] && d.choices[0].message && d.choices[0].message.content) || '';
    var linhas = txt.split(/\n+/).map(function (s) { return s.trim(); }).filter(Boolean).slice(0, 7);
    if (!linhas.length) throw new Error('vazio');
    linhas.forEach(function (l, i) {
      setTimeout(function () {
        pushMsg(badgeHtml('x') + '<b class="usuario" style="color:' + pick(CORES) + '">' + pick(USERS) + '</b>: <span class="msg-txt">' + l.replace(/</g, '&lt;') + '</span>');
      }, i * 560);
    });
  }).catch(function () {
    var resps = ['juro que ouvi aquilo \ud83d\ude33', 'kkkkkk que foi isso', 'explica isso melhor aai', 'ele tava falando da gata?', 'o chat entendeu TUDO'];
    resps.forEach(function (t, i) {
      setTimeout(function () {
        pushMsg(badgeHtml('x') + '<b class="usuario" style="color:' + pick(CORES) + '">' + pick(USERS) + '</b>: <span class="msg-txt">' + t + '</span>');
      }, i * 500);
    });
  });
}

/* microfone: escuta continua EVOLUIDA (parcial ao vivo, anti-repeticao, retomada automatica) */
var Rec = null, Falando = false, UltimoFalou = '', UltimoTm = 0;
function updMicUI() {
  var pill = $('micPill'), mm = $('mMic'), mb = $('micBtn');
  if (pill) pill.classList.toggle('oculto', !Falando);
  if (mm) { mm.classList.toggle('on', Falando); mm.textContent = Falando ? '\u23f9\ufe0f Parar voz' : '\ud83c\udf99\ufe0f Ligar voz (tecla V)'; }
  if (mb) mb.classList.toggle('on', Falando);
}
function falaFinal(t) {
  t = (t || '').trim();
  if (t.length < 6) return;
  if (t === UltimoFalou && Date.now() - UltimoTm < 9000) return;
  UltimoFalou = t; UltimoTm = Date.now();
  lastFalado = t;
  var mf = $('mFala');
  if (mf) mf.textContent = '\ud83d\udd99 ' + t;
  if (!LiveOn) return;
  if (!reacaoComando(t)) falaIA(t);
}
function ligaVoz() {
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { toast('\u26a0\ufe0f Sem escuta neste navegador. Use Chrome normal (sem Kiosk).'); return; }
  if (Falando) { Falando = false; try { Rec.stop(); } catch (e) { } updMicUI(); return; }
  try {
    Rec = new SR();
    Rec.lang = 'pt-BR';
    Rec.continuous = true;
    Rec.interimResults = true;
    Rec.maxAlternatives = 1;
    Rec.onresult = function (e) {
      var r = e.results[e.results.length - 1];
      var txt = (r[0] && r[0].transcript) || '';
      var mf = $('mFala');
      if (r.isFinal) falaFinal(txt);
      else if (mf && txt) mf.textContent = '\u270d\ufe0f escrevendo: ' + txt + ' |';
    };
    Rec.onerror = function (ev) {
      if (ev.error === 'not-allowed') { Falando = false; updMicUI(); toast('\ud83d\udd12 Permita o MICROFONE no Chrome (cadeado na barra)'); }
    };
    Rec.onend = function () { if (Falando) { try { Rec.start(); } catch (e) { } } else updMicUI(); };
    Falando = true;
    Rec.start();
    updMicUI();
    lastFalado = '';
    toast('\ud83c\udf99\ufe0f Jarvis OUVINDO: fale naturalmente, o chat reage!');
  } catch (e) { Falando = false; updMicUI(); }
}
$('mMic').onclick = ligaVoz;
$('micBtn').onclick = ligaVoz;
document.addEventListener('keydown', function (e) {
  var tag = (e.target && e.target.tagName) || '';
  if (tag === 'INPUT' || tag === 'TEXTAREA') return;
  if (e.key === 'v' || e.key === 'V') ligaVoz();
});

/* ----- foto de perfil / avatar do canal POR IA ----- */
var PRESETS = [
  'anime portrait headshot, smiling, purple neon light',
  'cartoon wolf mascot head, purple',
  'young gamer with headphones, cinematic light',
  'pixel art face portrait',
  'cyberpunk portrait, blue rim lighting',
  'cute cat with headphones, cartoon'
];
function avUrl(prom, seed) {
  return 'https://image.pollinations.ai/prompt/' + encodeURIComponent(prom + ', centered headshot avatar') +
    '?width=112&height=112&nologo=true&seed=' + seed;
}
function setPerfilImg(src) {
  $('meuAvatar').style.backgroundImage = 'url(' + src + ')';
  $('meuAvatar').style.backgroundSize = 'cover';
  CONF.perfilImg = src; salvarConf();
}
function setCanalImg(src) {
  elAvatar.src = src;
  CONF.canalImg = src; salvarConf();
}
function avToast(tipo) { toast('\u2705 Foto aplicada em ' + (tipo === 'p' ? 'SEU PERFIL' : 'o canal') + ' \ud83d\uddbc\ufe0f'); }
$('btnPick').onclick = function () { $('avatarPick').classList.remove('oculto'); };
$('avFechar').onclick = function () { $('avatarPick').classList.add('oculto'); };
(function avMontares() {
  ['gridPerfil', 'gridCanal'].forEach(function (gid, gi) {
    var g = $(gid);
    PRESETS.forEach(function (p, i) {
      var im = document.createElement('img');
      im.src = avUrl(p, i * 13 + gi * 5 + 2);
      im.alt = 'opcao ' + (i + 1);
      im.onclick = function () {
        if (gi === 0) { setPerfilImg(im.src); avToast('p'); }
        else { setCanalImg(im.src); avToast('c'); }
      };
      g.appendChild(im);
    });
  });
  if (CONF.perfilImg) { $('meuAvatar').style.backgroundImage = 'url(' + CONF.perfilImg + ')'; $('meuAvatar').style.backgroundSize = 'cover'; }
  if (CONF.canalImg) { elAvatar.src = CONF.canalImg; }
})();
$('avGerar').onclick = function () {
  var p = $('avPrompt').value.trim();
  if (!p) { toast('\u270d\ufe0f Descreva sua foto antes de gerar'); return; }
  toast('\ud83e\udd0b A IA gerando sua foto...');
  var im = $('avPreview');
  im.src = avUrl(p, 1 + rnd(99999));
  im.onload = function () { $('avPrevWrap').classList.remove('oculto'); toast('\u2705 Pronta! Escolha onde usar'); };
};
$('avUsaPerfil').onclick = function () { if ($('avPreview').src) { setPerfilImg($('avPreview').src); avToast('p'); } };
$('avUsaCanal').onclick = function () { if ($('avPreview').src) { setCanalImg($('avPreview').src); avToast('c'); } };

/* ----- fotografia do PC: usa SUA foto real (temporizada e quadrada) ----- */
$('avFile').onchange = function () {
  var f = this.files && this.files[0];
  if (!f) return;
  var fr = new FileReader();
  fr.onload = function () {
    var im = new Image();
    im.onload = function () {
      var c = document.createElement('canvas'); c.width = 112; c.height = 112;
      var cx = c.getContext('2d');
      var s = Math.max(112 / im.width, 112 / im.height);
      var w = im.width * s, h = im.height * s;
      cx.drawImage(im, (112 - w) / 2, (112 - h) / 2, w, h);
      $('avPreview').src = c.toDataURL('image/jpeg', 0.85);
      $('avPrevWrap').classList.remove('oculto');
      toast('\u2705 Sua foto carregada! Escolha "meu perfil" ou "canal"');
    };
    im.src = fr.result;
  };
  fr.readAsDataURL(f);
};

/* ----- banco de falas NATURAIS (gente real acompanhando a live no Ometv) ----- */
var CHAT_REAL = ['vai ter valorant hoje?', 'dia de domingo com o melhor streamer', 'hoje o dia ta brabo rs',
  'tem stream hoje tbm a noite?', 'quem ta no ometv hoje?', 'manda next nos trols chat', 'de onde vc e streamer?',
  'quantos anos vc tem?', 'a lenda ta on rs', 'chat do dia esta brabooooo', 'vamos bater 30k hoje chat',
  'o melhor domingo da twitch', 'essa live nao para', 'invito geral a rs', 'segue la que so tem vibe',
  'quantas horas de live hoje?', 'alguem me da um sub ai', 'chat vamo comparecer no rank de hoje',
  'quem mais ta assistindo de lan house? kkk', 'aqui e BR na veia', 'GGs pra todo mundo hoje', 'live domingo e massa',
  'cade os vale tudo de hoje?', 'esse a e bilionarios do next', 'vamo encher o chat hoje tmj', 'complicado'];

/* ----- botoes de PUBLICO e modo viral + encerrar/voltar por teclado ----- */
$('mB1').onclick = function () { if (!LiveOn) return; LiveV += 1000; toast('\ud83d\udcc8 +1.000! ' + fmt(LiveV) + ' espectadores'); beep(true); };
$('mB5').onclick = function () { if (!LiveOn) return; LiveV += 5000; toast('\ud83d\udcc8 +5.000! ' + fmt(LiveV) + ' espectadores'); beep(true); };
$('mB10').onclick = function () { if (!LiveOn) return; LiveV += 10000; toast('\ud83d\ude80 +10.000! ' + fmt(LiveV) + ' espectadores'); beep(true); };
$('mViral').onclick = function () {
  ViralMode = !ViralMode;
  $('mViral').classList.toggle('on', ViralMode);
  toast(ViralMode ? '\ud83d\udd25 MODO VIRAL LIGADO \u2014 o algoritmo encontrou sua live!' : '\ud83d\udd15 Modo viral desligado');
};
document.addEventListener('keydown', function (e) {
  var tag = (e.target && e.target.tagName) || '';
  if (tag === 'INPUT' || tag === 'TEXTAREA') return;
  if (e.key === 'e' || e.key === 'E') encerrarLive();
  if (e.key === 'r' || e.key === 'R') voltarLive();
});

/* =====================================================================
   SISTEMA DE COMANDOS DE VOZ + CANAL 150K (perfil equal Twich) + APIs
   ===================================================================== */
var DESPEDIDA = ['gg man, foi top', 'vlw pela live familia', 'ate amanha familia', 'fui :(', 'live braba hoje rs',
  'vlw pelo stream', 'melhor live da semana', 'ate o proximo rs', '(: uma triste se deprara', 'gg, vou dormir'];

if (!CONF.seg) CONF.seg = 150000;
function segFmt(n) {
  n = parseInt(n, 10) || 0;
  if (n >= 1000) return Math.round(n / 1000) + ' mil';
  return '' + n;
}

function cmdNota(txt) { var mf = $('mFala'); if (mf) mf.textContent = '\ud83e\uddf2 ' + txt; }

/* reconhece COMANDOS no que foi falado; devolve true se reagiu */
function reacaoComando(t) {
  var l = ((t || '').toLowerCase() + ' ').replace(/[?!.,]/g, ' ');
  function floo(pal) {
    var alvo = (pal || '').trim().replace(/\s+/g, ' ');
    if (!alvo || alvo.length > 24) return false;
    if (/^(a|o|um|uma|pra|para|por)\s/.test(alvo)) alvo = alvo.replace(/^(a|o|um|uma|pra|para|por)\s+/, '');
    if (!alvo) return false;
    if (alvo.length <= 3) alvo = alvo.toUpperCase();
    ondaMsgs([alvo], 14);
    beep(true);
    cmdNota('COMANDO: flood de "' + alvo + '" no chat');
    return true;
  }
  /* 1) encerrar live */
  if (/encerrar|fechar|desligar|acabar a live|vou encerrar/.test(l)) {
    ondaMsgs(DESPEDIDA, 10);
    cmdNota('COMANDO: ENCERRAR a live \u2014 despedida do chat rodando');
    toast('\ud83d\udcf4 O chat se despedindo... live encerra em 4s (seu comando)');
    setTimeout(function () { encerrarLive(); }, 4500);
    return true;
  }
  /* 2) flood "digita X no chat familia" */
  var m = l.match(/(?:digita|mand|flod|coloca|escreve|faz)\s+(.+?)(?:\s+(?:no|na|em|pra|para)\s+chat|$)/);
  if (!m) m = l.match(/(?:digita|mand|flod|coloca|escreve|faz)\s+(.{1,24})/);
  if (m && floo(m[1])) return true;
  /* 3) temas rapidos */
  if (/(gata|mina|mulher|garota|linda|noiva)/.test(l)) { ondaMsgs(ELOG, 9); cmdNota('COMANDO: elogios \ud83d\ude0d'); return true; }
  if (/\bnext\b|passa pra outra/.test(l)) { ondaMsgs(['NEXT', 'NEXT!', 'maldito next', 'next kkkk', 'N.E.X.T'], 8); cmdNota('COMANDO: next spam'); return true; }
  if (/(30k|meta|mil espectadores|explodir)/.test(l)) { ondaMsgs(HYPE, 9); cmdNota('COMANDO: hype de meta'); return true; }
  if (/seguidor/.test(l)) {
    for (var i = 0; i < 6; i++) setTimeout(function () { pushMsg(pick(USERS) + ' seguiu o canal \ud83d\udc9c', 'sistema'); }, i * 700);
    ondaMsgs(HYPE, 6); cmdNota('COMANDO: seguidores caindo reais \ud83d\udc9c'); return true;
  }
  if (/(familia|galera|salve|ola|oi)/.test(l)) {
    ondaMsgs(['SALVE!!!', 'OI FAMILIA', 'kkkk oi', 'salve BR', 'COMPANHEIROS'], 10); cmdNota('COMANDO: salve geral'); return true;
  }
  if (/(obrigad|valeu|vlw)/.test(l)) { ondaMsgs(['\u2665', 'gente boa demais', 'que humildade', 'tamo junto \ud83d\udc9c'], 7); cmdNota('COMANDO: gratidao'); return true; }
  if (/(valorant|lol|counter|csgo|fortnite|roblox|jogo)/.test(l)) {
    ondaMsgs(['hoje tem?', 'QUERO', 'CHAMA', 'depois do ometv vem o jogo?', 'vamo'], 8); cmdNota('COMANDO: game talk'); return true;
  }
  if (/(ban|banir|time ?out|spame)/.test(l)) { ondaMsgs(['ban esse ai', 'mod chat chegando', 'a lei passou por aqui'], 6); cmdNota('COMANDO: mod jokes'); return true; }
  return false; /* nao bateu comando: IA genrica reage */
}

/* ---------- PERFIL / CANAL (pagina igual Twich) ---------- */
function abrirPerfi() {
  $('pfNome').innerHTML = CONF.nome + ' <span class="pf-check">\u2714</span>';
  $('pfSeguidores').textContent = segFmt(CONF.seg) + ' seguidores';
  $('pfSeg2').textContent = segFmt(CONF.seg);
  $('pfLive2').textContent = LiveOn ? fmt(LiveV) : '\u2014';
  $('pfLiveChip').style.display = LiveOn ? 'inline-flex' : 'none';
  $('pfCat2').textContent = CONF.cat;
  $('pfSobre').textContent = 'Radando a meta, conversa boa e zero tedio. Parodia feita por um genio local \ud83e\udee0';
  $('pfAvatar').src = elAvatar.src || elAvatar.style.backgroundImage.replace(/url\((.+)\)/, '$1').replace(/"/g, '');
  if (CONF.bannerImg) $('pfBanner').style.backgroundImage = 'url(' + CONF.bannerImg + ')';
  /* videos recentes (link real: API de imagem + api de avatar ja usadas) */
  var g = $('vodsGrid'); g.innerHTML = '';
  var t = ['Live de hoje INTEIRA', 'Ometv com o chat MALUCO', 'Raid da galera +GG'];
  var dur = ['2h 14m', '1h 03m', '0h 48m'];
  for (var i = 0; i < 3; i++) {
    var d = document.createElement('div');
    d.className = 'vod';
    var thumb = 'https://image.pollinations.ai/prompt/' + encodeURIComponent('streamer neon setup scene, gaming thumbnail, no text') +
      '?width=260&height=146&nologo=true&seed=' + (41 + i);
    d.innerHTML = '<div class="vod-thumb" style="background-image:url(\'' + thumb + '\')"><span class="vod-dur">' + dur[i] + '</span></div>' +
      '<b class="vod-t">' + t[i] + '</b><span class="vod-m">' + CONF.cat + ' \u00b7 ' + segFmt(CONF.seg / 40 + i * 900) + ' views</span>';
    g.appendChild(d);
  }
  $('perfilPag').classList.remove('oculto');
}
$('mPerfil').onclick = abrirPerfi;
document.querySelector('.avatar-wrap').onclick = abrirPerfi;
$('pfFecha').onclick = function () { $('perfilPag').classList.add('oculto'); };
$('pfSeguir').onclick = function () {
  var on = $('pfSeguir').classList.toggle('on');
  toast(on ? '\ud83d\udc9c Seguindo ' + CONF.nome + '!' : 'Parou de seguir (que tristeza)');
};
$('pfSub').onclick = function () { toast('\u2b50 Inscri\u00e7\u00e3o (par\u00f3dia) ativada! Obrigado familia'); };
$('mSeg').onchange = function () {
  CONF.seg = Math.max(0, parseInt(this.value, 10) || 0);
  salvarConf();
  toast('\ud83d\udc65 Seguidores: ' + segFmt(CONF.seg));
};
$('pfTrocaBanner').onclick = function () { $('pfBannerFile').click(); };
$('pfBannerFile').onchange = function () {
  var f = this.files && this.files[0]; if (!f) return;
  var fr = new FileReader();
  fr.onload = function () {
    var im = new Image();
    im.onload = function () {
      var c = document.createElement('canvas'); c.width = 800; c.height = 200;
      var cx = c.getContext('2d');
      var s = Math.max(800 / im.width, 200 / im.height);
      cx.drawImage(im, (800 - im.width * s) / 2, (200 - im.height * s) / 2, im.width * s, im.height * s);
      CONF.bannerImg = c.toDataURL('image/jpeg', 0.86);
      salvarConf();
      $('pfBanner').style.backgroundImage = 'url(' + CONF.bannerImg + ')';
      toast('\u2705 Banner trocado pelo seu arquivo!');
    };
    im.src = fr.result;
  };
  fr.readAsDataURL(f);
};
$('pfBannerIA').onclick = function () {
  var u = 'https://image.pollinations.ai/prompt/' + encodeURIComponent('dark purple neon gradient abstract wide banner, smoke, no text') +
    '?width=800&height=200&nologo=true&seed=' + (1 + rnd(99999));
  CONF.bannerImg = u; salvarConf();
  $('pfBanner').style.backgroundImage = 'url(' + u + ')';
  toast('\u2728 Banner novo gerado pela IA (API de imagem em ao vivo)');
};
$('mMeta').value = MetaV;
$('mRitmo').value = Ritmo;
$('mCresce').checked = CrescerAuto;
$('mLive').textContent = fmt(LiveV);
$('mMeta').onchange = function () {
  MetaV = Math.max(1000, parseInt(this.value, 10) || 30000);
  CONF.meta = MetaV; salvarConf();
  toast('\ud83c\udfaf Nova meta: ' + fmt(MetaV));
};
$('mRitmo').onchange = function () {
  Ritmo = Math.min(20, Math.max(1, parseInt(this.value, 10) || 3));
  CONF.ritmo = Ritmo; salvarConf();
  toast('\ud83d\udcc8 Ritmo x' + Ritmo);
};
$('mCresce').onchange = function () {
  CrescerAuto = this.checked;
  CONF.crescer = CrescerAuto; salvarConf();
  toast(CrescerAuto ? '\ud83d\udcc8 Crescimento automatico LIGADO' : '\u23f8\ufe0f Crescimento automatico pausado');
};
$('mImp').onclick = function () {
  LiveV += 2000;
  toast('\ud83d\ude80 Impulso! ' + fmt(LiveV) + ' espectadores agora');
  beep(true);
};
