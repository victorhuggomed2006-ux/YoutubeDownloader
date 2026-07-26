<#
.SYNOPSIS
    Extracts the interface strings and compiles the translation files.

.DESCRIPTION
    Runs the standard Qt cycle:
      1. pyside6-lupdate scans the code and updates the .ts files
      2. pyside6-lrelease compiles each .ts into a .qm, which is what the
         application loads at runtime

    English is the source language — the strings in the code are already in it
    and need no translation file.

    After running this script, new or changed entries appear in the .ts marked
    as "unfinished". Edit them in Qt Linguist (pyside6-linguist) or in any text
    editor, then run the script again.

.PARAMETER CompileOnly
    Skips extraction and only compiles the existing .ts files.
#>
[CmdletBinding()]
param(
    [switch]$CompileOnly
)

$ErrorActionPreference = 'Stop'

$packagingDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $packagingDir
$guiDir = Join-Path $repoRoot 'ytdownloader\gui'
$i18nDir = Join-Path $repoRoot 'ytdownloader\resources\i18n'
$venvScripts = Join-Path $repoRoot 'venv\Scripts'

function Resolve-Tool([string]$name) {
    # The virtual environment normally lives beside this project, but a
    # developer may keep it one level up, at the repository root.
    $candidates = @(
        (Join-Path $venvScripts $name)
        (Join-Path (Split-Path -Parent $repoRoot) "venv\Scripts\$name")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }

    $onPath = Get-Command $name -ErrorAction SilentlyContinue
    if ($onPath) { return $onPath.Source }

    throw "$name not found. Install the dependencies with: pip install -r requirements-dev.txt"
}

$lupdate = Resolve-Tool 'pyside6-lupdate.exe'
$lrelease = Resolve-Tool 'pyside6-lrelease.exe'

New-Item -ItemType Directory -Force -Path $i18nDir | Out-Null

if (-not $CompileOnly) {
    Write-Host 'Extracting the interface strings...'
    $sources = Get-ChildItem $guiDir -Recurse -Filter '*.py' | ForEach-Object { $_.FullName }

    foreach ($ts in Get-ChildItem $i18nDir -Filter '*.ts') {
        # The target language comes from the file name: ytdownloader_<language>.ts
        $language = $ts.BaseName -replace '^ytdownloader_', ''
        Write-Host "  $($ts.Name) (target: $language)"
        & $lupdate $sources -ts $ts.FullName -source-language en -target-language $language
        if ($LASTEXITCODE -ne 0) { throw "lupdate failed on $($ts.Name)" }
    }
}

Write-Host ''
Write-Host 'Compiling the translations...'
$pending = 0

foreach ($ts in Get-ChildItem $i18nDir -Filter '*.ts') {
    $qm = Join-Path $i18nDir ($ts.BaseName + '.qm')
    $output = & $lrelease $ts.FullName -qm $qm
    if ($LASTEXITCODE -ne 0) { throw "lrelease failed on $($ts.Name)" }

    $output | Where-Object { $_ -match 'Generated' } | ForEach-Object {
        Write-Host "  $($ts.BaseName): $($_.Trim())"
        if ($_ -match '(\d+) unfinished' -and [int]$Matches[1] -gt 0) {
            $pending += [int]$Matches[1]
        }
    }
}

if ($pending -gt 0) {
    Write-Warning "$pending message(s) still untranslated. Open the .ts in Qt Linguist to finish."
}

Write-Host ''
Write-Host "Translations ready in $i18nDir"
