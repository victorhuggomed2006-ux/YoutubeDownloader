# Security Policy

*[Versão em português abaixo](#política-de-segurança)*

## Supported versions

Only the latest release receives security fixes. If you are running an older
build, update before reporting.

## Reporting a vulnerability

**Do not open a public issue for security problems.**

Use GitHub's private reporting instead:
[Security → Report a vulnerability](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/security/advisories/new).

Please include:

- what an attacker can achieve, not just what looks wrong
- the steps to reproduce it
- the version shown in the About window
- the relevant part of `%APPDATA%\YouTubeDownloader\ytdownloader.log`

You can expect a first reply within a week. Fixes ship in the next release, or
sooner when the impact justifies it.

## Where the risk actually lives

If you are auditing this project, these are the parts worth your attention:

**`core/updater.py`** — downloads a package from PyPI, extracts it and puts it
on `sys.path`, where the code will be imported and executed. It is the only
component that runs code fetched at runtime. Its defences are the SHA-256 check
against the digest published by PyPI, refusal of archive members whose path
escapes the destination directory (Zip Slip), a size ceiling, and refusal of
any package that does not contain `yt_dlp`. All four are covered by tests in
`tests/test_updater.py`.

**`core/urls.py`** — the only input the user pastes in. It accepts `http` and
`https` exclusively; `file://`, `javascript:` and `data:` are rejected before
anything else touches them.

**Bundled binaries** — FFmpeg comes from the official builds published at
`gyan.dev`, downloaded by `packaging/fetch_ffmpeg.ps1`. yt-dlp comes from PyPI.
Neither is vendored into this repository, so what ships is whatever those
sources publish at build time.

**What this application never does** — it does not open network ports, does not
send telemetry, and does not communicate with any server other than PyPI (to
check for engine updates) and whatever site you asked it to download from.

## Cookie import

The browser cookie feature reads your browser's cookie database through yt-dlp
to authenticate downloads. Those cookies stay on your machine and are used only
for the requests to the site you are downloading from. They are never written
to the application's own files. If this makes you uncomfortable, leave the
setting on "Do not use" — it is the default.

---

# Política de segurança

## Versões suportadas

Apenas a versão mais recente recebe correções de segurança. Se estiver rodando
uma versão antiga, atualize antes de reportar.

## Como reportar uma vulnerabilidade

**Não abra uma issue pública para problemas de segurança.**

Use o canal privado do GitHub:
[Security → Report a vulnerability](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/security/advisories/new).

Inclua:

- o que um atacante consegue fazer, não apenas o que parece errado
- os passos para reproduzir
- a versão mostrada na janela Sobre
- o trecho relevante de `%APPDATA%\YouTubeDownloader\ytdownloader.log`

A primeira resposta costuma sair em até uma semana. As correções entram na
versão seguinte, ou antes quando o impacto justificar.

## Onde o risco realmente está

Se você for auditar este projeto, é para estas partes que vale olhar:

**`core/updater.py`** — baixa um pacote do PyPI, extrai e coloca no `sys.path`,
de onde o código será importado e executado. É o único componente que roda
código obtido em tempo de execução. Suas defesas são a verificação SHA-256
contra o resumo publicado pelo PyPI, a recusa de arquivos cujo caminho escape
da pasta de destino (Zip Slip), um limite de tamanho e a recusa de qualquer
pacote que não contenha `yt_dlp`. As quatro têm teste em
`tests/test_updater.py`.

**`core/urls.py`** — a única entrada que o usuário digita. Aceita apenas `http`
e `https`; `file://`, `javascript:` e `data:` são recusados antes de chegarem a
qualquer outro lugar.

**Binários incluídos** — o FFmpeg vem das builds oficiais publicadas em
`gyan.dev`, baixadas por `packaging/fetch_ffmpeg.ps1`. O yt-dlp vem do PyPI.
Nenhum dos dois está versionado neste repositório, então o que é distribuído é
o que essas fontes publicam no momento da compilação.

**O que este aplicativo nunca faz** — não abre portas de rede, não envia
telemetria e não se comunica com nenhum servidor além do PyPI (para verificar
atualizações do motor) e do site de onde você pediu o download.

## Importação de cookies

O recurso de cookies lê o banco de cookies do seu navegador, através do yt-dlp,
para autenticar downloads. Esses cookies permanecem na sua máquina e são usados
apenas nas requisições ao site de onde você está baixando. Nunca são gravados
nos arquivos do próprio aplicativo. Se isso lhe incomoda, deixe a opção em
"Não usar" — é o padrão.
