# Jarvis — Assistente Local com Acesso Total ao PC

Assistente que roda inteiramente na sua máquina, com acesso irrestrito ao sistema de arquivos, execução de comandos, reconhecimento de voz, criação de sites/aplicativos/jogos em HTML e envio de mensagens em redes sociais.

## Funcionalidades
- **Wake word**: diga ou escreva `ok jarvis` (ou `hey jarvis`, `jarvis`) seguido do comando.
- **Idioma automático**: detecta se você fala português ou inglês e responde no mesmo idioma.
- **Abrir sites/redes sociais**: youtube, instagram, whatsapp, facebook, google, github e qualquer URL.
- **Instagram/WhatsApp com contato**: `abrir instagram na conversa do João` — abre direto buscando a pessoa.
- **Criar site/app/jogo HTML**: gera um arquivo `.html` completo e abre no navegador.
- **Ler/escrever arquivos**: acesso total a qualquer pasta do seu PC (exige Administrador).
- **Listar pastas e buscar arquivos**: navegue por diretórios e procure por nome.
- **Executar comandos**: roda qualquer comando do terminal/CMD/PowerShell.
- **Interface web**: rode localmente e use pelo navegador em `http://127.0.0.1:8765`.
- **Controle por voz**: clique no microfone e fale comandos.

## Pré-requisitos
- Windows 10 ou 11
- Python 3.10+
- Microfone (para uso por voz)

## Instalação
Baixe ou clone este repositório e instale as dependências:

```bash
pip install fastapi uvicorn speech_recognition pyttsx3 pyaudio
```

> Se `pyaudio` der erro, baixe o `.whl` compatível com sua versão do Python em: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

## Como rodar (obrigatório: como Administrador)
Clique com o botão direito no PowerShell ou CMD e escolha **Executar como Administrador**, então:

```bash
cd jarvis
python main.py
```

Abra o navegador em: `http://127.0.0.1:8765`

## Exemplos de comandos
| Comando | O que faz |
|---------|-----------|
| `ok jarvis, abra o youtube` | Abre o YouTube no navegador |
| `ok jarvis, criar site sobre viagens` | Cria um site HTML e abre |
| `ok jarvis, criar jogo de plataforma` | Cria um joguinho em HTML5 Canvas e abre |
| `ok jarvis, ler arquivo C:\Users\SeuNome\notas.txt` | Exibe o conteúdo do arquivo |
| `ok jarvis, abrir pasta C:\Downloads` | Lista os arquivos da pasta |
| `ok jarvis, executar dir` | Roda o comando dir no terminal |
| `ok jarvis, escrever arquivo C:\ola.txt conteudo Olá Jarvis!` | Cria/atualiza um arquivo de texto |
| `ok jarvis, instagram na conversa do Maria` | Abre o Instagram Direct buscando Maria |
| `ok jarvis, info do sistema` | Mostra dados do PC |

## Segurança
- Roda apenas em `127.0.0.1` (localhost), não expõe portas para a rede externa.
- Exige privilégios de **Administrador** para ler/escrever em qualquer lugar do PC e executar comandos.
- Você é o administrador desta máquina — use com responsabilidade.

## Hospedar no GitHub (opcional)
Este projeto é um backend Python, não um site estático. Não roda diretamente no GitHub Pages. Para hospedar:
1. Crie um repositório no GitHub.
2. Faça upload dos arquivos da pasta `jarvis/`.
3. Rode em um servidor com Python (VPS, Raspberry PC, seu próprio computador deixado ligado), ou use serviços como Railway, Render ou PythonAnywhere para expor a API.
4. Para acesso externo ao seu PC local, use ngrok ou similar (por sua conta e risco).
