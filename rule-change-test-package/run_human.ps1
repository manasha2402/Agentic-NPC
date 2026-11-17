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
$Target = [System.IO.Path]::GetFullPath($Target)

docker build -q -t rule-change-test $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw 'Docker build failed.' }
docker run --rm -it `
    -e RUN_MODE=human `
    -e "PARTICIPANT_ID=$ParticipantId" `
    --mount "type=bind,source=$Target,target=/output" `
    rule-change-test
if ($LASTEXITCODE -ne 0) { throw 'Human test run failed.' }

