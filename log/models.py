from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AktiviteLog(models.Model):
    """Sistem aktivite logları"""
    AKTIVITE_TIPLERI = [
        ('ekleme', 'Ekleme'),
        ('guncelleme', 'Güncelleme'),
        ('silme', 'Silme'),
        ('satis', 'Satış'),
        ('stok_guncelleme', 'Stok Güncelleme'),
        ('giris', 'Kullanıcı Girişi'),
        ('cikis', 'Kullanıcı Çıkışı'),
        ('rapor', 'Rapor Oluşturma'),
        ('iade', 'İade İşlemi'),
        ('iptal', 'İptal İşlemi'),
    ]
    
    # Kullanıcı bilgisi
    kullanici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Kullanıcı")
    
    # Aktivite bilgisi
    aktivite_tipi = models.CharField(max_length=20, choices=AKTIVITE_TIPLERI, verbose_name="Aktivite Tipi")
    baslik = models.CharField(max_length=200, verbose_name="Başlık")
    aciklama = models.TextField(verbose_name="Açıklama")
    
    # İlgili obje (Generic Foreign Key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # IP ve tarayıcı bilgisi
    ip_adresi = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Adresi")
    tarayici_bilgisi = models.TextField(null=True, blank=True, verbose_name="Tarayıcı Bilgisi")
    
    # Eski ve yeni değerler (JSON formatında)
    eski_degerler = models.JSONField(null=True, blank=True, verbose_name="Eski Değerler")
    yeni_degerler = models.JSONField(null=True, blank=True, verbose_name="Yeni Değerler")
    
    # Tarih bilgisi
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")

    class Meta:
        verbose_name = "Aktivite Log"
        verbose_name_plural = "Aktivite Logları"
        ordering = ['-tarih']

    def __str__(self):
        kullanici_adi = self.kullanici.username if self.kullanici else "Bilinmeyen"
        return f"{kullanici_adi} - {self.get_aktivite_tipi_display()} - {self.baslik}"

    @classmethod
    def log_aktivite(cls, kullanici, aktivite_tipi, baslik, aciklama, 
                     content_object=None, ip_adresi=None, tarayici_bilgisi=None, 
                     eski_degerler=None, yeni_degerler=None):
        """Aktivite log kaydı oluştur"""
        log = cls.objects.create(
            kullanici=kullanici,
            aktivite_tipi=aktivite_tipi,
            baslik=baslik,
            aciklama=aciklama,
            content_object=content_object,
            ip_adresi=ip_adresi,
            tarayici_bilgisi=tarayici_bilgisi,
            eski_degerler=eski_degerler,
            yeni_degerler=yeni_degerler
        )
        return log


class SistemHatasi(models.Model):
    """Sistem hataları için log"""
    HATA_SEVIYELERI = [
        ('bilgi', 'Bilgi'),
        ('uyari', 'Uyarı'),
        ('hata', 'Hata'),
        ('kritik', 'Kritik'),
    ]
    
    seviye = models.CharField(max_length=10, choices=HATA_SEVIYELERI, verbose_name="Hata Seviyesi")
    baslik = models.CharField(max_length=200, verbose_name="Başlık")
    mesaj = models.TextField(verbose_name="Hata Mesajı")
    dosya_yolu = models.CharField(max_length=500, null=True, blank=True, verbose_name="Dosya Yolu")
    satir_no = models.PositiveIntegerField(null=True, blank=True, verbose_name="Satır No")
    
    # Stack trace
    stack_trace = models.TextField(null=True, blank=True, verbose_name="Stack Trace")
    
    # Kullanıcı ve istek bilgisi
    kullanici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kullanıcı")
    ip_adresi = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Adresi")
    url = models.CharField(max_length=500, null=True, blank=True, verbose_name="URL")
    http_method = models.CharField(max_length=10, null=True, blank=True, verbose_name="HTTP Method")
    
    # Çözüldü mü?
    cozuldu = models.BooleanField(default=False, verbose_name="Çözüldü")
    cozum_notu = models.TextField(null=True, blank=True, verbose_name="Çözüm Notu")
    
    # Tarih bilgisi
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")

    class Meta:
        verbose_name = "Sistem Hatası"
        verbose_name_plural = "Sistem Hataları"
        ordering = ['-tarih']

    def __str__(self):
        return f"{self.get_seviye_display()} - {self.baslik}"


class LoginLog(models.Model):
    """Kullanıcı giriş logları"""
    kullanici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    giris_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Giriş Tarihi")
    cikis_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Çıkış Tarihi")
    ip_adresi = models.GenericIPAddressField(verbose_name="IP Adresi")
    tarayici_bilgisi = models.TextField(verbose_name="Tarayıcı Bilgisi")
    basarili = models.BooleanField(default=True, verbose_name="Başarılı")
    hata_mesaji = models.TextField(null=True, blank=True, verbose_name="Hata Mesajı")

    class Meta:
        verbose_name = "Giriş Log"
        verbose_name_plural = "Giriş Logları"
        ordering = ['-giris_tarihi']

    def __str__(self):
        durum = "Başarılı" if self.basarili else "Başarısız"
        return f"{self.kullanici.username} - {durum} - {self.giris_tarihi}"

    @property
    def oturum_suresi(self):
        """Oturum süresi hesapla"""
        if self.cikis_tarihi:
            return self.cikis_tarihi - self.giris_tarihi
        return None
