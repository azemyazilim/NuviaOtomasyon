from django.db import models
from django.conf import settings
from django.utils import timezone


class Musteri(models.Model):
    """Müşteri bilgileri modeli"""
    # Kişisel bilgiler
    ad = models.CharField(max_length=100, verbose_name="Ad")
    soyad = models.CharField(max_length=100, verbose_name="Soyad")
    telefon = models.CharField(max_length=20, unique=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, null=True, verbose_name="E-posta")
    
    # Adres bilgileri
    adres = models.TextField(blank=True, null=True, verbose_name="Adres")
    il = models.CharField(max_length=50, blank=True, null=True, verbose_name="İl")
    ilce = models.CharField(max_length=50, blank=True, null=True, verbose_name="İlçe")
    posta_kodu = models.CharField(max_length=10, blank=True, null=True, verbose_name="Posta Kodu")
    
    # Müşteri kategorisi
    MUSTERI_TIPI = [
        ('bireysel', 'Bireysel'),
        ('kurumsal', 'Kurumsal'),
    ]
    tip = models.CharField(max_length=20, choices=MUSTERI_TIPI, default='bireysel', verbose_name="Müşteri Tipi")
    
    # Kurumsal müşteriler için
    firma_adi = models.CharField(max_length=200, blank=True, null=True, verbose_name="Firma Adı")
    vergi_no = models.CharField(max_length=20, blank=True, null=True, verbose_name="Vergi No")
    vergi_dairesi = models.CharField(max_length=100, blank=True, null=True, verbose_name="Vergi Dairesi")
    
    # Bireysel müşteriler için
    tc_no = models.CharField(max_length=11, blank=True, null=True, verbose_name="TC Kimlik No")
    
    # Doğum günü (isteğe bağlı - promosyonlar için)
    dogum_tarihi = models.DateField(blank=True, null=True, verbose_name="Doğum Tarihi")
    
    # Açık hesap bilgileri
    acik_hesap_bakiye = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Açık Hesap Bakiyesi")
    acik_hesap_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Açık Hesap Limiti")
    
    # Durum bilgisi
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    # Notlar
    notlar = models.TextField(blank=True, null=True, verbose_name="Notlar")
    
    # Tarih bilgileri
    kayit_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")
    kaydeden = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kaydeden")

    class Meta:
        verbose_name = "Müşteri"
        verbose_name_plural = "Müşteriler"
        ordering = ['ad', 'soyad']

    def __str__(self):
        if self.tip == 'kurumsal' and self.firma_adi:
            return f"{self.firma_adi} ({self.ad} {self.soyad})"
        return f"{self.ad} {self.soyad}"

    @property
    def tam_ad(self):
        """Tam ad"""
        return f"{self.ad} {self.soyad}"

    @property
    def tam_adres(self):
        """Tam adres"""
        adres_parts = []
        if self.adres:
            adres_parts.append(self.adres)
        if self.ilce:
            adres_parts.append(self.ilce)
        if self.il:
            adres_parts.append(self.il)
        if self.posta_kodu:
            adres_parts.append(self.posta_kodu)
        return ", ".join(adres_parts)

    @property
    def toplam_satis_tutari(self):
        """Bu müşterinin toplam satış tutarı"""
        from satis.models import Satis
        satislar = Satis.objects.filter(musteri=self, durum='tamamlandi')
        return sum([satis.toplam_tutar for satis in satislar])

    @property
    def satis_sayisi(self):
        """Bu müşterinin toplam satış sayısı"""
        from satis.models import Satis
        return Satis.objects.filter(musteri=self, durum='tamamlandi').count()

    @property
    def son_satis_tarihi(self):
        """Son satış tarihi"""
        from satis.models import Satis
        son_satis = Satis.objects.filter(musteri=self, durum='tamamlandi').first()
        return son_satis.satis_tarihi if son_satis else None
    
    @property 
    def toplam_borc(self):
        """Müşterinin toplam borcu (pozitif değer)"""
        return max(0, self.acik_hesap_bakiye)
    
    @property
    def veresiye_satislar(self):
        """Ödenmemiş veresiye satışları"""
        from satis.models import Satis, Odeme
        
        # Açık hesap ödemesi olan satışları bul
        acik_hesap_satis_ids = Odeme.objects.filter(
            odeme_tipi='acik_hesap'
        ).values_list('satis_id', flat=True)
        
        return Satis.objects.filter(
            id__in=acik_hesap_satis_ids,
            musteri=self,
            durum='tamamlandi'
        )
    
    @property
    def son_tahsilat_tarihi(self):
        """Son tahsilat tarihi"""
        son_tahsilat = self.tahsilat_set.filter(durum='tahsil_edildi').first()
        return son_tahsilat.tahsilat_tarihi if son_tahsilat else None
    
    def borc_hareket_ekle(self, tutar, aciklama, satis_id=None, user=None):
        """Borç hareketi ekle"""
        onceki_bakiye = self.acik_hesap_bakiye
        self.acik_hesap_bakiye += tutar
        self.save()
        
        BorcAlacakHareket.objects.create(
            musteri=self,
            hareket_tipi='borc',
            tutar=tutar,
            satis_id=satis_id,
            onceki_bakiye=onceki_bakiye,
            yeni_bakiye=self.acik_hesap_bakiye,
            aciklama=aciklama,
            islem_yapan=user
        )
    
    def alacak_hareket_ekle(self, tutar, aciklama, tahsilat=None, user=None):
        """Alacak (tahsilat) hareketi ekle"""
        onceki_bakiye = self.acik_hesap_bakiye
        self.acik_hesap_bakiye -= tutar
        self.save()
        
        BorcAlacakHareket.objects.create(
            musteri=self,
            hareket_tipi='alacak',
            tutar=tutar,
            tahsilat=tahsilat,
            onceki_bakiye=onceki_bakiye,
            yeni_bakiye=self.acik_hesap_bakiye,
            aciklama=aciklama,
            islem_yapan=user
        )


class MusteriGruplar(models.Model):
    """Müşteri grupları (VIP, Toptan, vb.)"""
    ad = models.CharField(max_length=100, unique=True, verbose_name="Grup Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    indirim_orani = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="İndirim Oranı (%)")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Müşteri Grup"
        verbose_name_plural = "Müşteri Grupları"
        ordering = ['ad']

    def __str__(self):
        return self.ad


class MusteriGrupUyelik(models.Model):
    """Müşteri grup üyelikleri"""
    musteri = models.ForeignKey(Musteri, on_delete=models.CASCADE, verbose_name="Müşteri")
    grup = models.ForeignKey(MusteriGruplar, on_delete=models.CASCADE, verbose_name="Grup")
    baslama_tarihi = models.DateField(verbose_name="Başlama Tarihi")
    bitis_tarihi = models.DateField(blank=True, null=True, verbose_name="Bitiş Tarihi")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")

    class Meta:
        verbose_name = "Müşteri Grup Üyelik"
        verbose_name_plural = "Müşteri Grup Üyelikleri"
        unique_together = ['musteri', 'grup']

    def __str__(self):
        return f"{self.musteri} - {self.grup}"


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
