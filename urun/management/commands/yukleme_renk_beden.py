from django.core.management.base import BaseCommand
from urun.models import Renk, Beden


class Command(BaseCommand):
    help = 'Renk ve beden verilerini yükler'

    def handle(self, *args, **options):
        # Ana renkler
        renkler = [
            ('Kırmızı', 'K', '#FF0000', 1),
            ('Mavi', 'M', '#0000FF', 2),
            ('Yeşil', 'Y', '#00FF00', 3),
            ('Siyah', 'S', '#000000', 4),
            ('Beyaz', 'B', '#FFFFFF', 5),
            ('Sarı', 'A', '#FFFF00', 6),
            ('Mor', 'R', '#800080', 7),
            ('Pembe', 'P', '#FFC0CB', 8),
            ('Turuncu', 'T', '#FFA500', 9),
            ('Gri', 'G', '#808080', 10),
            ('Lacivert', 'L', '#000080', 11),
            ('Bordo', 'O', '#800000', 12),
            ('Kahverengi', 'H', '#8B4513', 13),
            ('Bej', 'J', '#F5F5DC', 14),
            ('Krem', 'E', '#FFFDD0', 15),
        ]

        self.stdout.write('Renkler ekleniyor...')
        for ad, kod, hex_kod, sira in renkler:
            renk, created = Renk.objects.get_or_create(
                kod=kod,
                defaults={
                    'ad': ad,
                    'hex_kod': hex_kod,
                    'sira': sira,
                    'aktif': True
                }
            )
            if created:
                self.stdout.write(f'✅ {ad} ({kod}) eklendi')
            else:
                self.stdout.write(f'⏭️  {ad} ({kod}) zaten mevcut')

        # Harf bedenler
        harf_bedenler = [
            ('XS', '1', 1),
            ('S', '2', 2),
            ('M', '3', 3),
            ('L', '4', 4),
            ('XL', '5', 5),
            ('XXL', '6', 6),
            ('XXXL', '7', 7),
        ]

        self.stdout.write('\nHarf bedenler ekleniyor...')
        for ad, kod, sira in harf_bedenler:
            beden, created = Beden.objects.get_or_create(
                kod=kod,
                defaults={
                    'ad': ad,
                    'tip': 'harf',
                    'sira': sira,
                    'aktif': True
                }
            )
            if created:
                self.stdout.write(f'✅ {ad} ({kod}) eklendi')
            else:
                self.stdout.write(f'⏭️  {ad} ({kod}) zaten mevcut')

        # Rakam bedenler (ayakkabı, pantolon vs)
        rakam_bedenler = [
            ('34', 'A', 20),
            ('36', 'B', 21),
            ('38', 'C', 22),
            ('40', 'D', 23),
            ('42', 'E', 24),
            ('44', 'F', 25),
            ('46', 'G', 26),
            ('48', 'H', 27),
            ('50', 'I', 28),
        ]

        self.stdout.write('\nRakam bedenler ekleniyor...')
        for ad, kod, sira in rakam_bedenler:
            beden, created = Beden.objects.get_or_create(
                kod=kod,
                defaults={
                    'ad': ad,
                    'tip': 'rakam',
                    'sira': sira,
                    'aktif': True
                }
            )
            if created:
                self.stdout.write(f'✅ {ad} ({kod}) eklendi')
            else:
                self.stdout.write(f'⏭️  {ad} ({kod}) zaten mevcut')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Başarıyla tamamlandı!'
                f'\n📊 Toplam Renk: {Renk.objects.count()}'
                f'\n📊 Toplam Beden: {Beden.objects.count()}'
            )
        )
