# Nuvia Otomasyon Backup PowerShell Script
# Bu script backup.py'yi daha kolay kullanmanızı sağlar

param(
    [Parameter(Position=0)]
    [string]$Action = "help",
    
    [Parameter(Position=1)]
    [string]$Message = ""
)

$BackupScript = "backup.py"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Proje dizinine geç
Set-Location $ProjectRoot

function Show-Help {
    Write-Host "Nuvia Otomasyon Backup Sistemi" -ForegroundColor Cyan
    Write-Host "=" * 40 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Kullanım:" -ForegroundColor Yellow
    Write-Host "  .\backup.ps1 create [mesaj]    - Backup oluştur" -ForegroundColor White
    Write-Host "  .\backup.ps1 git [mesaj]       - Sadece Git backup" -ForegroundColor White
    Write-Host "  .\backup.ps1 file              - Sadece dosya backup" -ForegroundColor White
    Write-Host "  .\backup.ps1 list              - Backup'ları listele" -ForegroundColor White
    Write-Host "  .\backup.ps1 restore <dosya>   - Dosya backup'ından geri yükle" -ForegroundColor White
    Write-Host ""
    Write-Host "Örnekler:" -ForegroundColor Yellow
    Write-Host "  .\backup.ps1 create `"Form tasarımı düzeltildi`"" -ForegroundColor Green
    Write-Host "  .\backup.ps1 create" -ForegroundColor Green
    Write-Host "  .\backup.ps1 list" -ForegroundColor Green
    Write-Host ""
    Write-Host "Hızlı Komutlar:" -ForegroundColor Yellow
    Write-Host "  .\backup.ps1                   - Bu yardımı göster" -ForegroundColor White
    Write-Host "  .\backup.ps1 quick             - Hızlı backup (git + file)" -ForegroundColor Green
}

switch ($Action.ToLower()) {
    "help" { 
        Show-Help 
    }
    "create" {
        if ($Message) {
            py $BackupScript create $Message
        } else {
            py $BackupScript create
        }
    }
    "quick" {
        Write-Host "🚀 Hızlı backup başlatılıyor..." -ForegroundColor Yellow
        if ($Message) {
            py $BackupScript create $Message
        } else {
            py $BackupScript create
        }
    }
    "git" {
        if ($Message) {
            py $BackupScript git $Message
        } else {
            py $BackupScript git
        }
    }
    "file" {
        py $BackupScript file
    }
    "list" {
        py $BackupScript list
    }
    "restore" {
        if ($Message) {
            py $BackupScript restore $Message
        } else {
            Write-Host "❌ Backup dosya adını belirtiniz!" -ForegroundColor Red
            Write-Host "Örnek: .\backup.ps1 restore nuvia_backup_20250904_200000.zip" -ForegroundColor Yellow
        }
    }
    default {
        Write-Host "❌ Bilinmeyen komut: $Action" -ForegroundColor Red
        Write-Host ""
        Show-Help
    }
}
