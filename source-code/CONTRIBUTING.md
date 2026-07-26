# Contributing

Contributions are welcome — bug reports, translations, features, or simply
telling us a site does not work.

## Getting set up

```powershell
git clone https://github.com/victorhuggomed2006-ux/YoutubeDownloader
cd YoutubeDownloader/source-code

python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt

powershell -ExecutionPolicy Bypass -File packaging\fetch_ffmpeg.ps1
python packaging\make_icon.py
powershell -ExecutionPolicy Bypass -File packaging\build_translations.ps1

$env:PYTHONPATH = "."
python -m ytdownloader
```

## Before opening a pull request

```powershell
pytest
ruff check .
ruff format --check .
```

CI runs the same three commands, so a green local run usually means a green PR.

## How the code is organised

The project draws a hard line between business rules and interface:

- **`ytdownloader/core/`** — imports nothing from Qt. All download logic,
  validation, formats and persistence live here, and are testable without
  opening a window.
- **`ytdownloader/gui/`** — interface only. It talks to the core through
  callbacks and Qt signals.

Please keep that line. It is what lets the test suite verify real behaviour
without a display, and what keeps the core reusable. The module-by-module
rundown is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Conventions

**Language.** Code, comments, docstrings and user-facing strings are written in
English. English is also the translation key; Portuguese and Spanish are
translations.

**Error messages** are written for people who do not program. Translate
yt-dlp's raw output in `core/errors.py` instead of passing it through.

**New user-facing strings** must be wrapped in `self.tr(...)`. After adding
them, run `packaging\build_translations.ps1` and fill in the translations.

Messages that originate in `core/` cannot call `tr()` — the core has no Qt. Add
them to `_declare_core_messages` in `gui/i18n.py` so the extraction tool finds
them.

**Long-running work** never runs on the UI thread. Use the workers in
`gui/workers.py`.

**New download options** go through `core/formats.py`, not straight into the
yt-dlp option dictionary.

## Adding a language

1. Copy `ytdownloader/resources/i18n/ytdownloader_es.ts` to
   `ytdownloader_<code>.ts` (for example `ytdownloader_fr.ts`) and change the
   `language` attribute at the top
2. Add the code to `LANGUAGES` in `ytdownloader/gui/i18n.py`
3. Run `packaging\build_translations.ps1`
4. Translate the entries — Qt Linguist (`pyside6-linguist`) or any text editor
   works — and run the script again

Watch out for plural forms: `%n` messages need every form your language uses,
which may be more than two.

## Reporting a problem

Open an issue with:

- what you were doing and what happened
- the version from the About window
- the relevant part of `%APPDATA%\YouTubeDownloader\ytdownloader.log`
- the video link, if it is specific to one video

For security issues, do not open a public issue — see [SECURITY.md](SECURITY.md).

## Licence

By contributing, you agree your contribution is distributed under the project's
[MIT licence](LICENSE).
