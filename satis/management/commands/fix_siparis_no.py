from django.core.management.base import BaseCommand
from satis.models import Satis, SiparisNumarasi
from django.db import transaction
import datetime


class Command(BaseCommand):
    help = 'Sipariş numaralarını düzelt ve yeniden oluştur'

    def handle(self, *args, **options):
        self.stdout.write('Sipariş numaraları düzeltiliyor...')
        
        # Önce tüm sipariş numarası sayaçlarını sıfırla
        SiparisNumarasi.objects.all().delete()
        
        # Yinelenen sipariş numaralarını bul
        from django.db.models import Count
        duplicates = Satis.objects.values('siparis_no').annotate(
            count=Count('siparis_no')
        ).filter(count__gt=1)
        
        self.stdout.write(f'Bulunan yinelenen sipariş numaraları: {duplicates.count()}')
        
        # Her yinelenen grup için işlem yap
        for duplicate in duplicates:
            siparis_no = duplicate['siparis_no']
            satislar = Satis.objects.filter(siparis_no=siparis_no).order_by('siparis_tarihi')
            
            self.stdout.write(f'Düzeltiliyor: {siparis_no} ({duplicate["count"]} adet)')
            
            # İlk satışı olduğu gibi bırak, diğerlerine yeni numara ata
            for i, satis in enumerate(satislar):
                if i > 0:  # İlkini atla
                    # Tarihe göre yeni sipariş numarası oluştur
                    tarih = satis.siparis_tarihi.date()
                    
                    # O günün sayacını al veya oluştur
                    obj, created = SiparisNumarasi.objects.get_or_create(
                        yil=tarih.year,
                        ay=tarih.month,
                        gun=tarih.day,
                        defaults={'sayac': 0}
                    )
                    
                    obj.sayac += 1
                    obj.save()
                    
                    yeni_no = f"SP{tarih.strftime('%Y%m%d')}{obj.sayac:04d}"
                    
                    # Yeni numaranın unique olduğundan emin ol
                    while Satis.objects.filter(siparis_no=yeni_no).exists():
                        obj.sayac += 1
                        obj.save()
                        yeni_no = f"SP{tarih.strftime('%Y%m%d')}{obj.sayac:04d}"
                    
                    # Raw SQL ile güncelle (save() metodunu bypass et)
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE satis_satis SET siparis_no = %s WHERE id = %s",
                            [yeni_no, satis.id]
                        )
                    
                    self.stdout.write(f'  ID {satis.id}: {siparis_no} -> {yeni_no}')
        
        self.stdout.write(
            self.style.SUCCESS('Sipariş numaraları başarıyla düzeltildi!')
        )
