<#
.SYNOPSIS
    Extrai as strings da interface e compila os arquivos de tradução.

.DESCRIPTION
    Executa o ciclo padrão do Qt:
      1. pyside6-lupdate varre o código e atualiza os arquivos .ts
      2. pyside6-lrelease compila cada .ts em um .qm, que é o que o
         aplicativo carrega em tempo de execução

    O português é o idioma de origem — as strings do código já estão nele e
    não precisam de arquivo de tradução.

    Depois de rodar este script, traduções novas ou alteradas aparecem no .ts
    marcadas como "unfinished". Edite-as no Qt Linguist (pyside6-linguist) ou
    em qualquer editor de texto e rode o script de novo.

.PARAMETER SomenteCompilar
    Pula a extração e apenas compila os .ts existentes.
#>
[CmdletBinding()]
param(
    [switch]$SomenteCompilar
)

$ErrorActionPreference = 'Stop'

$packagingDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $packagingDir
$guiDir = Join-Path $repoRoot 'ytdownloader\gui'
$i18nDir = Join-Path $repoRoot 'ytdownloader\resources\i18n'
$venvScripts = Join-Path $repoRoot 'venv\Scripts'

function Resolver-Ferramenta([string]$nome) {
    $noVenv = Join-Path $venvScripts $nome
    if (Test-Path $noVenv) { return $noVenv }
    $noPath = Get-Command $nome -ErrorAction SilentlyContinue
    if ($noPath) { return $noPath.Source }
    throw "$nome nao encontrado. Instale as dependencias com: pip install -r requirements-dev.txt"
}

$lupdate = Resolver-Ferramenta 'pyside6-lupdate.exe'
$lrelease = Resolver-Ferramenta 'pyside6-lrelease.exe'

New-Item -ItemType Directory -Force -Path $i18nDir | Out-Null

if (-not $SomenteCompilar) {
    Write-Host 'Extraindo as strings da interface...'
    $fontes = Get-ChildItem $guiDir -Recurse -Filter '*.py' | ForEach-Object { $_.FullName }

    foreach ($ts in Get-ChildItem $i18nDir -Filter '*.ts') {
        # O idioma de destino vem do nome do arquivo: ytdownloader_<idioma>.ts
        $idioma = $ts.BaseName -replace '^ytdownloader_', ''
        Write-Host "  $($ts.Name) (destino: $idioma)"
        & $lupdate $fontes -ts $ts.FullName -source-language pt_BR -target-language $idioma
        if ($LASTEXITCODE -ne 0) { throw "lupdate falhou em $($ts.Name)" }
    }
}

Write-Host ''
Write-Host 'Compilando as traducoes...'
$pendentes = 0

foreach ($ts in Get-ChildItem $i18nDir -Filter '*.ts') {
    $qm = Join-Path $i18nDir ($ts.BaseName + '.qm')
    $saida = & $lrelease $ts.FullName -qm $qm
    if ($LASTEXITCODE -ne 0) { throw "lrelease falhou em $($ts.Name)" }

    $saida | Where-Object { $_ -match 'Generated' } | ForEach-Object {
        Write-Host "  $($ts.BaseName): $($_.Trim())"
        if ($_ -match '(\d+) unfinished' -and [int]$Matches[1] -gt 0) {
            $pendentes += [int]$Matches[1]
        }
    }
}

if ($pendentes -gt 0) {
    Write-Warning "$pendentes mensagem(ns) ainda sem traducao. Abra o .ts no Qt Linguist para completar."
}

Write-Host ''
Write-Host "Traducoes prontas em $i18nDir"
