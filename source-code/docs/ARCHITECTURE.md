# Architecture

The implementation of YouTube Downloader. It is all Python.

```
ytdownloader/
├── core/     business rules — imports nothing from Qt
├── gui/      the PySide6 interface
└── app.py    startup
```

## The line between core and gui

`core/` knows nothing about the interface. It does not import PySide6, does not
know a window exists, and would work the same behind a command line or a
different GUI.

This is not architectural purism: it is what lets the 155 tests run without
opening a single window, and it is why the suite finishes in seconds inside
continuous integration. The one test that reaches into `gui/` covers language
selection and imports `QtCore` alone — it creates no widget.

The rule of thumb for anyone changing things: if the code needs to know a
button exists, it belongs in `gui/`. If it decides what to do with a video, it
belongs in `core/`.

## What each module does

**`core/downloader.py`** — the layer over yt-dlp. Builds the options, follows
the progress and works out where the final file ended up. It is the only place
that talks to yt-dlp directly.

**`core/formats.py`** — the catalogue of qualities and the format selectors.
Every new download option goes through here, never straight into yt-dlp's
option dictionary.

**`core/urls.py`** — validates and normalises the pasted address. Accepts any
`http`/`https`, with dedicated handling for YouTube, and refuses schemes such
as `file://` and `javascript:`.

**`core/errors.py`** — turns yt-dlp's raw output into messages that make sense
to someone who does not program. "Sign in to confirm you're not a bot" becomes
a sentence that explains the problem and what to do about it.

**`core/updater.py`** — downloads new yt-dlp versions from PyPI and puts them on
`sys.path`. It is the only component that executes code fetched at runtime,
which is why the security checks live here: SHA-256, refusal of paths that
escape the destination folder, and a size ceiling.

**`core/ffmpeg.py`**, **`core/jsruntime.py`** — locate the external binaries:
the FFmpeg bundled with the installer and the JavaScript interpreter, if there
is one.

**`core/settings.py`**, **`core/history.py`**, **`core/paths.py`** — preferences,
history and the directories the application uses.

**`gui/main_window.py`** — the window. Wires the components together and drives
the queue.

**`gui/workers.py`** — everything slow goes through here. Nothing that takes
time runs on the interface thread; results come back through Qt signals.

**`gui/i18n.py`** — translation. The strings in the code are written in English
and act as the keys; Portuguese and Spanish come from catalogues in
`resources/i18n`.

**`gui/theme.py`** — the light and dark themes, as a Qt style sheet.

## Running from here

```powershell
cd source-code
$env:PYTHONPATH = "."
python -m ytdownloader
```

The full walkthrough, with dependencies and tooling, is in the
[project README](../README.md#development).
