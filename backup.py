#!/usr/bin/env python3
"""
Nuvia Otomasyon Backup Sistemi
Bu script projenin hem Git commit'i hem de dosya yedeklemesi yapabilir.
"""

import os
import sys
import datetime
import shutil
import zipfile
import subprocess
from pathlib import Path

# Proje ana dizini
PROJECT_ROOT = Path(__file__).parent
BACKUP_DIR = PROJECT_ROOT / "backups"

def create_git_backup(message=None):
    """Git commit ile backup oluştur"""
    try:
        # Git statusunu kontrol et
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        if not result.stdout.strip():
            print("✅ Hiç değişiklik yok, backup gerekmiyor.")
            return False
            
        # Değişiklikleri stage'e ekle
        subprocess.run(['git', 'add', '.'], cwd=PROJECT_ROOT, check=True)
        
        # Commit mesajı oluştur
        if not message:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Backup: {timestamp}"
        
        # Commit yap
        subprocess.run(['git', 'commit', '-m', message], cwd=PROJECT_ROOT, check=True)
        
        print(f"✅ Git backup oluşturuldu: {message}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git backup hatası: {e}")
        return False
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        return False

def create_file_backup():
    """Dosya tabanlı backup oluştur"""
    try:
        # Backup dizinini oluştur
        BACKUP_DIR.mkdir(exist_ok=True)
        
        # Timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"nuvia_backup_{timestamp}.zip"
        backup_path = BACKUP_DIR / backup_filename
        
        # Yedeklenecek dosya ve klasörler
        items_to_backup = [
            'templates',
            'static',
            'urun',
            'satis',
            'musteri',
            'kullanici',
            'gider',
            'hediye',
            'rapor',
            'log',
            'stoktakip',
            'manage.py',
            'requirements.txt',
            'db.sqlite3',
        ]
        
        # Zip dosyası oluştur
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in items_to_backup:
                item_path = PROJECT_ROOT / item
                if item_path.exists():
                    if item_path.is_file():
                        zipf.write(item_path, item_path.name)
                    else:
                        for file_path in item_path.rglob('*'):
                            if file_path.is_file():
                                # Relative path hesapla
                                arcname = file_path.relative_to(PROJECT_ROOT)
                                zipf.write(file_path, arcname)
        
        # Dosya boyutunu hesapla
        size_mb = backup_path.stat().st_size / (1024 * 1024)
        
        print(f"✅ Dosya backup'ı oluşturuldu: {backup_filename}")
        print(f"📁 Konum: {backup_path}")
        print(f"📊 Boyut: {size_mb:.2f} MB")
        
        # Eski backup'ları temizle (son 10'unu sakla)
        cleanup_old_backups()
        
        return True
        
    except Exception as e:
        print(f"❌ Dosya backup hatası: {e}")
        return False

def cleanup_old_backups(keep_count=10):
    """Eski backup dosyalarını temizle"""
    try:
        if not BACKUP_DIR.exists():
            return
            
        # Backup dosyalarını listele
        backup_files = list(BACKUP_DIR.glob("nuvia_backup_*.zip"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Fazla olanları sil
        for backup_file in backup_files[keep_count:]:
            backup_file.unlink()
            print(f"🗑️ Eski backup silindi: {backup_file.name}")
            
    except Exception as e:
        print(f"⚠️ Temizlik hatası: {e}")

def list_backups():
    """Mevcut backup'ları listele"""
    print("📋 Mevcut Backup'lar:")
    print("-" * 50)
    
    # Git commit'leri
    try:
        result = subprocess.run(['git', 'log', '--oneline', '-10'], 
                              capture_output=True, text=True, cwd=PROJECT_ROOT)
        if result.stdout:
            print("🔄 Git Commit'leri:")
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
            print()
    except:
        pass
    
    # Dosya backup'ları
    if BACKUP_DIR.exists():
        backup_files = list(BACKUP_DIR.glob("nuvia_backup_*.zip"))
        if backup_files:
            print("📁 Dosya Backup'ları:")
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            for backup_file in backup_files:
                mtime = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                size_mb = backup_file.stat().st_size / (1024 * 1024)
                print(f"  {backup_file.name} - {mtime.strftime('%Y-%m-%d %H:%M:%S')} - {size_mb:.2f} MB")
        else:
            print("📁 Dosya backup'ı bulunamadı.")
    else:
        print("📁 Backup dizini bulunamadı.")

def restore_from_file_backup(backup_filename):
    """Dosya backup'ından geri yükle"""
    try:
        backup_path = BACKUP_DIR / backup_filename
        if not backup_path.exists():
            print(f"❌ Backup dosyası bulunamadı: {backup_filename}")
            return False
        
        print(f"⚠️ Dikkat: Bu işlem mevcut dosyaları silip backup'tan geri yükleyecek!")
        response = input("Devam etmek istiyor musunuz? (evet/hayır): ")
        
        if response.lower() not in ['evet', 'e', 'yes', 'y']:
            print("❌ İşlem iptal edildi.")
            return False
        
        # Backup'ı aç ve geri yükle
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(PROJECT_ROOT)
        
        print(f"✅ Backup geri yüklendi: {backup_filename}")
        return True
        
    except Exception as e:
        print(f"❌ Geri yükleme hatası: {e}")
        return False

def main():
    """Ana fonksiyon"""
    if len(sys.argv) < 2:
        print("Nuvia Otomasyon Backup Sistemi")
        print("=" * 40)
        print("Kullanım:")
        print("  py backup.py create [mesaj]    - Backup oluştur")
        print("  py backup.py git [mesaj]       - Sadece Git backup")
        print("  py backup.py file              - Sadece dosya backup")
        print("  py backup.py list              - Backup'ları listele")
        print("  py backup.py restore <dosya>   - Dosya backup'ından geri yükle")
        print()
        print("Örnekler:")
        print("  py backup.py create \"Form tasarımı düzeltildi\"")
        print("  py backup.py create")
        print("  py backup.py list")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        message = sys.argv[2] if len(sys.argv) > 2 else None
        print("🔄 Backup oluşturuluyor...")
        git_success = create_git_backup(message)
        file_success = create_file_backup()
        
        if git_success or file_success:
            print("✅ Backup işlemi tamamlandı!")
        else:
            print("❌ Backup işlemi başarısız!")
    
    elif command == "git":
        message = sys.argv[2] if len(sys.argv) > 2 else None
        create_git_backup(message)
    
    elif command == "file":
        create_file_backup()
    
    elif command == "list":
        list_backups()
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ Backup dosya adını belirtiniz!")
            return
        restore_from_file_backup(sys.argv[2])
    
    else:
        print(f"❌ Bilinmeyen komut: {command}")

if __name__ == "__main__":
    main()
