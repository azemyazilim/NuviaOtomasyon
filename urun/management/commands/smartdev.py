"""
Smart Development Server
Otomatik migration uygulama ve optimized auto-reload ile sunucu başlatma
"""
from django.core.management.base import BaseCommand
from django.core.management import execute_from_command_line, call_command
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
import os
import sys


class Command(BaseCommand):
    help = 'Smart development server with auto-migrations and optimized reload'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=str,
            default='8000',
            help='Port to run the server on (default: 8000)',
        )
        parser.add_argument(
            '--host',
            type=str,
            default='127.0.0.1',
            help='Host to run the server on (default: 127.0.0.1)',
        )
        parser.add_argument(
            '--no-migrations',
            action='store_true',
            help='Skip automatic migration check and apply',
        )
        parser.add_argument(
            '--force-migrations',
            action='store_true',
            help='Force apply all migrations even if no pending ones',
        )
    
    def handle(self, *args, **options):
        port = options['port']
        host = options['host']
        
        # ASCII Art Banner
        self.stdout.write(self.style.SUCCESS("""
╔══════════════════════════════════════╗
║        Django Smart Dev Server       ║
║     Auto-Migrations & Fast Reload    ║
╚══════════════════════════════════════╝
        """))
        
        # Migration kontrolü ve uygulama
        if not options['no_migrations']:
            self.handle_migrations(options['force_migrations'])
        
        # Environment optimizasyonları
        self.optimize_environment()
        
        # Sunucuyu başlat
        self.stdout.write(
            self.style.HTTP_INFO(f'🚀 Starting smart dev server at http://{host}:{port}/')
        )
        self.stdout.write(
            self.style.WARNING('💡 Press Ctrl+C to stop the server')
        )
        
        try:
            call_command('runserver', f'{host}:{port}')
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\n✅ Server stopped gracefully'))
    
    def handle_migrations(self, force=False):
        """Migration'ları kontrol et ve uygula"""
        try:
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if plan or force:
                if plan:
                    self.stdout.write(
                        self.style.WARNING(f'📦 Found {len(plan)} pending migration(s)')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('🔄 Force applying migrations...')
                    )
                
                self.stdout.write('⏳ Applying migrations...')
                call_command('migrate', verbosity=1, interactive=False)
                self.stdout.write(self.style.SUCCESS('✅ Migrations applied successfully!'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ No pending migrations found'))
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Migration error: {e}')
            )
            self.stdout.write(
                self.style.WARNING('⚠️  Continuing without migrations...')
            )
    
    def optimize_environment(self):
        """Development environment optimizasyonları"""
        optimizations = {
            'DJANGO_AUTORELOAD_POLL_INTERVAL': '0.5',
            'PYTHONUNBUFFERED': '1',
            'DJANGO_DEBUG': '1',
        }
        
        self.stdout.write('⚙️  Applying development optimizations...')
        for key, value in optimizations.items():
            os.environ[key] = value
            self.stdout.write(f'   • {key}={value}')
        
        self.stdout.write(self.style.SUCCESS('✅ Environment optimized for development'))
