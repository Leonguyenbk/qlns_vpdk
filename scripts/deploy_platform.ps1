<#
  Cài / cập nhật dịch vụ Windows cho PLATFORM (một tiến trình Waitress).
  KHÔNG đụng tới dịch vụ cũ (QLNS_Backend / QLNS_Nginx / server goiso).

  Dùng:
    powershell -File scripts\deploy_platform.ps1 -Port 5050
    powershell -File scripts\deploy_platform.ps1 -Port 5050 -Update   # chỉ build lại + restart

  Điều kiện: đã có backend\.env (DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY...),
  đã chạy  flask --app wsgi db upgrade  và các script di trú (xem docs/MIGRATION.md).
#>
param(
  [int]$Port = 5050,
  [string]$Root = (Split-Path -Parent $PSScriptRoot),
  [switch]$Update
)
$ErrorActionPreference = "Stop"
$nssm = "C:\ProgramData\chocolatey\lib\NSSM\tools\nssm.exe"
$svc  = "PLATFORM_Backend"
$be   = Join-Path $Root "backend"
$fe   = Join-Path $Root "frontend"
$py   = Join-Path $be ".venv\Scripts\python.exe"
$waitress = Join-Path $be ".venv\Scripts\waitress-serve.exe"

Write-Host "== Backend: venv + phụ thuộc ==" -ForegroundColor Cyan
if (-not (Test-Path $py)) { & python -m venv (Join-Path $be ".venv") }
& $py -m pip install -q --upgrade pip
& $py -m pip install -q -r (Join-Path $be "requirements.txt")

Write-Host "== DB migrate ==" -ForegroundColor Cyan
Push-Location $be; & (Join-Path $be ".venv\Scripts\flask.exe") --app wsgi db upgrade; Pop-Location

Write-Host "== Frontend: build ==" -ForegroundColor Cyan
Push-Location $fe
if (-not (Test-Path (Join-Path $fe "node_modules"))) { & npm ci } else { & npm ci }
& npm run build
Pop-Location

Write-Host "== Dịch vụ $svc (cổng $Port) ==" -ForegroundColor Cyan
$exists = (& $nssm status $svc 2>$null)
if ($exists) {
  & $nssm stop $svc
} else {
  & $nssm install $svc $waitress
}
& $nssm set $svc Application $waitress
& $nssm set $svc AppParameters "--host=0.0.0.0 --port=$Port --threads=48 wsgi:app"
& $nssm set $svc AppDirectory $be
& $nssm set $svc AppStdout (Join-Path $Root "logs\platform-out.log")
& $nssm set $svc AppStderr (Join-Path $Root "logs\platform-error.log")
& $nssm set $svc Start SERVICE_AUTO_START
New-Item -ItemType Directory -Force (Join-Path $Root "logs") | Out-Null
& $nssm start $svc
Start-Sleep -Seconds 4

try {
  $h = Invoke-RestMethod "http://127.0.0.1:$Port/api/health" -TimeoutSec 10
  Write-Host "OK  health: success=$($h.success) db=$($h.data.database)" -ForegroundColor Green
} catch {
  Write-Host "!! health lỗi: $($_.Exception.Message)" -ForegroundColor Red
  Get-Content (Join-Path $Root "logs\platform-error.log") -Tail 20
}
