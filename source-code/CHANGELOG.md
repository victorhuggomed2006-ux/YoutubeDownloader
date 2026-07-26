# Changelog

Notable changes to this project, following the spirit of
[Semantic Versioning](https://semver.org).

---

## [1.3.0] — 2026-07-26

### Changed

- **The whole project is now written in English** — code, comments, docstrings,
  user-facing strings and documentation. English is also the translation key,
  which is the Qt convention and what lets contributors from anywhere read the
  source.
- **Three interface languages:** English, Portuguese (Brazil) and Spanish. The
  app follows the Windows language and can be switched in Settings. Switching
  asks for a restart, because Qt only rebuilds the text of widgets created
  after the translator is installed.
- The Python package moved to the root of `source-code/` instead of a `src/`
  subfolder, so `pyproject.toml`, the PyInstaller spec and the build scripts
  all point at one place.

### Fixed

- The interface came up in English on a machine whose display language was
  Portuguese or Spanish. Qt's `QLocale.system().name()` reports the *regional
  format* setting, not the display language — an English keyboard layout on a
  Brazilian Windows is enough to make the two disagree. It now reads
  `uiLanguages()`, which is the list Windows actually ranks.
- The cookie setting stored `nenhum` as its value — Portuguese leaking into the
  data format, where it would have outlived the interface. It is `none` now,
  and a file written by 1.2.0 is migrated and rewritten on load.
- `settings.json` and `history.json` were thrown away and replaced by defaults
  if they carried a byte order mark, which is what Notepad and PowerShell write
  when someone edits them by hand. Both are read as `utf-8-sig` now.
- FFmpeg discovery and the install directory both walked one level too far up
  after the package moved.
- The download link in the README pointed at GitHub's file page rather than the
  file. GitHub refuses to render a 96 MB binary, so clicking it produced "we
  can't show files that are this big right now" instead of a download.

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
- Interface following the Windows language
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

[1.3.0]: https://github.com/victorhuggomed2006-ux/YoutubeDownloader/releases/tag/v1.3.0
[1.2.0]: https://github.com/victorhuggomed2006-ux/YoutubeDownloader/releases/tag/v1.2.0
