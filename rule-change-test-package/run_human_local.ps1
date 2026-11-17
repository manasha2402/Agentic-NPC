param(
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^[A-Za-z0-9_-]+$')]
    [string]$ParticipantId
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$Target = Join-Path $ProjectRoot "runs\user-$ParticipantId"
if (Test-Path -LiteralPath $Target) { throw "$Target already exists; choose another participant ID." }
New-Item -ItemType Directory -Path $Target | Out-Null

$env:RUN_MODE = 'human'
$env:LM_STUDIO_URL = 'http://127.0.0.1:1234/v1'
$env:TROLL_MODEL = 'qwen/qwen3.5-2b'
$env:MAX_TOKENS = '1200'
$env:PARTICIPANT_ID = $ParticipantId

[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ') | Set-Content -LiteralPath (Join-Path $Target 'started_at.txt')
python (Join-Path $ProjectRoot 'game.py') $Target
$GameExit = $LASTEXITCODE
$GameExit | Set-Content -LiteralPath (Join-Path $Target 'game_exit_code.txt')
[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ') | Set-Content -LiteralPath (Join-Path $Target 'finished_at.txt')
python (Join-Path $ProjectRoot 'make_outputs.py') $Target
if ($GameExit -ne 0 -or $LASTEXITCODE -ne 0) { throw 'Human test conversation failed.' }
python (Join-Path $ProjectRoot 'survey.py') $Target
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'interview_notes_template.md') -Destination (Join-Path $Target 'interview_notes.md')

