from django.db import models
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile


class UrunKategoriUst(models.Model):
    """Kategori modeli"""
    ad = models.CharField(max_length=100, unique=True, verbose_name="Kategori Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering = ['ad']

    def __str__(self):
        return self.ad


class Varyasyon(models.Model):
    """Ürün varyasyonları için model (Renk, Beden)"""
    VARYASYON_TIPI = [
        ('renk', 'Renk'),
        ('beden', 'Beden'),
        ('diger', 'Diğer'),
    ]
    
    tip = models.CharField(max_length=10, choices=VARYASYON_TIPI, verbose_name="Varyasyon Tipi")
    deger = models.CharField(max_length=50, verbose_name="Değer")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Varyasyon"
        verbose_name_plural = "Varyasyonlar"
        ordering = ['tip', 'deger']
        unique_together = ['tip', 'deger']

    def __str__(self):
        return f"{self.get_tip_display()}: {self.deger}"


class Marka(models.Model):
    """Ürün markaları için model"""
    ad = models.CharField(max_length=100, unique=True, verbose_name="Marka Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    logo = models.ImageField(upload_to='marka_logolari/', blank=True, null=True, verbose_name="Marka Logosu")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Marka"
        verbose_name_plural = "Markalar"
        ordering = ['ad']

    def __str__(self):
        return self.ad


class Urun(models.Model):
    """Ana ürün modeli"""
    CINSIYET_SECENEKLERI = [
        ('kadin', 'Kadın'),
        ('erkek', 'Erkek'),
    ]
    
    barkod = models.CharField(max_length=50, unique=True, verbose_name="Barkod")
    sku = models.CharField(max_length=50, unique=True, verbose_name="Ürün Kodu (SKU)", blank=True)
    ad = models.CharField(max_length=200, verbose_name="Ürün Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    kategori = models.ForeignKey(UrunKategoriUst, on_delete=models.CASCADE, verbose_name="Kategori")
    marka = models.ForeignKey(Marka, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Marka")
    varyasyonlar = models.ManyToManyField(Varyasyon, blank=True, verbose_name="Varyasyonlar")
    cinsiyet = models.CharField(max_length=10, choices=CINSIYET_SECENEKLERI, default='kadin', verbose_name="Cinsiyet")
    
    # Fiyat bilgileri
    alis_fiyati = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Alış Fiyatı (KDV Hariç)")
    kar_marji = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, verbose_name="Kar Marjı (%)")
    satis_fiyati = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Satış Fiyatı")
    
    # Stok bilgisi
    stok_miktari = models.PositiveIntegerField(default=0, verbose_name="Stok Miktarı")
    minimum_stok = models.PositiveIntegerField(default=5, verbose_name="Minimum Stok Uyarı Seviyesi")
    
    # Ürün resmi
    resim = models.ImageField(upload_to='urun_resimleri/', blank=True, null=True, verbose_name="Ürün Resmi")
    
    # Durum bilgisi
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    # Tarih bilgileri
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    olusturan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['-olusturma_tarihi']

    def __str__(self):
        return f"{self.barkod} - {self.ad}"

    def save(self, *args, **kwargs):
        # Kar marjına göre satış fiyatını otomatik hesapla
        if self.alis_fiyati and self.kar_marji:
            from decimal import Decimal
            try:
                # Tüm değerleri güvenli bir şekilde Decimal'e çevir
                alis_fiyati_decimal = Decimal(str(self.alis_fiyati))
                kar_marji_decimal = Decimal(str(self.kar_marji))
                kar_carpani = Decimal('1') + (kar_marji_decimal / Decimal('100'))
                self.satis_fiyati = alis_fiyati_decimal * kar_carpani
            except (ValueError, TypeError, ZeroDivisionError):
                # Hata durumunda satış fiyatını alış fiyatına eşitle
                self.satis_fiyati = self.alis_fiyati
        
        # Resmi yeniden boyutlandır
        if self.resim:
            self._resize_image()
        
        super().save(*args, **kwargs)

    def _resize_image(self):
        """Ürün resmini 800x800 maksimum boyuta getir"""
        if self.resim:
            img = Image.open(self.resim)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Maksimum boyut 800x800
            max_size = (800, 800)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Resmi BytesIO buffer'a kaydet
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            # Dosya adını güncelle
            file_name = f"{self.barkod}.jpg"
            self.resim.save(file_name, ContentFile(buffer.read()), save=False)

    @property
    def kdv_dahil_satis_fiyati(self):
        """KDV dahil satış fiyatı (varsayılan %10 KDV)"""
        return self.satis_fiyati * 1.10

    @property
    def stok_durumu(self):
        """Stok durum kontrolü"""
        if self.stok_miktari == 0:
            return "Tükendi"
        elif self.stok_miktari <= self.minimum_stok:
            return "Kritik Seviye"
        else:
            return "Normal"

    @property
    def varyasyon_listesi(self):
        """Varyasyonları string olarak döndür"""
        return ", ".join([str(v) for v in self.varyasyonlar.all()])
