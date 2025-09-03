from django.db import models
from django.conf import settings
from django.utils import timezone
from .models import Musteri


class Tahsilat(models.Model):
    """Müşteri tahsilat kayıtları"""
    TAHSILAT_TIPI = [
        ('nakit', 'Nakit'),
        ('kart', 'Kart'),
        ('havale', 'Havale/EFT'),
        ('cek', 'Çek'),
        ('senet', 'Senet'),
    ]
    
    # Ana bilgiler
    musteri = models.ForeignKey(Musteri, on_delete=models.CASCADE, verbose_name="Müşteri")
    tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tahsilat Tutarı")
    tahsilat_tipi = models.CharField(max_length=20, choices=TAHSILAT_TIPI, verbose_name="Tahsilat Tipi")
    
    # Tarih bilgileri
    tahsilat_tarihi = models.DateTimeField(default=timezone.now, verbose_name="Tahsilat Tarihi")
    
    # Çek/Senet için ek bilgiler
    vade_tarihi = models.DateField(null=True, blank=True, verbose_name="Vade Tarihi")
    cek_senet_no = models.CharField(max_length=50, null=True, blank=True, verbose_name="Çek/Senet No")
    banka = models.CharField(max_length=100, null=True, blank=True, verbose_name="Banka")
    
    # Havale/EFT için
    referans_no = models.CharField(max_length=100, null=True, blank=True, verbose_name="Referans No")
    
    # Notlar
    aciklama = models.TextField(null=True, blank=True, verbose_name="Açıklama")
    
    # İşlem bilgileri
    tahsilat_no = models.CharField(max_length=20, unique=True, verbose_name="Tahsilat No")
    tahsilat_eden = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Tahsilat Eden")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    
    # Durum
    DURUM_SECENEKLERI = [
        ('tahsil_edildi', 'Tahsil Edildi'),
        ('beklemede', 'Beklemede'), # Çek/senet için
        ('iptal', 'İptal'),
        ('iade', 'İade'),
    ]
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='tahsil_edildi', verbose_name="Durum")
    
    class Meta:
        verbose_name = "Tahsilat"
        verbose_name_plural = "Tahsilatlar"
        ordering = ['-tahsilat_tarihi']
    
    def __str__(self):
        return f"{self.tahsilat_no} - {self.musteri} - {self.tutar}₺"
    
    def save(self, *args, **kwargs):
        # Tahsilat numarası oluştur
        if not self.tahsilat_no:
            import datetime
            today = datetime.date.today()
            count = Tahsilat.objects.filter(olusturma_tarihi__date=today).count() + 1
            self.tahsilat_no = f"T{today.strftime('%Y%m%d')}{count:04d}"
        
        # İlk kayıt ise müşteri bakiyesini güncelle
        if not self.pk and self.durum == 'tahsil_edildi':
            self.musteri.acik_hesap_bakiye -= self.tutar
            self.musteri.save()
        
        super().save(*args, **kwargs)


class TahsilatDetay(models.Model):
    """Tahsilat hangi satışlara ait"""
    tahsilat = models.ForeignKey(Tahsilat, on_delete=models.CASCADE, related_name='detaylar', verbose_name="Tahsilat")
    satis_id = models.PositiveIntegerField(verbose_name="Satış ID")
    odenen_tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ödenen Tutar")
    
    class Meta:
        verbose_name = "Tahsilat Detay"
        verbose_name_plural = "Tahsilat Detayları"
    
    def __str__(self):
        return f"{self.tahsilat.tahsilat_no} - Satış #{self.satis_id} - {self.odenen_tutar}₺"


class BorcAlacakHareket(models.Model):
    """Müşteri borç-alacak hareketleri"""
    HAREKET_TIPI = [
        ('borc', 'Borç'),  # Satış yapıldığında
        ('alacak', 'Alacak'),  # Tahsilat yapıldığında
        ('duzeltme', 'Düzeltme'),  # Manuel düzeltme
    ]
    
    musteri = models.ForeignKey(Musteri, on_delete=models.CASCADE, verbose_name="Müşteri")
    hareket_tipi = models.CharField(max_length=20, choices=HAREKET_TIPI, verbose_name="Hareket Tipi")
    tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tutar")
    
    # İlişkili kayıtlar
    satis_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="Satış ID")
    tahsilat = models.ForeignKey(Tahsilat, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Tahsilat")
    
    # Bakiye bilgisi
    onceki_bakiye = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Önceki Bakiye")
    yeni_bakiye = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Yeni Bakiye")
    
    # Açıklama
    aciklama = models.TextField(verbose_name="Açıklama")
    
    # Tarih ve kullanıcı
    hareket_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Hareket Tarihi")
    islem_yapan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="İşlem Yapan")
    
    class Meta:
        verbose_name = "Borç Alacak Hareket"
        verbose_name_plural = "Borç Alacak Hareketleri"
        ordering = ['-hareket_tarihi']
    
    def __str__(self):
        return f"{self.musteri} - {self.get_hareket_tipi_display()} - {self.tutar}₺"
