from django.db import models
from django.conf import settings
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class UrunKategoriUst(models.Model):
    """Üst kategori modeli"""
    ad = models.CharField(max_length=100, unique=True, verbose_name="Kategori Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Üst Kategori"
        verbose_name_plural = "Üst Kategoriler"
        ordering = ['ad']

    def __str__(self):
        return self.ad


class Renk(models.Model):
    """Renk varyasyon modeli"""
    ad = models.CharField(max_length=50, unique=True, verbose_name="Renk Adı")
    kod = models.CharField(max_length=1, unique=True, verbose_name="Renk Kodu (1 harf)")
    hex_kod = models.CharField(max_length=7, blank=True, null=True, verbose_name="Hex Renk Kodu")
    sira = models.PositiveIntegerField(default=1, verbose_name="Sıra")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Renk"
        verbose_name_plural = "Renkler"
        ordering = ['sira', 'ad']

    def __str__(self):
        return f"{self.ad} ({self.kod})"


class Beden(models.Model):
    """Beden varyasyon modeli"""
    ad = models.CharField(max_length=20, unique=True, verbose_name="Beden Adı")
    kod = models.CharField(max_length=1, unique=True, verbose_name="Beden Kodu (1 karakter)")
    tip = models.CharField(max_length=20, choices=[
        ('harf', 'Harf (XS, S, M, L, XL, XXL)'),
        ('rakam', 'Rakam (36, 38, 40, 42)')
    ], default='harf', verbose_name="Beden Tipi")
    sira = models.PositiveIntegerField(default=1, verbose_name="Sıra")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Beden"
        verbose_name_plural = "Bedenler"
        ordering = ['tip', 'sira', 'ad']

    def __str__(self):
        return f"{self.ad} ({self.kod})"


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
    
    # Benzersiz ürün kodu
    urun_kodu = models.CharField(max_length=5, unique=True, verbose_name="Ürün Kodu (5 hane)", blank=True, null=True)
    ad = models.CharField(max_length=200, verbose_name="Ürün Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    kategori = models.ForeignKey(UrunKategoriUst, on_delete=models.CASCADE, verbose_name="Kategori")
    marka = models.ForeignKey(Marka, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Marka")
    cinsiyet = models.CharField(max_length=10, choices=CINSIYET_SECENEKLERI, default='kadin', verbose_name="Cinsiyet")
    birim = models.CharField(max_length=10, choices=BIRIM_SECENEKLERI, default='adet', verbose_name="Birim")
    
    # Varyasyon kontrolü
    varyasyonlu = models.BooleanField(default=False, verbose_name="Varyasyonlu Ürün")
    
    # Temel fiyat bilgileri
    alis_fiyati = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Alış Fiyatı")
    kar_orani = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, verbose_name="Kar Oranı (%)")
    satis_fiyati = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Satış Fiyatı")
    
    # Ürün resmi
    resim = models.ImageField(upload_to='urun_resimleri/', blank=True, null=True, verbose_name="Ana Ürün Resmi")
    
    # Durum bilgisi
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    stok_takibi = models.BooleanField(default=True, verbose_name="Stok Takibi Yapılsın")
    kritik_stok_seviyesi = models.PositiveIntegerField(default=5, verbose_name="Kritik Stok Seviyesi")
    
    # Tarih bilgileri
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    olusturan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['-olusturma_tarihi']

    def save(self, *args, **kwargs):
        # Ürün kodu otomatik oluştur
        if not self.urun_kodu:
            # Son ürün kodunu bul ve 1 artır
            son_urun = Urun.objects.filter(urun_kodu__isnull=False).order_by('-urun_kodu').first()
            if son_urun and son_urun.urun_kodu.isdigit():
                yeni_kod = str(int(son_urun.urun_kodu) + 1).zfill(5)
            else:
                yeni_kod = '00001'
            self.urun_kodu = yeni_kod
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.urun_kodu} - {self.ad}"

    @property
    def toplam_stok(self):
        """Toplam stok miktarını hesapla"""
        if self.varyasyonlu:
            return sum(v.stok_miktari for v in self.varyantlar.filter(aktif=True))
        else:
            varyant = self.varyantlar.first()
            return varyant.stok_miktari if varyant else 0

    @property
    def ozellik_kodu(self):
        """Barkod için özellik kodunu oluştur"""
        if not self.varyasyonlu:
            return "00"  # Varyasyonsuz ürün
        
        # Varyantları kontrol et
        varyant = self.varyantlar.first()
        if not varyant:
            return "00"
        
        renk_var = varyant.renk is not None
        beden_var = varyant.beden is not None
        
        if renk_var and beden_var:
            return "03"  # Renk + Beden
        elif renk_var:
            return "01"  # Sadece renk
        elif beden_var:
            return "02"  # Sadece beden
        else:
            return "00"  # Varyasyonsuz


class UrunVaryanti(models.Model):
    """Ürün varyantları - her renk/beden kombinasyonu için ayrı kayıt"""
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, related_name='varyantlar', verbose_name="Ürün")
    renk = models.ForeignKey(Renk, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Renk")
    beden = models.ForeignKey(Beden, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Beden")
    
    # Barkod - otomatik oluşturulacak
    barkod = models.CharField(max_length=13, unique=True, verbose_name="Barkod", blank=True)
    
    # Stok bilgisi
    stok_miktari = models.PositiveIntegerField(default=1, verbose_name="Stok Miktarı")
    stok_kaydedildi = models.BooleanField(default=False, verbose_name="Stok Kaydedildi Mi?")
    
    # Ek bilgiler
    ek_aciklama = models.TextField(blank=True, null=True, verbose_name="Ek Açıklama")
    resim = models.ImageField(upload_to='varyant_resimleri/', blank=True, null=True, verbose_name="Varyant Resmi")
    
    # Durum
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ürün Varyantı"
        verbose_name_plural = "Ürün Varyantları"
        ordering = ['urun', 'renk', 'beden']
        unique_together = ['urun', 'renk', 'beden']

    def save(self, *args, **kwargs):
        # Barkod otomatik oluştur
        if not self.barkod:
            self.barkod = self.olustur_barkod()
        super().save(*args, **kwargs)

    def olustur_barkod(self):
        """Akıllı barkod algoritması ile barkod oluştur"""
        # 1. Özellik kodu (2 hane)
        ozellik_kodu = self.urun.ozellik_kodu
        
        # 2. Varyant kodu (2 hane)
        renk_kodu = self.renk.kod if self.renk else "0"
        beden_kodu = self.beden.kod if self.beden else "0"
        varyant_kodu = f"{renk_kodu}{beden_kodu}"
        
        # 3. Ürün numarası (5 hane)
        urun_numarasi = self.urun.urun_kodu
        
        # 4. Fiyat (4 hane)
        fiyat_kodu = str(int(self.urun.satis_fiyati)).zfill(4)
        
        # Barkod birleştir
        barkod = f"{ozellik_kodu}{varyant_kodu}{urun_numarasi}{fiyat_kodu}"
        
        return barkod

    @property
    def varyasyon_adi(self):
        """Varyasyon adını oluştur"""
        parts = []
        if self.renk:
            parts.append(self.renk.ad)
        if self.beden:
            parts.append(self.beden.ad)
        return " - ".join(parts) if parts else "Standart"

    def __str__(self):
        return f"{self.urun.ad} ({self.varyasyon_adi})"

    @classmethod
    def barkod_cozumle(cls, barkod):
        """Barkod çözümleme algoritması"""
        if len(barkod) != 13:
            return None
        
        try:
            # Barkodu parçalara ayır
            ozellik_kodu = barkod[:2]
            varyant_kodu = barkod[2:4]
            urun_numarasi = barkod[4:9]
            fiyat_kodu = barkod[9:13]
            
            # Ürünü bul
            urun = Urun.objects.filter(urun_kodu=urun_numarasi).first()
            if not urun:
                return None
            
            # Varyant kodlarını çöz
            renk_kodu = varyant_kodu[0] if varyant_kodu[0] != "0" else None
            beden_kodu = varyant_kodu[1] if varyant_kodu[1] != "0" else None
            
            # Renk ve beden objelerini bul
            renk = None
            beden = None
            
            if renk_kodu:
                renk = Renk.objects.filter(kod=renk_kodu).first()
            if beden_kodu:
                beden = Beden.objects.filter(kod=beden_kodu).first()
            
            # Varyantı bul
            varyant = cls.objects.filter(urun=urun, renk=renk, beden=beden).first()
            
            return {
                'varyant': varyant,
                'urun': urun,
                'renk': renk,
                'beden': beden,
                'fiyat': int(fiyat_kodu),
                'ozellik_kodu': ozellik_kodu,
                'varyant_kodu': varyant_kodu,
                'urun_numarasi': urun_numarasi
            }
        except:
            return None


class StokHareket(models.Model):
    """Stok hareket takip modeli"""
    HAREKET_TIPLERI = [
        ('giris', 'Stok Girişi'),
        ('cikis', 'Stok Çıkışı'),
        ('duzeltme', 'Stok Düzeltmesi'),
        ('sayim', 'Stok Sayımı'),
        ('transfer', 'Transfer'),
        ('fire', 'Fire'),
    ]
    
    varyant = models.ForeignKey('UrunVaryanti', on_delete=models.CASCADE, verbose_name="Ürün Varyantı")
    hareket_tipi = models.CharField(max_length=20, choices=HAREKET_TIPLERI, verbose_name="Hareket Tipi")
    miktar = models.IntegerField(verbose_name="Miktar")
    onceki_stok = models.IntegerField(verbose_name="Önceki Stok")
    yeni_stok = models.IntegerField(verbose_name="Yeni Stok")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    referans_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Referans ID")  # Satış ID vs.
    kullanici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    
    class Meta:
        verbose_name = "Stok Hareket"
        verbose_name_plural = "Stok Hareketleri"
        ordering = ['-olusturma_tarihi']
    
    def __str__(self):
        return f"{self.varyant} - {self.get_hareket_tipi_display()} ({self.miktar})"
    
    @classmethod
    def stok_hareketi_olustur(cls, varyant, hareket_tipi, miktar, kullanici, aciklama=None, referans_id=None):
        """Stok hareketi oluşturur"""
        onceki_stok = varyant.stok_miktari
        
        if hareket_tipi == 'giris':
            yeni_stok = onceki_stok + miktar
        elif hareket_tipi == 'cikis':
            yeni_stok = onceki_stok - miktar
        else:
            yeni_stok = miktar  # Düzeltme, sayım vb. için direkt miktar
        
        # Stok hareketini kaydet
        hareket = cls.objects.create(
            varyant=varyant,
            hareket_tipi=hareket_tipi,
            miktar=miktar,
            onceki_stok=onceki_stok,
            yeni_stok=yeni_stok,
            aciklama=aciklama,
            referans_id=referans_id,
            kullanici=kullanici
        )
        
        # Varyantın stok miktarını güncelle
        varyant.stok_miktari = yeni_stok
        varyant.save(update_fields=['stok_miktari'])
        
        return hareket
