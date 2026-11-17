$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { throw 'Python 3.11 or newer was not found on PATH.' }

$VersionText = & python --version 2>&1
if ($LASTEXITCODE -ne 0) { throw 'Python could not be executed.' }
Write-Host $VersionText

$Required = @(
    'game.py', 'make_outputs.py', 'troll_system_prompt.md', 'troll_opening.txt',
    'simulated_user_script.txt', 'participant_briefing.md', 'survey.py',
    'survey_questions.json', 'interview_notes_template.md'
)
foreach ($File in $Required) {
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot $File))) {
        throw "Required package file is missing: $File"
    }
}

try {
    $Models = Invoke-RestMethod 'http://127.0.0.1:1234/v1/models' -TimeoutSec 10
} catch {
    throw "LM Studio API is not reachable. Run .\setup_lmstudio.ps1 first. Details: $_"
}
if ($Models.data.id -notcontains 'qwen/qwen3.5-2b') {
    throw "LM Studio is running but qwen/qwen3.5-2b is not loaded. Run .\setup_lmstudio.ps1."
}

foreach ($Number in '01','02','03','04','05') {
    foreach ($File in 'trajectory.json','reward.json','config.json') {
        $Path = Join-Path $ProjectRoot "runs\run-$Number\$File"
        if (-not (Test-Path -LiteralPath $Path)) { throw "Missing baseline output: $Path" }
        Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json | Out-Null
    }
}

Write-Host 'Verification passed: files, baseline outputs, Python, API, and model are ready.'
