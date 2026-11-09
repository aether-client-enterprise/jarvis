# Twich Fake 🟣 (paródia para troçar os amigos)

Plataforma estilo streaming AO VIVO — **não é real**: chat vivo aleatório, 15k+ espectadores,
raids, badges, doações, ecos do jogo e a imagem ao vivo — tudo simulado.

## Como rodar
1. Dá dois cliques em `index.html` (Chrome/Edge).
2. **Modo cinema (mais convincente):** copie o endereço do arquivo e rode no Terminal:

   ```powershell
   chrome --kiosk "file:///C:/Users/joilton/Downloads/Jarvis/Projetos/twitchfake_08112026-1826/index.html"
   ```

   (com a URL: sem barra de endereço nem abas — parece o app real)

## Painel do Mestre
Aperte **P** em cima da página:
- Nome do streamer, título, categoria
- Base dos espectadores (ex.: 15.000)
- Velocidade do chat (1 tranquilo → 12 guerra)
- Botão **🚀 Raid agora** pra invadir com milhares de "espectadores"

Aperte **B** pra revelar a treta (banner de "PARÓDIA") — é moral sempre revelar pra todo mundo rir junto 😄

Você pode digitar no chat e, inclusive, receber respostas.

### O chat REAGE à sua live (Ometv)
- **Tecla P** (Painel do Mestre): escreva em "🎯 O que está acontecendo" e clique **🧠 Chat reage (IA)** — a IA gera mensagens na hora reagindo ao momento (elogios, perguntas, zoação, hype), como se estivessem vendo sua tela.
- Ou aperte direto: **1** = 😍 elogios · **2** = ❓ perguntas · **3** = 🤪 zoar · **4** = 🔥 hype.
- Sozinho, o chat já comenta sozinho a cada poucos segundos ("de onde vc é?", "vc tá com alguém aí rs").
- Interface imitando a Twitch de verdade: ícones do topo (Prime 👑, sussurros, notificações, bits), botões Presentear/Compartilhar/Mais, barra do player (volume, 1080p60, ⚙️, modo teatro, tela cheia), **Pontos do canal** (+50 pts), mensagem fixada no chat, **Hype Train**, grid de emotes (Kappa, LUL, Pog, monkaS...) e lista de espectadores.

## Mostrar a SUA TELA de verdade no player (Ometv 🔥)
1. Abra o **Ometv num Chrome separado** (janela ou aba própria).
2. Abra este `index.html` em **janela NORMAL do Chrome** com **F11** (fullscreen) — **evite** `--kiosk`: o seletor de tela do navegador não abre em modo kiosk.
3. Clique em **🖥️ Compartilhar tela** (no canto do player).
4. No seletor do navegador, escolha a **aba/janela do Ometv** → ela aparece como a "transmissão" ao vivo, com o chat rodando em cima. O gameplay fake de canvas some enquanto compartilha.

Dica: para parecer ainda mais real, rode por localhost:
`python -m http.server 8080 --directory "C:\Users\joilton\Downloads\Jarvis\Projetos\twitchfake_08112026-1826"` e abra `http://localhost:8080`.

---
Projeto criado pelo Jarvis ✦. Sinta seu chat movendo, sons de doação e raids caindo de vez em vez.
