<div align="center">

# YouTube Downloader

**Aplicativo desktop para Windows que baixa vídeos e áudios do YouTube e de mais de mil outros sites.**

[![CI](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/actions/workflows/ci.yml/badge.svg)](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/actions/workflows/ci.yml)
[![Versão](https://img.shields.io/github/v/release/victorhuggomed2006-ux/YoutubeDownloader)](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/releases/latest)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)

[Baixar](#baixar) · [Recursos](#recursos) · [Compilar](#compilando-o-projeto) · [Contribuir](CONTRIBUTING.md) · **[English](README.md)**

![Janela principal](docs/captura-tela-escuro.png)

</div>

---

Sem navegador, sem linha de comando, sem Python para instalar. O instalador traz
o FFmpeg e o motor de download embutidos, então funciona no primeiro clique.

Por Victor Medeiros. Licença MIT.

## Baixar

**[⬇️ Baixar a versão mais recente](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/releases/latest)**

Pegue o `YouTubeDownloader-1.2.0-Setup.msi`, dê dois cliques e escolha se quer o
atalho na Área de Trabalho. É isso — o passo a passo detalhado está em
[`source-code/docs/`](programa).

**Não pede administrador.** O programa é instalado em
`%LOCALAPPDATA%\Programs\YouTube Downloader`, a pasta que o Windows reserva para
programas de um único usuário — o mesmo lugar que Chrome, Discord e Spotify
usam. Não é `C:\Program Files` por um motivo concreto: gravar ali exige
elevação, sem exceção. Um instalador que não pede nada é, necessariamente, um
que não escreve em Arquivos de Programas.

**Requisitos:** Windows 10 ou 11 de 64 bits. Cerca de 300 MB de espaço em disco.

> **Sobre o aviso do SmartScreen:** o instalador ainda não é assinado, então o
> Windows mostra *"Editor desconhecido"*. Clique em **Mais informações →
> Executar assim mesmo**. A assinatura está planejada — veja
> [docs/ASSINATURA.md](docs/ASSINATURA.md) para a situação e o raciocínio.

Instalação silenciosa, para quem precisa:

```powershell
msiexec /i YouTubeDownloader-1.2.0-Setup.msi /qn
```

O instalador mantém a extensão `.msi` de propósito. Renomeá-lo para `setup.exe`
o quebraria: o Windows carrega arquivos `.exe` como executáveis PE, e um MSI não
é um — é a extensão que faz o arquivo ser entregue ao `msiexec`.

## Recursos

Vídeo em **MP4, MKV ou WebM**, de 360p a 4K, com o áudio já mesclado. Áudio em
**MP3, M4A, Opus, WAV ou FLAC**, de 128 a 320 kbps.

Cole um link e o aplicativo mostra a miniatura, o título, o canal e a duração
antes de você se comprometer com qualquer coisa. A fila aceita vários downloads
ao mesmo tempo, com progresso real, velocidade, tempo restante e cancelamento.
Playlists entram na fila de uma vez.

O arquivo final leva capa e metadados, e legendas quando você pedir. Há
histórico dos downloads anteriores, temas claro e escuro, e a interface fala
português e inglês.

**Não se limita ao YouTube.** Qualquer endereço `http`/`https` é repassado ao
yt-dlp, que suporta [mais de mil sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
— Vimeo, Twitch, SoundCloud, Reddit, Bandcamp e por aí vai. O YouTube mantém um
caminho dedicado no código porque é o caso comum e permite que a prévia apareça
antes mesmo de tocar na rede.

### Vídeos que exigem conta conectada

Vídeos com restrição de idade, conteúdo exclusivo para membros e o pedido de
*"confirme que você não é um robô"* precisam de uma sessão autenticada. Em
**Configurações → Usar cookies do navegador**, escolha o navegador em que você
já está logado e **feche esse navegador** antes de baixar — enquanto ele estiver
aberto, mantém o arquivo de cookies travado.

## O que mantém tudo funcionando

Os sites mudam a forma de servir vídeo o tempo todo, e quem acompanha isso é o
**yt-dlp**. Uma cópia congelada dentro do executável envelhece rápido: em poucos
meses, parte dos vídeos deixaria de baixar.

Por isso o aplicativo verifica ao abrir se há uma versão mais nova do yt-dlp e
oferece atualizá-la. O pacote vem do PyPI, é conferido contra o resumo SHA-256
publicado lá e é extraído na sua pasta de usuário — o programa instalado não é
tocado, e a atualização não exige privilégio de administrador.

Se um vídeo específico parar de baixar, atualizar o motor é a primeira coisa a
tentar.

## Compilando o projeto

```powershell
git clone https://github.com/victorhuggomed2006-ux/YoutubeDownloader
cd YoutubeDownloader
powershell -ExecutionPolicy Bypass -File packaging\build.ps1
```

Esse comando único cria o ambiente virtual, instala as dependências, baixa o
FFmpeg, gera os ícones, compila as traduções, roda os testes, compila o
executável com o PyInstaller e empacota o instalador. A saída vai para `dist/`.

Parâmetros: `-SkipTests`, `-SkipMsi` (só o executável), `-Clean`.

**Requisitos de compilação:** Python 3.10+, .NET SDK 6+ e o WiX 5:

```powershell
dotnet tool install --global wix --version 5.0.2
wix extension add -g WixToolset.UI.wixext/5.0.2
```

> O WiX 7 exige aceitar a EULA do Open Source Maintenance Fee. A versão 5 é
> livre e faz o mesmo trabalho aqui.

## Desenvolvimento

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt

powershell -ExecutionPolicy Bypass -File packaging\fetch_ffmpeg.ps1
python packaging\make_icon.py
powershell -ExecutionPolicy Bypass -File packaging\build_translations.ps1

cd source-code
python -m ytdownloader
```

```powershell
pytest                    # testes
ruff check .              # linter
ruff format .             # formatador
```

### Organização

```
source-code/docs/             onde baixar o instalador
source-code/ytdownloader/
├── core/              regras de negócio — não importa nada do Qt
│   ├── downloader.py    a camada sobre o yt-dlp
│   ├── formats.py       qualidades e seletores de formato
│   ├── urls.py          validação e normalização de endereços
│   ├── errors.py        erros do yt-dlp traduzidos para linguagem clara
│   ├── ffmpeg.py        localização do FFmpeg embutido
│   ├── jsruntime.py     detecção do runtime JavaScript
│   ├── settings.py      preferências (%APPDATA%)
│   ├── history.py       histórico de downloads
│   ├── updater.py       atualização do yt-dlp
│   ├── models.py        estruturas de dados compartilhadas
│   └── paths.py         diretórios do aplicativo
├── gui/               interface em PySide6
│   ├── main_window.py
│   ├── workers.py       trabalho mantido fora da thread da interface
│   ├── i18n.py          tradução
│   ├── theme.py         temas claro e escuro
│   ├── widgets/
│   └── dialogs/
└── app.py             inicialização

packaging/             PyInstaller, WiX, ícones, FFmpeg, traduções
tests/                 testes do núcleo
```

`core` não importa nada do Qt. Isso não é purismo: é o que permite rodar a suíte
de testes sem abrir janela, e o que permitiria reaproveitar a lógica de download
atrás de outra interface.

Trabalho demorado nunca toca a thread da interface — passa todo pelos workers em
`gui/workers.py`, que devolvem resultado por sinais do Qt.

### Onde ficam os dados do usuário

Em `%APPDATA%\YouTubeDownloader`: `settings.json`, `history.json`,
`ytdownloader.log` e `runtime/` (versões atualizadas do yt-dlp). Desinstalar não
apaga essa pasta.

O log é o primeiro lugar a olhar quando alguém reporta um problema: ele registra
a versão do yt-dlp em uso, onde o FFmpeg foi encontrado e qual runtime
JavaScript está ativo.

## Limitações conhecidas

**Menos opções de qualidade em alguns vídeos.** O yt-dlp precisa de um
interpretador JavaScript para resolver certos formatos. O aplicativo detecta
Node, Deno ou Bun se estiverem instalados e os usa automaticamente. Sem nenhum
deles ainda funciona, mas alguns vídeos oferecem menos resoluções. Embutir um
runtime acrescentaria mais de 100 MB ao instalador, o que não pareceu uma troca
justa para um caso que atinge poucos vídeos.

**Alarme falso de antivírus.** Executáveis do PyInstaller às vezes disparam
heurísticas. O código é aberto e o `build.ps1` reproduz o binário.

**Arquivos MP4 maiores do que você esperaria.** O download prioriza H.264/AAC. O
YouTube oferece AV1 na mesma resolução com arquivo bem menor, mas AV1 não toca
em aparelhos e TVs mais antigos. Escolha MKV ou WebM se quiser o arquivo menor.

## Licença e créditos

Feito por **Victor Medeiros** — Analista de TI, Desenvolvedor, Engenheiro de IA.

Copyright © 2026 Victor Medeiros. [Licença MIT](LICENSE).

Construído sobre:

| Projeto | Papel | Licença |
|---|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Extração e download | Unlicense |
| [Qt / PySide6](https://www.qt.io/qt-for-python) | Interface gráfica | LGPL v3 |
| [FFmpeg](https://ffmpeg.org) | Conversão e junção das faixas | LGPL v2.1+ |

## Uso responsável

Baixe apenas o que você tem direito de guardar: material próprio, obras em
domínio público, conteúdo sob licença aberta ou mídia que você tem permissão
para salvar. Respeite os termos de serviço de cada site e a legislação de
direitos autorais que se aplica a você. O que você faz com esta ferramenta é
responsabilidade sua.
