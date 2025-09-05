from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Kasa(models.Model):
    """Kasa tanımları"""
    KASA_TIPLERI = [
        ('nakit', 'Nakit Kasası'),
        ('pos', 'POS Kredi Kartı'),
        ('kart', 'Harcama Kredi Kartı'), 
        ('banka', 'Banka Hesabı'),
        ('other', 'Diğer'),
    ]
    
    ad = models.CharField(max_length=100, verbose_name="Kasa Adı")
    tip = models.CharField(max_length=20, choices=KASA_TIPLERI, verbose_name="Kasa Tipi")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    baslangic_bakiye = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Başlangıç Bakiyesi")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    
    class Meta:
        verbose_name = "Kasa"
        verbose_name_plural = "Kasalar"
        ordering = ['tip', 'ad']
    
    def __str__(self):
        return f"{self.ad} ({self.get_tip_display()})"
    
    @property
    def guncel_bakiye(self):
        """Güncel kasa bakiyesini hesapla"""
        toplam_giris = self.hareketler.filter(tip='giris').aggregate(
            toplam=models.Sum('tutar')
        )['toplam'] or Decimal('0')
        
        toplam_cikis = self.hareketler.filter(tip='cikis').aggregate(
            toplam=models.Sum('tutar')
        )['toplam'] or Decimal('0')
        
        return self.baslangic_bakiye + toplam_giris - toplam_cikis
    
    def bakiye(self):
        """Güncel kasa bakiyesini hesapla - method versiyonu"""
        return self.guncel_bakiye
    
    @property
    def bugunki_hareketler(self):
        """Bugünkü hareketleri getir"""
        bugun = timezone.now().date()
        return self.hareketler.filter(tarih__date=bugun)


class KasaHareket(models.Model):
    """Kasa hareketleri"""
    HAREKET_TIPLERI = [
        ('giris', 'Para Girişi'),
        ('cikis', 'Para Çıkışı'),
    ]
    
    HAREKET_KAYNAKLARI = [
        ('satis', 'Satış'),
        ('gider', 'Gider'),
        ('virman', 'Virman'),
        ('cikis', 'Para Çıkışı'),
        ('giris', 'Para Girişi'),
        ('duzeltme', 'Düzeltme'),
    ]
    
    kasa = models.ForeignKey(Kasa, on_delete=models.CASCADE, related_name='hareketler', verbose_name="Kasa")
    tip = models.CharField(max_length=10, choices=HAREKET_TIPLERI, verbose_name="Hareket Tipi")
    kaynak = models.CharField(max_length=20, choices=HAREKET_KAYNAKLARI, verbose_name="Kaynak")
    tutar = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Tutar")
    aciklama = models.TextField(verbose_name="Açıklama")
    
    # İlişkili kayıtlar
    satis_id = models.PositiveIntegerField(blank=True, null=True, verbose_name="Satış ID")
    gider_id = models.PositiveIntegerField(blank=True, null=True, verbose_name="Gider ID")
    virman_id = models.PositiveIntegerField(blank=True, null=True, verbose_name="Virman ID")
    
    # Sistem bilgileri
    kullanici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Kullanıcı")
    tarih = models.DateTimeField(default=timezone.now, verbose_name="Tarih")
    
    class Meta:
        verbose_name = "Kasa Hareketi"
        verbose_name_plural = "Kasa Hareketleri"
        ordering = ['-tarih']
    
    def __str__(self):
        return f"{self.kasa.ad} - {self.get_tip_display()} - {self.tutar}₺"


