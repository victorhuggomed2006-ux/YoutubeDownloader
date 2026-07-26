<div align="center">

# YouTube Downloader — technical documentation

[Installing](docs/INSTALLING.md) · [Architecture](docs/ARCHITECTURE.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · **[Português](README.pt-BR.md)**

![Main window](docs/screenshot-dark.png)

</div>

---

A Windows desktop application built with PySide6. The installer bundles FFmpeg
and the download engine, so the end user needs no Python and no other
dependency.

For installation instructions, see the [project home page](../README.md).

## Features

Video in **MP4, MKV or WebM**, from 360p to 4K, with the audio already merged.
Audio in **MP3, M4A, Opus, WAV or FLAC**, from 128 to 320 kbps.

Paste a link and the app shows the thumbnail, title, channel and duration
before you commit. The queue takes several downloads at once, with real
progress, speed, time remaining and cancellation. Playlists can be queued in
one go.

The finished file carries cover art and metadata, and subtitles when asked for.
There is a download history, light and dark themes, and the interface speaks
English, Portuguese and Spanish.

**Not limited to YouTube.** Any `http`/`https` address is handed to yt-dlp,
which supports [over a thousand sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).
YouTube keeps a dedicated code path because it is the common case and lets the
preview appear before the network is even touched.

## Building

```powershell
git clone https://github.com/victorhuggomed2006-ux/YoutubeDownloader
cd YoutubeDownloader/source-code
powershell -ExecutionPolicy Bypass -File packaging\build.ps1
```

That single command creates the virtual environment, installs dependencies,
downloads FFmpeg, generates icons, compiles translations, runs the tests,
builds the executable with PyInstaller and packages the installer. Output lands
in `dist/`.

Flags: `-SkipTests`, `-SkipMsi` (executable only), `-Clean`.

**Requirements:** Python 3.10+, .NET SDK 6+, and WiX 5:

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

$env:PYTHONPATH = "."
python -m ytdownloader
```

```powershell
pytest                    # tests
ruff check .              # linter
ruff format .             # formatter
```

### Layout

```
ytdownloader/
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
docs/                  architecture, installing, code signing
```

`core` imports nothing from Qt. That is not purism: it is what lets the test
suite run without opening a window, and what would let the download logic be
reused behind a different interface. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the module-by-module rundown.

### Translations

The source strings are written in English and act as the translation keys.
Portuguese and Spanish live in `ytdownloader/resources/i18n`.

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_translations.ps1
```

That extracts new strings into the `.ts` files and compiles the `.qm` files the
app loads at runtime. Adding a language is described in
[CONTRIBUTING.md](CONTRIBUTING.md#adding-a-language).

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

**The installer is not code-signed.** SmartScreen shows "Unknown publisher"
until it is. See [docs/CODE-SIGNING.md](docs/CODE-SIGNING.md).

## Licence and credits

Built by **Victor Medeiros** — IT Analyst, Developer, AI Engineer.

Copyright © 2026 Victor Medeiros. [MIT licensed](LICENSE).

| Project | Role | Licence |
|---|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Extraction and download | Unlicense |
| [Qt / PySide6](https://www.qt.io/qt-for-python) | Graphical interface | LGPL v3 |
| [FFmpeg](https://ffmpeg.org) | Conversion and stream merging | LGPL v2.1+ |

## Responsible use

Download only what you have the right to keep: your own material, public domain
works, openly licensed content, or media you have permission to save. Respect
each site's terms of service and the copyright law that applies to you.
