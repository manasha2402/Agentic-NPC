# run_human.ps1 - Windows version of run_human.sh.
# USER TESTING mode: a person plays the knight in the terminal.
# Usage (PowerShell, in this folder):  .\run_human.ps1 P01
#        Gemini instead of Ollama:     .\run_human.ps1 P01 -Backend gemini
# If PowerShell blocks scripts, use:   .\run_human.cmd P01
# Output goes to runs\user-P01\ (trajectory.json, reward.json, config.json, survey.json).
# After the interview, save the notes there as interview_notes.md.
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$ParticipantId,
    [string]$Backend = $(if ($env:BACKEND) { $env:BACKEND } else { "ollama" })
)

Set-Location -LiteralPath $PSScriptRoot
$envArgs = @()
if (Test-Path -LiteralPath ".env") { $envArgs = @("--env-file", ".env") }   # .env only needed for Gemini

$out = Join-Path $PSScriptRoot "runs\user-$ParticipantId"
if (Test-Path -LiteralPath $out) {
    Write-Host "runs\user-$ParticipantId already exists - pick another participant id"
    exit 1
}
New-Item -ItemType Directory -Force -Path $out | Out-Null

docker build -q -t hint-fishing-test . | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "Docker build failed. Is Docker Desktop running?"; exit 1 }

docker run --rm -it @envArgs -e RUN_MODE=human -e "TROLL_BACKEND=$Backend" `
    -e "PARTICIPANT_ID=$ParticipantId" -v "${out}:/output" hint-fishing-test
