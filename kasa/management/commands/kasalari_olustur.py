from django.core.management.base import BaseCommand
from kasa.models import Kasa


class Command(BaseCommand):
    help = 'Başlangıç kasalarını oluşturur'

    def handle(self, *args, **options):
        # Nakit kasası
        nakit_kasa, created = Kasa.objects.get_or_create(
            ad='Ana Nakit Kasası',
            tip='nakit',
            defaults={
                'aciklama': 'Ana nakit kasası',
                'aktif': True
            }
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Nakit kasası oluşturuldu: {nakit_kasa.ad}')
            )
        else:
            self.stdout.write(f'Nakit kasası zaten mevcut: {nakit_kasa.ad}')

        # POS kredi kartı kasası
        pos_kasa, created = Kasa.objects.get_or_create(
            ad='POS Kredi Kartı',
            tip='pos',
            defaults={
                'aciklama': 'POS ile kredi kartı tahsilatları',
                'aktif': True
            }
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'POS kasası oluşturuldu: {pos_kasa.ad}')
            )
        else:
            self.stdout.write(f'POS kasası zaten mevcut: {pos_kasa.ad}')

        # Harcama kredi kartı kasası
        kart_kasa, created = Kasa.objects.get_or_create(
            ad='Harcama Kredi Kartı',
            tip='kart',
            defaults={
                'aciklama': 'Harcamalar için kredi kartı',
                'aktif': True
            }
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Kredi kartı kasası oluşturuldu: {kart_kasa.ad}')
            )
        else:
            self.stdout.write(f'Kredi kartı kasası zaten mevcut: {kart_kasa.ad}')

        # Banka havale kasası
        banka_kasa, created = Kasa.objects.get_or_create(
            ad='Banka Havale',
            tip='banka',
            defaults={
                'aciklama': 'Banka havale/EFT tahsilatları',
                'aktif': True
            }
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Banka kasası oluşturuldu: {banka_kasa.ad}')
            )
        else:
            self.stdout.write(f'Banka kasası zaten mevcut: {banka_kasa.ad}')

        self.stdout.write(
            self.style.SUCCESS('Tüm kasalar hazır!')
        )
