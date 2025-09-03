from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class GiderKategori(models.Model):
    """Gider kategorileri"""
    ad = models.CharField(max_length=100, verbose_name="Kategori Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    renk = models.CharField(max_length=7, default="#6c757d", verbose_name="Renk Kodu", 
                           help_text="Hex renk kodu (örn: #FF5733)")
    ikon = models.CharField(max_length=50, default="fas fa-money-bill", verbose_name="İkon",
                           help_text="FontAwesome ikon sınıfı")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Gider Kategorisi"
        verbose_name_plural = "Gider Kategorileri"
        ordering = ['ad']

    def __str__(self):
        return self.ad


class Gider(models.Model):
    """Ana gider modeli"""
    ODEME_YONTEMLERI = [
        ('nakit', 'Nakit'),
        ('kart', 'Kredi/Banka Kartı'),
        ('havale', 'Havale/EFT'),
        ('cek', 'Çek'),
        ('diger', 'Diğer'),
    ]

    baslik = models.CharField(max_length=200, verbose_name="Başlık")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    kategori = models.ForeignKey(GiderKategori, on_delete=models.PROTECT, verbose_name="Kategori")
    tutar = models.DecimalField(max_digits=10, decimal_places=2, 
                               validators=[MinValueValidator(Decimal('0.01'))],
                               verbose_name="Tutar")
    odeme_yontemi = models.CharField(max_length=20, choices=ODEME_YONTEMLERI, 
                                   default='nakit', verbose_name="Ödeme Yöntemi")
    tarih = models.DateField(verbose_name="Gider Tarihi")
    fatura_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fatura/Fiş No")
    tedarikci = models.CharField(max_length=200, blank=True, null=True, verbose_name="Tedarikçi/Firma")
    
    # Belge ekleri
    fatura_fotografi = models.ImageField(upload_to='giderler/faturalar/', blank=True, null=True,
                                        verbose_name="Fatura/Fiş Fotoğrafı")
    ek_belge = models.FileField(upload_to='giderler/belgeler/', blank=True, null=True,
                               verbose_name="Ek Belge")
    
    # Tekrarlayan gider özellikleri
    tekrarlayan = models.BooleanField(default=False, verbose_name="Tekrarlayan Gider")
    tekrar_periyodu = models.CharField(max_length=20, blank=True, null=True,
                                     choices=[
                                         ('gunluk', 'Günlük'),
                                         ('haftalik', 'Haftalık'),
                                         ('aylik', 'Aylık'),
                                         ('yillik', 'Yıllık'),
                                     ], verbose_name="Tekrar Periyodu")
    
    # Meta bilgiler
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Gider"
        verbose_name_plural = "Giderler"
        ordering = ['-tarih', '-olusturma_tarihi']
        indexes = [
            models.Index(fields=['tarih']),
            models.Index(fields=['kategori']),
            models.Index(fields=['olusturan']),
        ]

    def __str__(self):
        return f"{self.baslik} - {self.tutar} ₺ ({self.tarih})"

    @property
    def kategori_renk(self):
        """Kategori renk kodunu döndürür"""
        return self.kategori.renk if self.kategori else "#6c757d"

    @property
    def kategori_ikon(self):
        """Kategori ikon sınıfını döndürür"""
        return self.kategori.ikon if self.kategori else "fas fa-money-bill"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
