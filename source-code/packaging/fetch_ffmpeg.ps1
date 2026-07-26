<#
.SYNOPSIS
    Downloads the FFmpeg binaries used by YouTube Downloader.

.DESCRIPTION
    Fetches the "essentials" build for Windows x64 maintained by Gyan Doshi (the
    one recommended on ffmpeg.org) and extracts only ffmpeg.exe and ffprobe.exe
    into packaging/vendor/ffmpeg. Those files are bundled into the final
    executable, so the user needs nothing beyond the MSI.

.PARAMETER Force
    Downloads again even if the binaries already exist.
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
    Write-Host "FFmpeg is already in $vendorDir (use -Force to download again)."
    exit 0
}

$downloadUrl = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
$tempZip = Join-Path ([System.IO.Path]::GetTempPath()) 'ffmpeg-essentials.zip'
$tempExtract = Join-Path ([System.IO.Path]::GetTempPath()) 'ffmpeg-extract'

Write-Host "Downloading FFmpeg from $downloadUrl ..."
$previousProgress = $ProgressPreference
$ProgressPreference = 'SilentlyContinue'
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip -UseBasicParsing
}
finally {
    $ProgressPreference = $previousProgress
}

$sizeMb = [math]::Round((Get-Item $tempZip).Length / 1MB, 1)
Write-Host "Download complete ($sizeMb MB). Extracting..."

if (Test-Path $tempExtract) { Remove-Item -Recurse -Force $tempExtract }
Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null

foreach ($name in @('ffmpeg.exe', 'ffprobe.exe')) {
    $source = Get-ChildItem -Path $tempExtract -Filter $name -Recurse | Select-Object -First 1
    if (-not $source) {
        throw "Could not find $name inside the downloaded package."
    }
    Copy-Item -Path $source.FullName -Destination (Join-Path $vendorDir $name) -Force
    $mb = [math]::Round($source.Length / 1MB, 1)
    Write-Host "  $name ($mb MB)"
}

# Keep FFmpeg's licence next to the binaries, as the LGPL/GPL requires.
$licenseSource = Get-ChildItem -Path $tempExtract -Filter 'LICENSE' -Recurse | Select-Object -First 1
if ($licenseSource) {
    Copy-Item -Path $licenseSource.FullName -Destination (Join-Path $vendorDir 'FFMPEG-LICENSE.txt') -Force
}

Remove-Item -Force $tempZip -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $tempExtract -ErrorAction SilentlyContinue

& (Join-Path $vendorDir 'ffmpeg.exe') -version | Select-Object -First 1
Write-Host "FFmpeg ready in $vendorDir"
