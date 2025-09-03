from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from musteri.models import Musteri


class HediyeCeki(models.Model):
    """Hediye çeki modeli"""
    DURUM_SECENEKLERI = [
        ('aktif', 'Aktif'),
        ('kullanilmis', 'Kullanılmış'),
        ('iptal', 'İptal'),
        ('suresi_dolmus', 'Süresi Dolmuş'),
    ]
    
    # Çek bilgileri
    kod = models.CharField(max_length=20, unique=True, verbose_name="Hediye Çeki Kodu")
    tutar = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Çek Tutarı")
    kalan_tutar = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Kalan Tutar")
    
    # Tarih bilgileri
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    gecerlilik_tarihi = models.DateField(verbose_name="Geçerlilik Tarihi")
    kullanilma_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Kullanılma Tarihi")
    
    # İlişkiler
    olusturan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='olusturulan_hediye_cekleri', verbose_name="Oluşturan")
    musteri = models.ForeignKey(Musteri, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Müşteri")
    
    # Durum
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='aktif', verbose_name="Durum")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    # Notlar
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")

    class Meta:
        verbose_name = "Hediye Çeki"
        verbose_name_plural = "Hediye Çekleri"
        ordering = ['-olusturma_tarihi']
    
    def __str__(self):
        return f"{self.kod} - {self.kalan_tutar} ₺"
    
    def kullan(self, tutar):
        """Hediye çekinden belirtilen tutarı kullan"""
        from decimal import Decimal
        tutar = Decimal(str(tutar))
        
        if tutar > self.kalan_tutar:
            raise ValueError("Hediye çekinde yeterli bakiye yok!")
        
        self.kalan_tutar -= tutar
        if self.kalan_tutar == 0:
            self.durum = 'kullanilmis'
            self.kullanilma_tarihi = timezone.now()
        
        self.save()
        return self.kalan_tutar
    
    @property
    def kullanilabilir_mi(self):
        """Hediye çeki kullanılabilir mi?"""
        from django.utils import timezone
        return (
            self.aktif and 
            self.durum == 'aktif' and 
            self.kalan_tutar > 0 and 
            self.gecerlilik_tarihi >= timezone.now().date()
        )


class HediyeCekiKullanim(models.Model):
    """Hediye çeki kullanım geçmişi"""
    hediye_ceki = models.ForeignKey(HediyeCeki, on_delete=models.CASCADE, related_name='kullanimlar', verbose_name="Hediye Çeki")
    kullanilan_tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kullanılan Tutar")
    kullanim_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Kullanım Tarihi")
    satis_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="Satış ID")
    kullanan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Kullanan")
    aciklama = models.CharField(max_length=255, blank=True, verbose_name="Açıklama")

    class Meta:
        verbose_name = "Hediye Çeki Kullanımı"
        verbose_name_plural = "Hediye Çeki Kullanımları"
        ordering = ['-kullanim_tarihi']
    
    def __str__(self):
        return f"{self.hediye_ceki.kod} - {self.kullanilan_tutar} ₺"
