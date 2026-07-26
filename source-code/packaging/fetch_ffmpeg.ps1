<#
.SYNOPSIS
    Baixa os binários do FFmpeg usados pelo YouTube Downloader.

.DESCRIPTION
    Obtém a build "essentials" para Windows x64 mantida por Gyan Doshi (a mesma
    recomendada em ffmpeg.org) e extrai apenas ffmpeg.exe e ffprobe.exe para
    packaging/vendor/ffmpeg. Esses arquivos são embutidos no executável final,
    para que o usuário não precise instalar nada além do MSI.

.PARAMETER Force
    Baixa novamente mesmo que os binários já existam.
#>
[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$packagingDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$vendorDir = Join-Path $packagingDir 'vendor\ffmpeg'
$ffmpegExe = Join-Path $vendorDir 'ffmpeg.exe'
$ffprobeExe = Join-Path $vendorDir 'ffprobe.exe'

if (-not $Force -and (Test-Path $ffmpegExe) -and (Test-Path $ffprobeExe)) {
    Write-Host "FFmpeg ja esta em $vendorDir (use -Force para baixar de novo)."
    exit 0
}

$downloadUrl = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
$tempZip = Join-Path ([System.IO.Path]::GetTempPath()) 'ffmpeg-essentials.zip'
$tempExtract = Join-Path ([System.IO.Path]::GetTempPath()) 'ffmpeg-extract'

Write-Host "Baixando FFmpeg de $downloadUrl ..."
$previousProgress = $ProgressPreference
$ProgressPreference = 'SilentlyContinue'
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip -UseBasicParsing
}
finally {
    $ProgressPreference = $previousProgress
}

$sizeMb = [math]::Round((Get-Item $tempZip).Length / 1MB, 1)
Write-Host "Download concluido ($sizeMb MB). Extraindo..."

if (Test-Path $tempExtract) { Remove-Item -Recurse -Force $tempExtract }
Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null

foreach ($name in @('ffmpeg.exe', 'ffprobe.exe')) {
    $source = Get-ChildItem -Path $tempExtract -Filter $name -Recurse | Select-Object -First 1
    if (-not $source) {
        throw "Nao foi possivel encontrar $name dentro do pacote baixado."
    }
    Copy-Item -Path $source.FullName -Destination (Join-Path $vendorDir $name) -Force
    $mb = [math]::Round($source.Length / 1MB, 1)
    Write-Host "  $name ($mb MB)"
}

# Guarda a licenca do FFmpeg junto dos binarios (exigencia da LGPL/GPL).
$licenseSource = Get-ChildItem -Path $tempExtract -Filter 'LICENSE' -Recurse | Select-Object -First 1
if ($licenseSource) {
    Copy-Item -Path $licenseSource.FullName -Destination (Join-Path $vendorDir 'FFMPEG-LICENSE.txt') -Force
}

Remove-Item -Force $tempZip -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $tempExtract -ErrorAction SilentlyContinue

& (Join-Path $vendorDir 'ffmpeg.exe') -version | Select-Object -First 1
Write-Host "FFmpeg pronto em $vendorDir"
