param([switch]$DockerAccess)

$ErrorActionPreference = 'Stop'

$LmsCommand = Get-Command lms -ErrorAction SilentlyContinue
if ($LmsCommand) {
    $Lms = $LmsCommand.Source
} else {
    $Fallback = Join-Path $env:USERPROFILE '.lmstudio\bin\lms.exe'
    if (-not (Test-Path -LiteralPath $Fallback)) {
        throw @'
LM Studio's `lms` command was not found.
Install and open LM Studio, enable its CLI integration, then open a new PowerShell window.
Download: https://lmstudio.ai/download
'@
    }
    $Lms = $Fallback
}

function Invoke-Lms {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
    & $Lms @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "LM Studio command failed: lms $($Arguments -join ' ')"
    }
}

Write-Host 'Downloading Qwen3.5 2B Q4_K_M if needed...'
Invoke-Lms get 'qwen/qwen3.5-2b@q4_k_m' --gguf --yes

$BindAddress = if ($DockerAccess) { '0.0.0.0' } else { '127.0.0.1' }
if ($DockerAccess) {
    Write-Host 'Restarting the LM Studio server with Docker-accessible binding...'
    & $Lms server stop 2>$null
    Invoke-Lms server start --port 1234 --bind $BindAddress
} else {
    try {
        Invoke-RestMethod 'http://127.0.0.1:1234/v1/models' -TimeoutSec 3 | Out-Null
        Write-Host 'LM Studio server is already running.'
    } catch {
        Write-Host 'Starting the LM Studio server...'
        Invoke-Lms server start --port 1234 --bind $BindAddress
    }
}

$Available = $null
for ($Attempt = 0; $Attempt -lt 20; $Attempt++) {
    try {
        $Available = Invoke-RestMethod 'http://127.0.0.1:1234/v1/models' -TimeoutSec 3
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $Available) { throw 'LM Studio API did not become ready on port 1234.' }

if ($Available.data.id -notcontains 'qwen/qwen3.5-2b') {
    Write-Host 'Loading Qwen3.5 2B with the required API identifier and context...'
    Invoke-Lms load 'qwen/qwen3.5-2b' --context-length 8192 --gpu max --identifier 'qwen/qwen3.5-2b' --yes
}

for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
    $Available = Invoke-RestMethod 'http://127.0.0.1:1234/v1/models' -TimeoutSec 5
    if ($Available.data.id -contains 'qwen/qwen3.5-2b') {
        Write-Host 'Setup complete: qwen/qwen3.5-2b is available at http://127.0.0.1:1234/v1'
        exit 0
    }
    Start-Sleep -Seconds 1
}

throw 'The model was loaded but was not advertised by the LM Studio API.'
