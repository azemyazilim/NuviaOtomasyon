from django.apps import AppConfig
import os


class StoktakipConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stoktakip'
    
    def ready(self):
        """Uygulama hazır olduğunda çalışır"""
        # Development ortamında auto-reload optimizasyonları
        if os.environ.get('RUN_MAIN') != 'true':  # Sadece bir kez çalışsın
            return
            
        # Auto-reload ayarları
        if hasattr(self, 'settings') and getattr(self.settings, 'DEBUG', False):
            self.optimize_autoreload()
    
    def optimize_autoreload(self):
        """Auto-reload optimizasyonları"""
        try:
            import django.utils.autoreload as autoreload
            
            # Polling interval'i optimize et
            if hasattr(autoreload, 'StatReloader'):
                original_poll_interval = getattr(autoreload.StatReloader, 'POLL_INTERVAL', 1)
                autoreload.StatReloader.POLL_INTERVAL = 0.5
                print(f"Auto-reload polling interval optimized: {original_poll_interval}s -> 0.5s")
                
        except Exception as e:
            print(f"Auto-reload optimization failed: {e}")
