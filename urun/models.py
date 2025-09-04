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
    hex_kodu = models.CharField(max_length=7, blank=True, null=True, verbose_name="Renk Hex Kodu")  # Renk için
    sira = models.PositiveIntegerField(default=0, verbose_name="Sıra")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Varyasyon"
        verbose_name_plural = "Varyasyonlar"
        ordering = ['tip', 'sira', 'deger']
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
    """Ana ürün modeli - Varyasyonların ana bilgilerini tutar"""
    CINSIYET_SECENEKLERI = [
        ('kadin', 'Kadın'),
        ('erkek', 'Erkek'),
        ('unisex', 'Unisex'),
    ]
    
    BIRIM_SECENEKLERI = [
        ('adet', 'Adet'),
        ('takim', 'Takım'),
        ('cift', 'Çift'),
        ('kg', 'Kilogram'),
        ('gr', 'Gram'),
        ('lt', 'Litre'),
        ('ml', 'Mililitre'),
        ('m', 'Metre'),
        ('cm', 'Santimetre'),
    ]
    
    sku = models.CharField(max_length=50, unique=True, verbose_name="Ürün Kodu (SKU)", blank=True)
    ad = models.CharField(max_length=200, verbose_name="Ürün Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    kategori = models.ForeignKey(UrunKategoriUst, on_delete=models.CASCADE, verbose_name="Kategori")
    marka = models.ForeignKey(Marka, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Marka")
    cinsiyet = models.CharField(max_length=10, choices=CINSIYET_SECENEKLERI, default='kadin', verbose_name="Cinsiyet")
    birim = models.CharField(max_length=10, choices=BIRIM_SECENEKLERI, default='adet', verbose_name="Birim")
    
    # Varyasyon kontrolü
    varyasyonlu = models.BooleanField(default=False, verbose_name="Varyasyonlu Ürün")
    varyasyon_tipleri = models.ManyToManyField(
        Varyasyon, 
        blank=True, 
        limit_choices_to={'aktif': True},
        verbose_name="Kullanılan Varyasyon Tipleri"
    )
    
    # Temel fiyat bilgileri (varyasyonsuz ürünler için)
    temel_alis_fiyati = models.DecimalField(
        max_digits=10, decimal_places=2, 
        null=True, blank=True,
        verbose_name="Temel Alış Fiyatı"
    )
    temel_kar_orani = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=50.00, 
        verbose_name="Temel Kar Oranı (%)"
    )
    temel_satis_fiyati = models.DecimalField(
        max_digits=10, decimal_places=2, 
        null=True, blank=True,
        verbose_name="Temel Satış Fiyatı"
    )
    
    # Varyasyonsuz ürünler için stok
    temel_stok_miktari = models.PositiveIntegerField(default=0, verbose_name="Temel Stok Miktarı")
    kritik_stok_seviyesi = models.PositiveIntegerField(default=5, verbose_name="Kritik Stok Seviyesi")
    
    # Ürün resmi
    resim = models.ImageField(upload_to='urun_resimleri/', blank=True, null=True, verbose_name="Ana Ürün Resmi")
    
    # Durum bilgisi
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    stok_takibi = models.BooleanField(default=True, verbose_name="Stok Takibi Yapılsın")
    
    # Tarih bilgileri
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    olusturan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['-olusturma_tarihi']

    def __str__(self):
        return f"{self.sku} - {self.ad}"

    def save(self, *args, **kwargs):
        # SKU otomatik oluştur
        if not self.sku:
            from django.utils.crypto import get_random_string
            self.sku = f"URN{get_random_string(6, allowed_chars='0123456789')}"
        
        # Varyasyonsuz ürünler için fiyat hesapla
        if not self.varyasyonlu and self.temel_alis_fiyati and self.temel_kar_orani:
            from decimal import Decimal
            try:
                alis_fiyati_decimal = Decimal(str(self.temel_alis_fiyati))
                kar_orani_decimal = Decimal(str(self.temel_kar_orani))
                kar_carpani = Decimal('1') + (kar_orani_decimal / Decimal('100'))
                self.temel_satis_fiyati = alis_fiyati_decimal * kar_carpani
            except (ValueError, TypeError, ZeroDivisionError):
                self.temel_satis_fiyati = self.temel_alis_fiyati
        
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
            file_name = f"{self.sku}.jpg"
            self.resim.save(file_name, ContentFile(buffer.read()), save=False)

    @property
    def toplam_stok(self):
        """Toplam stok miktarı (varyantları dahil)"""
        if self.varyasyonlu:
            return sum(varyant.stok_miktari for varyant in self.varyantlari.all())
        return self.temel_stok_miktari

    @property
    def stok_durumu(self):
        """Stok durum kontrolü"""
        toplam_stok = self.toplam_stok
        if toplam_stok == 0:
            return "Tükendi"
        elif toplam_stok <= self.kritik_stok_seviyesi:
            return "Kritik Seviye"
        else:
            return "Normal"

    @property
    def en_dusuk_fiyat(self):
        """En düşük satış fiyatı"""
        if self.varyasyonlu:
            fiyatlar = [v.satis_fiyati for v in self.varyantlari.filter(aktif=True)]
            return min(fiyatlar) if fiyatlar else 0
        return self.temel_satis_fiyati or 0

    @property
    def en_yuksek_fiyat(self):
        """En yüksek satış fiyatı"""
        if self.varyasyonlu:
            fiyatlar = [v.satis_fiyati for v in self.varyantlari.filter(aktif=True)]
            return max(fiyatlar) if fiyatlar else 0
        return self.temel_satis_fiyati or 0


class UrunVaryanti(models.Model):
    """Ürün varyantları - Her kombinasyon için ayrı kayıt"""
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, related_name='varyantlari', verbose_name="Ana Ürün")
    barkod = models.CharField(max_length=50, unique=True, verbose_name="Barkod")
    
    # Varyasyon kombinasyonu
    renk = models.ForeignKey(
        Varyasyon, 
        on_delete=models.CASCADE, 
        related_name='renk_varyantlari',
        limit_choices_to={'tip': 'renk', 'aktif': True},
        null=True, blank=True,
        verbose_name="Renk"
    )
    beden = models.ForeignKey(
        Varyasyon, 
        on_delete=models.CASCADE, 
        related_name='beden_varyantlari',
        limit_choices_to={'tip': 'beden', 'aktif': True},
        null=True, blank=True,
        verbose_name="Beden"
    )
    diger_varyasyon = models.ForeignKey(
        Varyasyon, 
        on_delete=models.CASCADE, 
        related_name='diger_varyantlari',
        limit_choices_to={'tip': 'diger', 'aktif': True},
        null=True, blank=True,
        verbose_name="Diğer Varyasyon"
    )
    
    # Fiyat bilgileri
    alis_fiyati = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Alış Fiyatı")
    kar_orani = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, verbose_name="Kar Oranı (%)")
    satis_fiyati = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Satış Fiyatı")
    
    # Stok bilgisi
    stok_miktari = models.PositiveIntegerField(default=0, verbose_name="Stok Miktarı")
    
    # Ek bilgiler
    ek_aciklama = models.CharField(max_length=200, blank=True, null=True, verbose_name="Ek Açıklama")
    resim = models.ImageField(upload_to='varyant_resimleri/', blank=True, null=True, verbose_name="Varyant Resmi")
    
    # Durum bilgisi
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    # Tarih bilgileri
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ürün Varyantı"
        verbose_name_plural = "Ürün Varyantları"
        ordering = ['urun', 'renk', 'beden', 'diger_varyasyon']
        unique_together = ['urun', 'renk', 'beden', 'diger_varyasyon']

    def __str__(self):
        varyasyonlar = []
        if self.renk:
            varyasyonlar.append(str(self.renk.deger))
        if self.beden:
            varyasyonlar.append(str(self.beden.deger))
        if self.diger_varyasyon:
            varyasyonlar.append(str(self.diger_varyasyon.deger))
        
        varyasyon_str = " - ".join(varyasyonlar) if varyasyonlar else "Standart"
        return f"{self.urun.ad} ({varyasyon_str})"

    def save(self, *args, **kwargs):
        # Barkod otomatik oluştur
        if not self.barkod:
            from django.utils.crypto import get_random_string
            suffix = get_random_string(4, allowed_chars='0123456789')
            self.barkod = f"{self.urun.sku}V{suffix}"
        
        # Kar oranına göre satış fiyatını otomatik hesapla
        if self.alis_fiyati and self.kar_orani:
            from decimal import Decimal
            try:
                alis_fiyati_decimal = Decimal(str(self.alis_fiyati))
                kar_orani_decimal = Decimal(str(self.kar_orani))
                kar_carpani = Decimal('1') + (kar_orani_decimal / Decimal('100'))
                self.satis_fiyati = alis_fiyati_decimal * kar_carpani
            except (ValueError, TypeError, ZeroDivisionError):
                self.satis_fiyati = self.alis_fiyati
        
        # Resmi yeniden boyutlandır
        if self.resim:
            self._resize_image()
        
        super().save(*args, **kwargs)

    def _resize_image(self):
        """Varyant resmini 800x800 maksimum boyuta getir"""
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
    def varyasyon_adi(self):
        """Varyasyon adını döndür"""
        varyasyonlar = []
        if self.renk:
            varyasyonlar.append(self.renk.deger)
        if self.beden:
            varyasyonlar.append(self.beden.deger)
        if self.diger_varyasyon:
            varyasyonlar.append(self.diger_varyasyon.deger)
        
        return " - ".join(varyasyonlar) if varyasyonlar else "Standart"

    @property
    def kdv_dahil_satis_fiyati(self):
        """KDV dahil satış fiyatı (varsayılan %10 KDV)"""
        return self.satis_fiyati * 1.10

    @property
    def stok_durumu(self):
        """Stok durum kontrolü"""
        if self.stok_miktari == 0:
            return "Tükendi"
        elif self.stok_miktari <= self.urun.kritik_stok_seviyesi:
            return "Kritik Seviye"
        else:
            return "Normal"
