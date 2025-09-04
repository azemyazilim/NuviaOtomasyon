@echo off
REM Nuvia Otomasyon Hızlı Backup Batch Dosyası
REM Bu dosyayı çift tıklayarak hızlı backup alabilirsiniz

echo.
echo ==========================================
echo    Nuvia Otomasyon Hızlı Backup
echo ==========================================
echo.

cd /d "%~dp0"

echo 🔄 Backup oluşturuluyor...
echo.

py backup.py create "Hızlı backup - %date% %time%"

echo.
echo ==========================================
echo Backup tamamlandı! Bu pencereyi kapatabilirsiniz.
echo ==========================================
echo.

pause
