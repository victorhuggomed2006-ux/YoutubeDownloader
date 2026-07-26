# -*- mode: python ; coding: utf-8 -*-
"""Receita do PyInstaller para o YouTube Downloader.

Gera uma pasta autocontida em dist/YouTubeDownloader com o executável, o
FFmpeg e todas as dependências. O usuário final não precisa de Python.

Uso:
    pyinstaller packaging/ytdownloader.spec --noconfirm
"""

import sys
from pathlib import Path

# O PyInstaller executa este arquivo com exec(), então __file__ não existe.
REPO_ROOT = Path(SPECPATH).resolve().parent
SRC_DIR = REPO_ROOT
RESOURCES_DIR = SRC_DIR / "ytdownloader" / "resources"
FFMPEG_DIR = REPO_ROOT / "packaging" / "vendor" / "ffmpeg"

sys.path.insert(0, str(SRC_DIR))
from ytdownloader import __app_name__, __author__, __copyright__, __version__  # noqa: E402

APP_EXE_NAME = "YouTubeDownloader"

# ── Metadados que o Windows mostra nas propriedades do arquivo ───────────
_parts = tuple(int(p) for p in __version__.split(".")) + (0, 0, 0, 0)
_filevers = _parts[:4]

VERSION_INFO = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={_filevers},
    prodvers={_filevers},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '041604B0',
        [StringStruct('CompanyName', {__author__!r}),
         StringStruct('FileDescription', {__app_name__!r}),
         StringStruct('FileVersion', {__version__!r}),
         StringStruct('InternalName', {APP_EXE_NAME!r}),
         StringStruct('LegalCopyright', {__copyright__!r}),
         StringStruct('OriginalFilename', {APP_EXE_NAME + '.exe'!r}),
         StringStruct('ProductName', {__app_name__!r}),
         StringStruct('ProductVersion', {__version__!r})])
    ]),
    VarFileInfo([VarStruct('Translation', [1046, 1200])])
  ]
)
"""

VERSION_FILE = REPO_ROOT / "packaging" / "version_info.txt"
VERSION_FILE.write_text(VERSION_INFO, encoding="utf-8")

# ── Recursos ─────────────────────────────────────────────────────────────
# Icones, setas e as traducoes compiladas (resources/i18n/*.qm).
datas = []
if RESOURCES_DIR.is_dir():
    for item in RESOURCES_DIR.rglob("*"):
        if not item.is_file() or item.suffix == ".ts":
            continue  # o .ts e fonte de traducao, so o .qm vai junto
        destino = Path("resources") / item.relative_to(RESOURCES_DIR).parent
        datas.append((str(item), str(destino)))

if not any(str(d[0]).endswith(".qm") for d in datas):
    print("AVISO: nenhuma traducao compilada encontrada; a interface sairá so em portugues.")

# ── FFmpeg ───────────────────────────────────────────────────────────────
binaries = []
missing_ffmpeg = []
for name in ("ffmpeg.exe", "ffprobe.exe"):
    candidate = FFMPEG_DIR / name
    if candidate.is_file():
        binaries.append((str(candidate), "ffmpeg"))
    else:
        missing_ffmpeg.append(name)

if missing_ffmpeg:
    raise SystemExit(
        "FFmpeg nao encontrado em packaging/vendor/ffmpeg: "
        + ", ".join(missing_ffmpeg)
        + "\nExecute primeiro: powershell -File packaging/fetch_ffmpeg.ps1"
    )

# A licenca do FFmpeg acompanha os binarios, como exige a LGPL.
ffmpeg_license = FFMPEG_DIR / "FFMPEG-LICENSE.txt"
if ffmpeg_license.is_file():
    datas.append((str(ffmpeg_license), "ffmpeg"))

for extra in ("LICENSE", "README.md"):
    candidate = REPO_ROOT / extra
    if candidate.is_file():
        datas.append((str(candidate), "."))

# ── Modulos ──────────────────────────────────────────────────────────────
hiddenimports = [
    "yt_dlp",
    "yt_dlp.extractor",
    "yt_dlp.extractor.youtube",
    "yt_dlp.postprocessor",
    "yt_dlp.compat",
    "yt_dlp.networking",
    "yt_dlp.networking._urllib",
    "yt_dlp.networking._requests",
    "requests",
    "certifi",
]

# Nada disso e usado pelo aplicativo; tirar reduz bastante o tamanho final.
excludes = [
    "tkinter",
    "unittest",
    "pydoc",
    "doctest",
    "test",
    "distutils",
    "setuptools",
    "pip",
    "numpy",
    "PIL",
    "matplotlib",
    "pytest",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtPositioning",
    "PySide6.QtLocation",
    "PySide6.QtSerialPort",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtSpatialAudio",
    "PySide6.QtTextToSpeech",
]
# Atencao: shiboken6 e o nucleo do PySide6 e nunca pode entrar nesta lista.


a = Analysis(
    [str(REPO_ROOT / "packaging" / "entry.py")],
    pathex=[str(SRC_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_EXE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # aplicativo de janela: sem console preto ao abrir
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(RESOURCES_DIR / "icon.ico"),
    version=str(VERSION_FILE),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_EXE_NAME,
)
