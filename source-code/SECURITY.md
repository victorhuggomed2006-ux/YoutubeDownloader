# Security Policy

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

**`ytdownloader/core/updater.py`** — downloads a package from PyPI, extracts it and puts it
on `sys.path`, where the code will be imported and executed. It is the only
component that runs code fetched at runtime. Its defences are the SHA-256 check
against the digest published by PyPI, refusal of archive members whose path
escapes the destination directory (Zip Slip), a size ceiling, and refusal of
any package that does not contain `yt_dlp`. All four are covered by tests in
`tests/test_updater.py`.

**`ytdownloader/core/urls.py`** — the only input the user pastes in. It accepts `http` and
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
