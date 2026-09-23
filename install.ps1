# Run in PowerShell: irm https://raw.githubusercontent.com/jrmaiworm/codex-limbo/main/install.ps1 | iex
$ErrorActionPreference = 'Stop'

if (-not $env:USERPROFILE) {
    throw 'codex-limbo: USERPROFILE is unavailable.'
}

$installDir = Join-Path $env:USERPROFILE '.local\bin'
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
$uvExe = if ($uvCommand -and $uvCommand.CommandType -eq 'Application') {
    $uvCommand.Source
} else {
    Join-Path $installDir 'uv.exe'
}

if (-not (Test-Path $uvExe)) {
    $previousInstallDir = $env:UV_INSTALL_DIR
    $previousNoModifyPath = $env:UV_NO_MODIFY_PATH
    $env:UV_INSTALL_DIR = $installDir
    $env:UV_NO_MODIFY_PATH = '1'
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    } finally {
        if ($null -eq $previousInstallDir) { Remove-Item Env:UV_INSTALL_DIR -ErrorAction SilentlyContinue }
        else { $env:UV_INSTALL_DIR = $previousInstallDir }
        if ($null -eq $previousNoModifyPath) { Remove-Item Env:UV_NO_MODIFY_PATH -ErrorAction SilentlyContinue }
        else { $env:UV_NO_MODIFY_PATH = $previousNoModifyPath }
    }
    $uvExe = Join-Path $installDir 'uv.exe'
}
if (-not (Test-Path $uvExe)) {
    throw 'codex-limbo: uv installation did not produce uv.exe.'
}

$source = if ($env:CODEX_LIMBO_PACKAGE_SOURCE) {
    $env:CODEX_LIMBO_PACKAGE_SOURCE
} else {
    'https://github.com/jrmaiworm/codex-limbo/archive/refs/heads/main.zip'
}
& $uvExe tool install --python 3.11 $source
if ($LASTEXITCODE -ne 0) {
    throw 'codex-limbo: package installation failed.'
}

$toolBin = (& $uvExe tool dir --bin).Trim()
if ($LASTEXITCODE -ne 0 -or -not $toolBin) {
    throw 'codex-limbo: could not find the tool executable directory.'
}
foreach ($directory in @($installDir, $toolBin)) {
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $entries = @($userPath -split ';' | Where-Object { $_ })
    if ($entries -notcontains $directory) {
        [Environment]::SetEnvironmentVariable('Path', (($entries + $directory) -join ';'), 'User')
    }
    if (@($env:Path -split ';') -notcontains $directory) {
        $env:Path += ";$directory"
    }
}

$limboExe = Join-Path $toolBin 'codex-limbo.exe'
if (-not (Test-Path $limboExe)) {
    throw 'codex-limbo: executable was not created.'
}
& $limboExe --version
if ($LASTEXITCODE -ne 0) {
    throw 'codex-limbo: installed executable failed to start.'
}

Write-Host 'codex-limbo installed. Open a new PowerShell window and run: codex-limbo doctor'
Write-Host "You can run it now with: $limboExe doctor"
