<div align="center">

# YouTube Downloader

**A desktop app for Windows that downloads video and audio from YouTube and a thousand other sites.**

[![CI](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/actions/workflows/ci.yml/badge.svg)](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/victorhuggomed2006-ux/YoutubeDownloader)](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)

[Download](#download) · [Features](#features) · [Building](#building-from-source) · [Contributing](CONTRIBUTING.md) · **[Português](README.pt-BR.md)**

![Main window](docs/captura-tela-escuro.png)

</div>

---

No browser, no command line, no Python to install. The installer bundles FFmpeg
and the download engine, so it works on the first double-click.

By Victor Medeiros. MIT licensed.

## Download

**[⬇️ Download the latest release](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/releases/latest)**

Grab `YouTubeDownloader-1.2.0-Setup.msi`, double-click it, and choose whether
you want a Desktop shortcut. That is the whole process — see
[`programa/`](programa) for the step-by-step.

**No administrator prompt.** The app installs into
`%LOCALAPPDATA%\Programs\YouTube Downloader`, the folder Windows reserves for
single-user programs — the same place Chrome, Discord and Spotify use. It is not
`C:\Program Files` for a concrete reason: writing there requires elevation, with
no exceptions. An installer that asks for nothing is, necessarily, one that does
not write to Program Files.

**Requirements:** Windows 10 or 11, 64-bit. Around 300 MB of disk space.

> **On the SmartScreen warning:** the installer is not yet code-signed, so
> Windows shows *"Unknown publisher"*. Click **More info → Run anyway**. Signing
> is planned — see [docs/ASSINATURA.md](docs/ASSINATURA.md) for the status and
> the reasoning.

Silent installation, for those who need it:

```powershell
msiexec /i YouTubeDownloader-1.2.0-Setup.msi /qn
```

The installer keeps the `.msi` extension on purpose. Renaming it to `setup.exe`
would break it: Windows loads `.exe` files as PE executables, and an MSI is not
one — the extension is what routes the file to `msiexec`.

## Features

Video in **MP4, MKV or WebM**, from 360p to 4K, with audio already merged.
Audio in **MP3, M4A, Opus, WAV or FLAC**, from 128 to 320 kbps.

Paste a link and the app shows the thumbnail, title, channel and duration before
you commit to anything. The queue takes several downloads at once, with real
progress, speed, time remaining and cancellation. Playlists can be queued in one
go.

The finished file carries cover art and metadata, and subtitles when you ask for
them. There is a history of past downloads, light and dark themes, and the
interface speaks English and Portuguese.

**It is not limited to YouTube.** Any `http`/`https` address is handed to
yt-dlp, which supports [over a thousand sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
— Vimeo, Twitch, SoundCloud, Reddit, Bandcamp and so on. YouTube keeps a
dedicated code path because it is the common case and allows the preview to
appear before the network is even touched.

### Videos that require a signed-in account

Age-restricted videos, members-only content and the *"confirm you're not a bot"*
prompt all need an authenticated session. In **Settings → Use cookies from
browser**, pick the browser where you are already signed in, then **close that
browser** before downloading — it holds a lock on the cookie file while running.

## Keeping it working

Sites change how they serve video all the time, and the component that keeps up
is **yt-dlp**. A copy frozen inside the executable ages fast: within months,
some videos would stop downloading.

So the app checks for a newer yt-dlp on startup and offers to update it. The
package comes from PyPI, is verified against the SHA-256 digest published there,
and is extracted into your user folder — the installed program is never touched,
and the update needs no administrator rights.

If one particular video stops downloading, updating the engine is the first
thing to try.

## Building from source

```powershell
git clone https://github.com/victorhuggomed2006-ux/YoutubeDownloader
cd YoutubeDownloader
powershell -ExecutionPolicy Bypass -File packaging\build.ps1
```

That single command creates the virtual environment, installs dependencies,
downloads FFmpeg, generates icons, compiles translations, runs the tests, builds
the executable with PyInstaller and packages the installer. Output lands in
`dist/`.

Flags: `-SkipTests`, `-SkipMsi` (executable only), `-Clean`.

**Build requirements:** Python 3.10+, .NET SDK 6+, and WiX 5:

```powershell
dotnet tool install --global wix --version 5.0.2
wix extension add -g WixToolset.UI.wixext/5.0.2
```

> WiX 7 requires accepting the Open Source Maintenance Fee EULA. Version 5 is
> free and does the same job here.

## Development

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt

powershell -ExecutionPolicy Bypass -File packaging\fetch_ffmpeg.ps1
python packaging\make_icon.py
powershell -ExecutionPolicy Bypass -File packaging\build_translations.ps1

$env:PYTHONPATH = "codigo-fonte"
python -m ytdownloader
```

```powershell
pytest                    # tests
ruff check .              # linter
ruff format .             # formatter
```

### Layout

```
programa/             where to download the installer
codigo-fonte/ytdownloader/
├── core/              business rules — imports nothing from Qt
│   ├── downloader.py    the layer over yt-dlp
│   ├── formats.py       qualities and format selectors
│   ├── urls.py          address validation and normalisation
│   ├── errors.py        yt-dlp errors turned into plain language
│   ├── ffmpeg.py        locating the bundled FFmpeg
│   ├── jsruntime.py     JavaScript runtime detection
│   ├── settings.py      preferences (%APPDATA%)
│   ├── history.py       download history
│   ├── updater.py       yt-dlp self-update
│   ├── models.py        shared data structures
│   └── paths.py         application directories
├── gui/               PySide6 interface
│   ├── main_window.py
│   ├── workers.py       work kept off the UI thread
│   ├── i18n.py          translation
│   ├── theme.py         light and dark themes
│   ├── widgets/
│   └── dialogs/
└── app.py             startup

packaging/             PyInstaller, WiX, icons, FFmpeg, translations
tests/                 core test suite
```

`core` imports nothing from Qt. That is not purism: it is what lets the test
suite run without opening a window, and what would let the download logic be
reused behind a different interface.

Long-running work never touches the UI thread — it all goes through the workers
in `gui/workers.py`, which report back through Qt signals.

### Where user data lives

In `%APPDATA%\YouTubeDownloader`: `settings.json`, `history.json`,
`ytdownloader.log` and `runtime/` (updated yt-dlp versions). Uninstalling does
not remove this folder.

The log is the first place to look when someone reports a problem: it records
the yt-dlp version in use, where FFmpeg was found and which JavaScript runtime
is active.

## Known limitations

**Fewer quality options on some videos.** yt-dlp needs a JavaScript interpreter
to resolve certain formats. The app detects Node, Deno or Bun if installed and
uses them automatically. Without any of them it still works, but some videos
offer fewer resolutions. Bundling a runtime would add over 100 MB to the
installer, which did not seem a fair trade for a case that affects few videos.

**Antivirus false positives.** PyInstaller executables sometimes trip
heuristics. The source is open and `build.ps1` reproduces the binary.

**MP4 files are larger than you might expect.** Downloads prefer H.264/AAC.
YouTube offers AV1 at the same resolution with a noticeably smaller file, but
AV1 does not play on older devices and TVs. Choose MKV or WebM if you want the
smaller file.

## Licence and credits

Built by **Victor Medeiros** — IT Analyst, Developer, AI Engineer.

Copyright © 2026 Victor Medeiros. [MIT licensed](LICENSE).

Built on:

| Project | Role | Licence |
|---|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Extraction and download | Unlicense |
| [Qt / PySide6](https://www.qt.io/qt-for-python) | Graphical interface | LGPL v3 |
| [FFmpeg](https://ffmpeg.org) | Conversion and stream merging | LGPL v2.1+ |

## Responsible use

Download only what you have the right to keep: your own material, public domain
works, openly licensed content, or media you have permission to save. Respect
each site's terms of service and the copyright law that applies to you. What you
do with this tool is on you.
