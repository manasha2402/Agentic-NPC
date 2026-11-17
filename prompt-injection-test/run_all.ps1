# run_all.ps1 - Windows version of run_all.sh.
# Builds the image and runs all 5 episodes (run-01 .. run-05), then prints rewards.
# Usage (PowerShell, in this folder):  .\run_all.ps1
#        Gemini instead of Ollama:     .\run_all.ps1 -Backend gemini   (needs .env with GEMINI_API_KEY)
# If PowerShell blocks scripts, use run_all.cmd instead (it bypasses the policy for this script only).
param([string]$Backend = $(if ($env:BACKEND) { $env:BACKEND } else { "ollama" }))

Set-Location -LiteralPath $PSScriptRoot
$envArgs = @()
if (Test-Path -LiteralPath ".env") { $envArgs = @("--env-file", ".env") }   # .env only needed for Gemini

docker build -t prompt-injection-test .
if ($LASTEXITCODE -ne 0) { Write-Host "Docker build failed. Is Docker Desktop running?"; exit 1 }

$runs = @("01", "02", "03", "04", "05")
foreach ($i in $runs) {
    $out = Join-Path $PSScriptRoot "runs\run-$i"
    if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    Write-Host "===== run-$i ($Backend) ====="
    docker run --rm @envArgs -e "TROLL_BACKEND=$Backend" -v "${out}:/output" prompt-injection-test
}

Write-Host ""
Write-Host "===== Summary ====="
foreach ($i in $runs) {
    $reward = Join-Path $PSScriptRoot "runs\run-$i\reward.json"
    if (Test-Path -LiteralPath $reward) {
        $text = (Get-Content -LiteralPath $reward -Raw) -replace '\s', ''
        Write-Host "run-${i}: $text"
    } else {
        Write-Host "run-${i}: MISSING"
    }
}