class KasaVirman(models.Model):
    """Kasalar arası virman işlemleri"""
    kaynak_kasa = models.ForeignKey(Kasa, on_delete=models.CASCADE, related_name='giden_virmanlar', verbose_name="Kaynak Kasa")
    hedef_kasa = models.ForeignKey(Kasa, on_delete=models.CASCADE, related_name='gelen_virmanlar', verbose_name="Hedef Kasa")
    tutar = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Tutar")
    aciklama = models.TextField(verbose_name="Açıklama")
    kullanici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Kullanıcı")
    tarih = models.DateTimeField(default=timezone.now, verbose_name="Tarih")
    
    class Meta:
        verbose_name = "Kasa Virmanı"
        verbose_name_plural = "Kasa Virmanları"
        ordering = ['-tarih']
    
    def __str__(self):
        return f"{self.kaynak_kasa.ad} → {self.hedef_kasa.ad} ({self.tutar}₺)"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Kaynak kasadan çıkış hareketi
        KasaHareket.objects.create(
            kasa=self.kaynak_kasa,
            tip='cikis',
            kaynak='virman',
            tutar=self.tutar,
            aciklama=f"Virman: {self.hedef_kasa.ad} kasasına",
            virman_id=self.id,
            kullanici=self.kullanici
        )
        
        # Hedef kasaya giriş hareketi
        KasaHareket.objects.create(
            kasa=self.hedef_kasa,
            tip='giris',
            kaynak='virman',
            tutar=self.tutar,
            aciklama=f"Virman: {self.kaynak_kasa.ad} kasasından",
            virman_id=self.id,
            kullanici=self.kullanici
        )


class KasaCikis(models.Model):
    """Kasadan para çıkış işlemleri"""
    CIKIS_SEBEPLERI = [
        ('kisisel', 'Kişisel Çekim'),
        ('harcama', 'Harcama'),
        ('odeme', 'Ödeme'),
        ('banka', 'Bankaya Yatırma'),
        ('diger', 'Diğer'),
    ]
    
    kasa = models.ForeignKey(Kasa, on_delete=models.CASCADE, related_name='cikislar', verbose_name="Kasa")
    tutar = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Tutar")
    sebep = models.CharField(max_length=20, choices=CIKIS_SEBEPLERI, verbose_name="Çıkış Sebebi")
    aciklama = models.TextField(verbose_name="Açıklama")
    kullanici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Kullanıcı")
    tarih = models.DateTimeField(default=timezone.now, verbose_name="Tarih")
    
    class Meta:
        verbose_name = "Kasa Çıkışı"
        verbose_name_plural = "Kasa Çıkışları"
        ordering = ['-tarih']
    
    def __str__(self):
        return f"{self.kasa.ad} - {self.tutar}₺ ({self.get_sebep_display()})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Kasa hareket kaydı oluştur
        KasaHareket.objects.create(
            kasa=self.kasa,
            tip='cikis',
            kaynak='cikis',
            tutar=self.tutar,
            aciklama=f"{self.get_sebep_display()}: {self.aciklama}",
            kullanici=self.kullanici
        )


class KasaGiris(models.Model):
    """Kasaya para giriş işlemleri"""
    GIRIS_SEBEPLERI = [
        ('yatirim', 'Yatırım'),
        ('gelir', 'Gelir'),
        ('bankadan', 'Bankadan Çekim'),
        ('diger', 'Diğer'),
    ]
    
    kasa = models.ForeignKey(Kasa, on_delete=models.CASCADE, related_name='girisler', verbose_name="Kasa")
    tutar = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Tutar")
    sebep = models.CharField(max_length=20, choices=GIRIS_SEBEPLERI, verbose_name="Giriş Sebebi")
    aciklama = models.TextField(verbose_name="Açıklama")
    kullanici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Kullanıcı")
    tarih = models.DateTimeField(default=timezone.now, verbose_name="Tarih")
    
    class Meta:
        verbose_name = "Kasa Girişi"
        verbose_name_plural = "Kasa Girişleri"
        ordering = ['-tarih']
    
    def __str__(self):
        return f"{self.kasa.ad} + {self.tutar}₺ ({self.get_sebep_display()})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Kasa hareket kaydı oluştur
        KasaHareket.objects.create(
            kasa=self.kasa,
            tip='giris',
            kaynak='giris',
            tutar=self.tutar,
            aciklama=f"{self.get_sebep_display()}: {self.aciklama}",
            kullanici=self.kullanici
        )
