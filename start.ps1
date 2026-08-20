param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [ValidateSet("start", "stop")]
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$RunDir = Join-Path $ProjectRoot ".run"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Stop-ManagedProcess {
    param([string]$Name)
    $pidFile = Join-Path $RunDir "$Name.pid"
    if (-not (Test-Path -LiteralPath $pidFile)) { return }
    $managedPid = (Get-Content -LiteralPath $pidFile -Raw).Trim()
    if ($managedPid -match '^\d+$' -and (Get-Process -Id ([int]$managedPid) -ErrorAction SilentlyContinue)) {
        & taskkill.exe /PID $managedPid /T /F | Out-Null
        Write-Host "[$Name] stopped (PID: $managedPid)"
    }
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
}

function Get-PortOwner {
    param([int]$Port)
    $line = netstat -ano -p tcp | Select-String -Pattern "^\s*TCP\s+\S+:$Port\s+\S+\s+LISTENING\s+(\d+)\s*$" | Select-Object -First 1
    if ($line -and $line.Matches.Count) { return [int]$line.Matches[0].Groups[1].Value }
    return $null
}

function Stop-Services {
    Stop-ManagedProcess -Name "frontend"
    Stop-ManagedProcess -Name "backend"
}

if ($Action -eq "stop") {
    Stop-Services
    exit 0
}

Stop-Services
foreach ($port in @($BackendPort, $FrontendPort)) {
    $ownerPid = Get-PortOwner -Port $port
    if ($ownerPid) {
        $owner = Get-Process -Id $ownerPid -ErrorAction SilentlyContinue
        $ownerName = if ($owner) { $owner.ProcessName } else { "unknown" }
        throw "Port $port is occupied by PID $ownerPid ($ownerName). Stop it or choose another port."
    }
}

$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $PythonExe)) {
    Write-Host "[Setup] Creating Python virtual environment..."
    & python -m venv (Join-Path $BackendDir ".venv")
    & $PythonExe -m pip install -r (Join-Path $BackendDir "requirements.txt")
}

if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "[Setup] Installing frontend dependencies..."
    Push-Location $FrontendDir
    try { & npm install } finally { Pop-Location }
}

$backendOut = Join-Path $RunDir "backend.out.log"
$backendErr = Join-Path $RunDir "backend.err.log"
$frontendOut = Join-Path $RunDir "frontend.out.log"
$frontendErr = Join-Path $RunDir "frontend.err.log"

$backend = Start-Process -FilePath $PythonExe `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", $BackendPort, "--reload") `
    -WorkingDirectory $BackendDir -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr `
    -WindowStyle Hidden -PassThru

$npmCommand = (Get-Command npm.cmd -ErrorAction Stop).Source
$previousProxyTarget = $env:VITE_API_PROXY_TARGET
$env:VITE_API_PROXY_TARGET = "http://127.0.0.1:$BackendPort"
$frontend = Start-Process -FilePath $npmCommand `
    -ArgumentList @("run", "dev", "--", "--host", "0.0.0.0", "--port", $FrontendPort) `
    -WorkingDirectory $FrontendDir -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr `
    -WindowStyle Hidden -PassThru
if ($null -eq $previousProxyTarget) {
    Remove-Item Env:VITE_API_PROXY_TARGET -ErrorAction SilentlyContinue
} else {
    $env:VITE_API_PROXY_TARGET = $previousProxyTarget
}

Set-Content -LiteralPath (Join-Path $RunDir "backend.pid") -Value $backend.Id
Set-Content -LiteralPath (Join-Path $RunDir "frontend.pid") -Value $frontend.Id
Start-Sleep -Seconds 3

foreach ($service in @(@("Backend", $backend, $backendErr), @("Frontend", $frontend, $frontendErr))) {
    if ($service[1].HasExited) { throw "$($service[0]) failed to start. See $($service[2])" }
}

Write-Host "[Backend] http://127.0.0.1:$BackendPort (PID: $($backend.Id))"
Write-Host "[Frontend] http://127.0.0.1:$FrontendPort (PID: $($frontend.Id))"
Write-Host "[Logs] $RunDir"
