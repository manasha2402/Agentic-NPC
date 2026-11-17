param([switch]$Force)

# Runs the same five baseline episodes directly on Windows when Docker is unavailable.
$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$RunsRoot = Join-Path $ProjectRoot 'runs'
New-Item -ItemType Directory -Force -Path $RunsRoot | Out-Null
$ResolvedRunsRoot = [System.IO.Path]::GetFullPath($RunsRoot)

foreach ($Number in '01','02','03','04','05') {
    $Target = Join-Path $RunsRoot "run-$Number"
    if ((Test-Path -LiteralPath $Target) -and -not $Force) {
        throw "$Target already exists. Re-run with -Force to replace baseline outputs."
    }
}

$env:RUN_MODE = 'simulated_user'
$env:LM_STUDIO_URL = 'http://127.0.0.1:1234/v1'
$env:TROLL_MODEL = 'qwen/qwen3.5-2b'
$env:MAX_TOKENS = '1200'

foreach ($Number in '01','02','03','04','05') {
    $Target = [System.IO.Path]::GetFullPath((Join-Path $RunsRoot "run-$Number"))
    if (-not $Target.StartsWith($ResolvedRunsRoot + [System.IO.Path]::DirectorySeparatorChar)) {
        throw "Refusing to modify unexpected path: $Target"
    }
    if (Test-Path -LiteralPath $Target) { Remove-Item -LiteralPath $Target -Recurse -Force }
    New-Item -ItemType Directory -Path $Target | Out-Null

    Write-Host "===== run-$Number`: Qwen3.5-2B, thinking on, native Windows ====="
    [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ') | Set-Content -LiteralPath (Join-Path $Target 'started_at.txt')
    python (Join-Path $ProjectRoot 'game.py') $Target
    $GameExit = $LASTEXITCODE
    $GameExit | Set-Content -LiteralPath (Join-Path $Target 'game_exit_code.txt')
    [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ') | Set-Content -LiteralPath (Join-Path $Target 'finished_at.txt')
    python (Join-Path $ProjectRoot 'make_outputs.py') $Target
    if ($GameExit -ne 0 -or $LASTEXITCODE -ne 0) { throw "run-$Number failed." }
}

Write-Host '===== Summary ====='
foreach ($Number in '01','02','03','04','05') {
    $Reward = Get-Content -LiteralPath (Join-Path $RunsRoot "run-$Number\reward.json") -Raw
    Write-Host "run-$Number`: $($Reward -replace '\s','')"
}

