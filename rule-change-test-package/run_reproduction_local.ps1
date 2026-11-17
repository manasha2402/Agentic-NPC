$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$RunsRoot = Join-Path $ProjectRoot 'runs'
New-Item -ItemType Directory -Force -Path $RunsRoot | Out-Null

$Stamp = [DateTime]::Now.ToString('yyyyMMdd-HHmmss')
$Target = Join-Path $RunsRoot "reproduction-$Stamp"
New-Item -ItemType Directory -Path $Target | Out-Null

$env:RUN_MODE = 'simulated_user'
$env:LM_STUDIO_URL = 'http://127.0.0.1:1234/v1'
$env:TROLL_MODEL = 'qwen/qwen3.5-2b'
$env:MAX_TOKENS = '1200'

[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ') | Set-Content -LiteralPath (Join-Path $Target 'started_at.txt')
python (Join-Path $ProjectRoot 'game.py') $Target
$GameExit = $LASTEXITCODE
$GameExit | Set-Content -LiteralPath (Join-Path $Target 'game_exit_code.txt')
[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ') | Set-Content -LiteralPath (Join-Path $Target 'finished_at.txt')
python (Join-Path $ProjectRoot 'make_outputs.py') $Target
$ScoreExit = $LASTEXITCODE

if ($GameExit -ne 0 -or $ScoreExit -ne 0) { throw 'Reproduction run failed.' }
$Reward = Get-Content -LiteralPath (Join-Path $Target 'reward.json') -Raw
Write-Host "Reproduction complete: $Target"
Write-Host "Metrics: $($Reward -replace '\s','')"
