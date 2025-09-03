# Django Development Server with Auto-Reload Optimization
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   Django Auto-Reload Optimized" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan

# Önceki Python süreçlerini temizle
Write-Host "Cleaning up previous Python processes..." -ForegroundColor Yellow
try {
    Get-Process python -ErrorAction Stop | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
} catch {
    # Process yoksa devam et
}

# Migration kontrolü
Write-Host "Checking for pending migrations..." -ForegroundColor Yellow
$migrationCheck = & .\.venv\Scripts\python.exe manage.py showmigrations --plan 2>&1
if ($migrationCheck -match "\[ \]") {
    Write-Host "Applying pending migrations..." -ForegroundColor Green
    & .\.venv\Scripts\python.exe manage.py migrate
    Write-Host "Migrations applied successfully!" -ForegroundColor Green
} else {
    Write-Host "No pending migrations found." -ForegroundColor Green
}

# Environment değişkenlerini ayarla
$env:DJANGO_AUTORELOAD_POLL_INTERVAL = "0.5"
$env:PYTHONUNBUFFERED = "1"

# Sunucuyu başlat
Write-Host "Starting development server with fast reload..." -ForegroundColor Green
Write-Host "Server will be available at: http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Cyan

try {
    & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
} catch {
    Write-Host "Server stopped." -ForegroundColor Red
}

Read-Host "Press Enter to exit"
