<#
.SYNOPSIS
    Gera o executável e o instalador MSI do YouTube Downloader.

.DESCRIPTION
    Executa o pipeline completo de empacotamento:
      1. Verifica o ambiente (Python, venv, dependências)
      2. Baixa o FFmpeg, se ainda não estiver presente
      3. Gera os ícones
      4. Roda os testes automatizados
      5. Compila o executável com o PyInstaller
      6. Compila o instalador MSI com o WiX

    Saída em dist/:
      YouTubeDownloader/                       aplicativo, para rodar sem instalar
      YouTubeDownloader-<versao>-Setup.msi     instalador para o usuário final

    O instalador é per-user: grava em %LOCALAPPDATA%\Programs e não pede
    elevação. Instalar em Arquivos de Programas exigiria privilégio de
    administrador — é restrição do Windows, não escolha do empacotamento.

.PARAMETER SkipTests
    Não roda a suíte de testes antes de compilar.

.PARAMETER SkipMsi
    Gera apenas o executável, sem o instalador.

.PARAMETER Clean
    Apaga build/ e dist/ antes de começar.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File packaging\build.ps1

.NOTES
    Requisitos: Python 3.10+, .NET SDK 6+ (para o WiX).
    Autor: Victor Medeiros — licença MIT.
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
Write-Step 'Verificando o ambiente'

if (-not (Test-Path $venvPython)) {
    Write-Host '    Ambiente virtual nao encontrado. Criando...'
    $systemPython = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $systemPython) {
        throw 'Python nao encontrado no PATH. Instale o Python 3.10 ou superior.'
    }
    & $systemPython -m venv (Join-Path $repoRoot 'venv')
}

# Atualizar o pip e desejavel, mas nao essencial: em algumas instalacoes ele nao
# consegue se substituir e escreve no stderr. Sem o try/catch, o PowerShell
# transforma esse aviso em erro terminante e o build morre por nada.
try {
    & $venvPython -m pip install --quiet --disable-pip-version-check --upgrade pip
}
catch {
    Write-Host '    (nao foi possivel atualizar o pip; seguindo com a versao atual)'
}

& $venvPython -m pip install --quiet --disable-pip-version-check -r (Join-Path $repoRoot 'requirements-dev.txt')
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar as dependencias.' }

$appVersion = (& $venvPython -c "import sys; sys.path.insert(0, r'$repoRoot'); import ytdownloader; print(ytdownloader.__version__)").Trim()
if (-not $appVersion) { throw 'Nao foi possivel ler a versao do aplicativo.' }
Write-Ok "Python pronto. Versao do aplicativo: $appVersion"

if ($Clean) {
    Write-Step 'Limpando build/ e dist/'
    foreach ($dir in @($buildDir, $distDir)) {
        if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
    }
    Write-Ok 'Pastas removidas.'
}

# ── 2. FFmpeg ────────────────────────────────────────────────────────────
Write-Step 'Preparando o FFmpeg'
& (Join-Path $packagingDir 'fetch_ffmpeg.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Falha ao obter o FFmpeg.' }

# ── 3. Icones ────────────────────────────────────────────────────────────
Write-Step 'Gerando os icones'
& $venvPython (Join-Path $packagingDir 'make_icon.py')
if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar os icones.' }

# ── 3b. Traducoes ────────────────────────────────────────────────────────
Write-Step 'Compilando as traducoes'
& (Join-Path $packagingDir 'build_translations.ps1') -SomenteCompilar
if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar as traducoes.' }

# ── 4. Testes ────────────────────────────────────────────────────────────
if ($SkipTests) {
    Write-Step 'Testes ignorados (-SkipTests)'
}
else {
    Write-Step 'Rodando os testes'
    & $venvPython -m pytest (Join-Path $repoRoot 'tests')
    if ($LASTEXITCODE -ne 0) { throw 'Os testes falharam. Corrija antes de empacotar.' }
    Write-Ok 'Todos os testes passaram.'
}

# ── 5. Executavel ────────────────────────────────────────────────────────
Write-Step 'Compilando o executavel (PyInstaller)'
$env:PYTHONPATH = $repoRoot
& $venvPython -m PyInstaller (Join-Path $packagingDir 'ytdownloader.spec') `
    --noconfirm --distpath $distDir --workpath $buildDir --log-level WARN
if ($LASTEXITCODE -ne 0) { throw 'O PyInstaller falhou.' }

$exePath = Join-Path $appDir 'YouTubeDownloader.exe'
if (-not (Test-Path $exePath)) { throw "Executavel nao encontrado em $exePath" }

$appSize = [math]::Round((Get-ChildItem $appDir -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
Write-Ok "Executavel pronto: $exePath ($appSize MB)"

# ── 6. Instalador ────────────────────────────────────────────────────────
if ($SkipMsi) {
    Write-Step 'Instalador ignorado (-SkipMsi)'
    Write-Host ''
    Write-Host "Concluido. Aplicativo em: $appDir" -ForegroundColor Green
    exit 0
}

Write-Step 'Compilando o instalador (WiX)'

$wix = Get-Command wix -ErrorAction SilentlyContinue
if (-not $wix) {
    $candidate = Join-Path $env:USERPROFILE '.dotnet\tools\wix.exe'
    if (Test-Path $candidate) {
        $wix = $candidate
    }
    else {
        throw @'
WiX nao encontrado. Instale com:
    dotnet tool install --global wix --version 5.0.2
    wix extension add -g WixToolset.UI.wixext/5.0.2
'@
    }
}
else {
    $wix = $wix.Source
}

# O nome traz "Setup" para deixar obvio o que o arquivo faz. A extensao
# continua .msi porque e ela que faz o Windows entregar o arquivo ao msiexec:
# um MSI renomeado para .exe simplesmente nao abre.
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

if ($LASTEXITCODE -ne 0) { throw 'O WiX falhou ao gerar o instalador.' }
if (-not (Test-Path $msiPath)) { throw "Instalador nao encontrado em $msiPath" }

$msiSize = [math]::Round((Get-Item $msiPath).Length / 1MB, 1)

# Arquivos intermediarios que nao interessam a quem baixa.
Get-ChildItem $distDir -Filter '*.wixpdb' -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Host ''
Write-Host '--------------------------------------------------------'
Write-Host ' Empacotamento concluido'
Write-Host '--------------------------------------------------------'
Write-Host "  Aplicativo  : $appDir ($appSize MB)"
Write-Host "  Instalador  : $msiPath ($msiSize MB)"
Write-Host ''
Write-Host '  Instala para o usuario atual, sem pedir administrador.'
Write-Host '  Destino: %LOCALAPPDATA%\Programs\YouTube Downloader'
Write-Host ''
