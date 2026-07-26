# Changelog

Notable changes to this project, following the spirit of
[Semantic Versioning](https://semver.org).

*As entradas estão em inglês e português.*

---

## [1.2.0] — 2026-07-26

First public release.

### The application

- Native Windows desktop app built with PySide6
- Video in MP4, MKV or WebM, from 360p to 4K, with audio already merged
- Audio in MP3, M4A, Opus, WAV or FLAC, from 128 to 320 kbps
- Preview with thumbnail, title, channel and duration before downloading
- Download queue with real progress, speed, time remaining and cancellation
- Playlist support
- Cover art, metadata and optional subtitles embedded into the file
- Download history
- Light and dark themes
- Interface in Portuguese and English, following the Windows language
- Works with YouTube and over a thousand other sites supported by yt-dlp

### Installation

- Single MSI installer, per-user, with no administrator prompt
- Optional Desktop shortcut, chosen during setup
- FFmpeg and the download engine bundled — no other dependency to install

### Under the hood

- Business rules isolated from the interface: `core/` imports nothing from Qt,
  which lets the test suite run without opening a window
- Download engine (yt-dlp) updates itself from PyPI, verified by SHA-256, into
  the user folder — no reinstall and no administrator rights needed
- yt-dlp errors translated into plain language instead of raw output
- MP4 downloads prefer H.264/AAC over AV1, trading file size for playback
  compatibility with older devices and TVs
- 142 tests covering the core, with the update mechanism's security defences
  under explicit test
- Continuous integration on every push; installers built and published
  automatically from a version tag

---

*Primeira versão pública.*

### O aplicativo

- Aplicativo Windows nativo em PySide6
- Vídeo em MP4, MKV ou WebM, de 360p a 4K, com o áudio já mesclado
- Áudio em MP3, M4A, Opus, WAV ou FLAC, de 128 a 320 kbps
- Prévia com miniatura, título, canal e duração antes de baixar
- Fila com progresso real, velocidade, tempo restante e cancelamento
- Suporte a playlists
- Capa, metadados e legendas opcionais gravados no arquivo
- Histórico de downloads
- Temas claro e escuro
- Interface em português e inglês, seguindo o idioma do Windows
- Funciona com o YouTube e mais de mil outros sites suportados pelo yt-dlp

### Instalação

- Instalador MSI único, por usuário, sem pedir administrador
- Atalho na Área de Trabalho opcional, escolhido durante a instalação
- FFmpeg e motor de download embutidos — nenhuma outra dependência

### Por dentro

- Regras de negócio isoladas da interface: `core/` não importa nada do Qt, o que
  permite rodar a suíte de testes sem abrir janela
- O motor de download (yt-dlp) se atualiza a partir do PyPI, com verificação
  SHA-256, na pasta do usuário — sem reinstalar nada e sem privilégio de
  administrador
- Erros do yt-dlp traduzidos para linguagem clara em vez da saída crua
- Downloads em MP4 preferem H.264/AAC a AV1, trocando tamanho de arquivo por
  compatibilidade com aparelhos e TVs mais antigos
- 142 testes cobrindo o núcleo, com as defesas de segurança do mecanismo de
  atualização sob teste explícito
- Integração contínua a cada push; instaladores compilados e publicados
  automaticamente a partir de uma tag de versão

[1.2.0]: https://github.com/victorhuggomed2006-ux/YoutubeDownloader/releases/tag/v1.2.0
