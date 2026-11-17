param([switch]$Force)

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

docker build -t rule-change-test $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw 'Docker build failed.' }

foreach ($Number in '01','02','03','04','05') {
    $Target = [System.IO.Path]::GetFullPath((Join-Path $RunsRoot "run-$Number"))
    if (-not $Target.StartsWith($ResolvedRunsRoot + [System.IO.Path]::DirectorySeparatorChar)) {
        throw "Refusing to modify unexpected path: $Target"
    }
    if (Test-Path -LiteralPath $Target) { Remove-Item -LiteralPath $Target -Recurse -Force }
    New-Item -ItemType Directory -Path $Target | Out-Null
    Write-Host "===== run-$Number`: Qwen3.5-2B, thinking on ====="
    docker run --rm --mount "type=bind,source=$Target,target=/output" rule-change-test
    if ($LASTEXITCODE -ne 0) { throw "run-$Number failed." }
}

Write-Host '===== Summary ====='
foreach ($Number in '01','02','03','04','05') {
    $Reward = Get-Content -LiteralPath (Join-Path $RunsRoot "run-$Number\reward.json") -Raw
    Write-Host "run-$Number`: $($Reward -replace '\s','')"
}

