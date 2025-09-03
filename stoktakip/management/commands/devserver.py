"""
Gelişmiş development server komutu
Auto-reload optimizasyonları ile
"""
import os
import sys
from django.core.management.commands.runserver import Command as RunServerCommand
from django.conf import settings


class Command(RunServerCommand):
    help = 'Development server with enhanced auto-reload'
    
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--no-reload',
            action='store_false',
            dest='use_reloader',
            default=True,
            help='Disable auto-reloader.',
        )
        parser.add_argument(
            '--fast-reload',
            action='store_true',
            dest='fast_reload',
            default=False,
            help='Enable fast reload mode.',
        )
    
    def handle(self, *args, **options):
        # Fast reload modunu etkinleştir
        if options.get('fast_reload'):
            os.environ['DJANGO_AUTORELOAD_EXTRA_FILES'] = ''
            # Polling interval'i azalt
            os.environ['DJANGO_AUTORELOAD_POLL_INTERVAL'] = '0.5'
            self.stdout.write(
                self.style.SUCCESS('Fast reload mode enabled!')
            )
        
        # Migration kontrolü ve otomatik uygulama
        if options.get('use_reloader'):
            self.check_and_apply_migrations()
        
        super().handle(*args, **options)
    
    def check_and_apply_migrations(self):
        """Migration'ları kontrol et ve gerekirse uygula"""
        try:
            from django.core.management import execute_from_command_line
            from django.db.migrations.executor import MigrationExecutor
            from django.db import connection
            
            # Pending migration'ları kontrol et
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if plan:
                self.stdout.write(
                    self.style.WARNING(
                        f'{len(plan)} pending migration(s) found. Applying...'
                    )
                )
                # Migration'ları otomatik uygula
                execute_from_command_line(['manage.py', 'migrate', '--verbosity', '0'])
                self.stdout.write(
                    self.style.SUCCESS('Migrations applied successfully!')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Migration check failed: {e}')
            )
