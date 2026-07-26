<div align="center">

# YouTube Downloader

**Download video and audio from YouTube and a thousand other sites.**

[![CI](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/actions/workflows/ci.yml/badge.svg)](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/victorhuggomed2006-ux/YoutubeDownloader)](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](source-code/LICENSE)

### [⬇️ Download the installer](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/raw/main/YouTubeDownloader-1.3.0-Setup.msi)

*96 MB · Windows 10 or 11, 64-bit · the download starts immediately*

![Main window](source-code/docs/screenshot-dark.png)

</div>

---

## Installing

Click the link above — the download starts right away. Double-click the file,
choose whether you want a Desktop shortcut, and finish.

**No administrator prompt**, and no Python, FFmpeg or anything else to install
— it is all inside the installer.

The app goes into `%LOCALAPPDATA%\Programs\YouTube Downloader`, the folder
Windows reserves for single-user programs, and that is exactly what makes the
permission dialog unnecessary. It is the same place Chrome, Discord and Spotify
install into.

> **Windows warning:** the installer is not code-signed yet, so SmartScreen
> shows *"Windows protected your PC"*. Click **More info → Run anyway**. This
> happens with any unsigned program; the
> [plan to fix it](source-code/docs/CODE-SIGNING.md) is documented.

To uninstall: **Settings → Apps → Installed apps**.

The installer is also on the
[releases page](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/releases/latest),
which is where previous versions live.

## What it does

Video in **MP4, MKV or WebM**, from 360p to 4K, with the audio already merged.
Audio in **MP3, M4A, Opus, WAV or FLAC**, from 128 to 320 kbps.

Paste a link and the app shows the thumbnail, title, channel and duration
before you commit to anything. The queue takes several downloads at once, with
real progress, speed, time remaining and cancellation. Playlists go in with one
click.

The finished file carries cover art and metadata, plus subtitles when you ask
for them. There is a history of past downloads, light and dark themes, and the
interface speaks **English, Portuguese and Spanish** — it follows your Windows
language and can be changed in Settings.

**It is not limited to YouTube.** Any `http`/`https` address is handed to
yt-dlp, which supports [over a thousand sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
— Vimeo, Twitch, SoundCloud, Reddit, Bandcamp and more.

### Videos that require a signed-in account

Age restrictions, members-only content and the *"confirm you're not a bot"*
prompt all need an authenticated session. In **Settings → Use cookies from
browser**, pick the browser where you are already signed in and **close it**
before downloading — while open, it keeps the cookie file locked.

### What keeps it working

Sites change how they serve video all the time, and the component that keeps up
is yt-dlp. A copy frozen inside the program would age within months, so the app
checks for a newer one at startup and offers to update it — straight from PyPI,
verified by SHA-256, into your user folder.

If one particular video stops downloading, updating the engine is the first
thing to try.

## The code

Everything lives in **[`source-code/`](source-code)** — implementation, tests,
packaging and the technical documentation.

| | |
|---|---|
| [Full documentation](source-code/README.md) | features, building, limitations |
| [Documentação em português](source-code/README.pt-BR.md) | a documentação completa em português |
| [Architecture](source-code/docs/ARCHITECTURE.md) | how the project is organised inside |
| [Contributing](source-code/CONTRIBUTING.md) | environment, conventions, how to send changes |
| [Security](source-code/SECURITY.md) | where the risk is and how to report it |
| [Changelog](source-code/CHANGELOG.md) | what changed in each release |

Building from scratch is a single command:

```powershell
cd source-code
powershell -ExecutionPolicy Bypass -File packaging\build.ps1
```

It creates the environment, downloads FFmpeg, generates icons and translations,
runs the 155 tests and produces the installer.

## Licence

Built by **Victor Medeiros** — IT Analyst, Developer, AI Engineer.

Copyright © 2026 Victor Medeiros. [MIT licensed](source-code/LICENSE).

Built on [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense),
[Qt/PySide6](https://www.qt.io/qt-for-python) (LGPL v3) and
[FFmpeg](https://ffmpeg.org) (LGPL v2.1+).

## Responsible use

Download only what you have the right to keep: your own material, public domain
works, openly licensed content, or media you have permission to save. Respect
each site's terms of service and the copyright law that applies to you.
