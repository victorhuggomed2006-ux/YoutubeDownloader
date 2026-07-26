<#
.SYNOPSIS
    Builds the YouTube Downloader executable and MSI installer.

.DESCRIPTION
    Runs the full packaging pipeline:
      1. Checks the environment (Python, venv, dependencies)
      2. Downloads FFmpeg, if not already present
      3. Generates the icons
      4. Runs the automated tests
      5. Builds the executable with PyInstaller
      6. Builds the MSI installer with WiX

    Output in dist/:
      YouTubeDownloader/                       the app, to run without installing
      YouTubeDownloader-<version>-Setup.msi    installer for the end user

    The installer is per-user: it writes to %LOCALAPPDATA%\Programs and does not
    ask for elevation. Installing into Program Files would require administrator
    rights — a Windows restriction, not a packaging choice.

.PARAMETER SkipTests
    Skips the test suite before building.

.PARAMETER SkipMsi
    Builds only the executable, without the installer.

.PARAMETER Clean
    Deletes build/ and dist/ before starting.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File packaging\build.ps1

.NOTES
    Requires: Python 3.10+, .NET SDK 6+ (for WiX).
    Author: Victor Medeiros — MIT licence.
#>
[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$SkipMsi,
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'

$packagingDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $packagingDir
$distDir = Join-Path $repoRoot 'dist'
$buildDir = Join-Path $repoRoot 'build'
$appDir = Join-Path $distDir 'YouTubeDownloader'
$venvPython = Join-Path $repoRoot 'venv\Scripts\python.exe'

function Write-Step([string]$Message) {
    Write-Host ''
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok([string]$Message) {
    Write-Host "    $Message" -ForegroundColor Green
}

# ── 1. Ambiente ──────────────────────────────────────────────────────────
Write-Step 'Checking the environment'

if (-not (Test-Path $venvPython)) {
    Write-Host '    Virtual environment not found. Creating...'
    $systemPython = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $systemPython) {
        throw 'Python not found on PATH. Install Python 3.10 or newer.'
    }
    & $systemPython -m venv (Join-Path $repoRoot 'venv')
}

# Upgrading pip is nice to have, not essential: in some installs it cannot
# replace itself and writes to stderr. Without the try/catch, PowerShell
# turns that warning into a terminating error and the build dies for nothing.
try {
    & $venvPython -m pip install --quiet --disable-pip-version-check --upgrade pip
}
catch {
    Write-Host '    (could not upgrade pip; carrying on with the current version)'
}

& $venvPython -m pip install --quiet --disable-pip-version-check -r (Join-Path $repoRoot 'requirements-dev.txt')
if ($LASTEXITCODE -ne 0) { throw 'Failed to install the dependencies.' }

$appVersion = (& $venvPython -c "import sys; sys.path.insert(0, r'$repoRoot'); import ytdownloader; print(ytdownloader.__version__)").Trim()
if (-not $appVersion) { throw 'Could not read the application version.' }
Write-Ok "Python ready. Application version: $appVersion"

if ($Clean) {
    Write-Step 'Cleaning build/ and dist/'
    foreach ($dir in @($buildDir, $distDir)) {
        if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
    }
    Write-Ok 'Folders removed.'
}

# ── 2. FFmpeg ────────────────────────────────────────────────────────────
Write-Step 'Preparing FFmpeg'
& (Join-Path $packagingDir 'fetch_ffmpeg.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Failed to obtain FFmpeg.' }

# ── 3. Icones ────────────────────────────────────────────────────────────
Write-Step 'Generating the icons'
& $venvPython (Join-Path $packagingDir 'make_icon.py')
if ($LASTEXITCODE -ne 0) { throw 'Failed to generate the icons.' }

# ── 3b. Translations ─────────────────────────────────────────────────────
Write-Step 'Compiling the translations'
& (Join-Path $packagingDir 'build_translations.ps1') -CompileOnly
if ($LASTEXITCODE -ne 0) { throw 'Failed to compile the translations.' }

# ── 4. Testes ────────────────────────────────────────────────────────────
if ($SkipTests) {
    Write-Step 'Tests skipped (-SkipTests)'
}
else {
    Write-Step 'Running the tests'
    & $venvPython -m pytest (Join-Path $repoRoot 'tests')
    if ($LASTEXITCODE -ne 0) { throw 'The tests failed. Fix them before packaging.' }
    Write-Ok 'All tests passed.'
}

# ── 5. Executavel ────────────────────────────────────────────────────────
Write-Step 'Building the executable (PyInstaller)'
$env:PYTHONPATH = $repoRoot
& $venvPython -m PyInstaller (Join-Path $packagingDir 'ytdownloader.spec') `
    --noconfirm --distpath $distDir --workpath $buildDir --log-level WARN
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }

$exePath = Join-Path $appDir 'YouTubeDownloader.exe'
if (-not (Test-Path $exePath)) { throw "Executable not found at $exePath" }

$appSize = [math]::Round((Get-ChildItem $appDir -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
Write-Ok "Executable ready: $exePath ($appSize MB)"

# ── 6. Installer ─────────────────────────────────────────────────────────
if ($SkipMsi) {
    Write-Step 'Installer skipped (-SkipMsi)'
    Write-Host ''
    Write-Host "Done. Application at: $appDir" -ForegroundColor Green
    exit 0
}

Write-Step 'Building the installer (WiX)'

$wix = Get-Command wix -ErrorAction SilentlyContinue
if (-not $wix) {
    $candidate = Join-Path $env:USERPROFILE '.dotnet\tools\wix.exe'
    if (Test-Path $candidate) {
        $wix = $candidate
    }
    else {
        throw @'
WiX not found. Install it with:
    dotnet tool install --global wix --version 5.0.2
    wix extension add -g WixToolset.UI.wixext/5.0.2
'@
    }
}
else {
    $wix = $wix.Source
}

# The name carries "Setup" to make the file's purpose obvious. The extension
# stays .msi because that is what makes Windows hand the file to msiexec:
# an MSI renamed to .exe simply does not open.
$msiName = "YouTubeDownloader-$appVersion-Setup.msi"
$msiPath = Join-Path $distDir $msiName

& $wix build (Join-Path $packagingDir 'wix\Package.wxs') `
    -define "AppDir=$appDir" `
    -define "AppVersion=$appVersion" `
    -define "RepoRoot=$repoRoot" `
    -ext WixToolset.UI.wixext `
    -arch x64 `
    -culture pt-BR `
    -out $msiPath

if ($LASTEXITCODE -ne 0) { throw 'WiX failed to build the installer.' }
if (-not (Test-Path $msiPath)) { throw "Installer not found at $msiPath" }

$msiSize = [math]::Round((Get-Item $msiPath).Length / 1MB, 1)

# Intermediate files that are of no interest to whoever downloads this.
Get-ChildItem $distDir -Filter '*.wixpdb' -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Host ''
Write-Host '--------------------------------------------------------'
Write-Host ' Packaging complete'
Write-Host '--------------------------------------------------------'
Write-Host "  Application : $appDir ($appSize MB)"
Write-Host "  Installer   : $msiPath ($msiSize MB)"
Write-Host ''
Write-Host '  Installs for the current user, with no administrator prompt.'
Write-Host '  Destination: %LOCALAPPDATA%\Programs\YouTube Downloader'
Write-Host ''
