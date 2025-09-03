from django.db import models
from django.conf import settings
from django.utils import timezone
from urun.models import Urun
from musteri.models import Musteri


class SiparisNumarasi(models.Model):
    """Sipariş numarası sayacı için model"""
    yil = models.PositiveIntegerField(verbose_name="Yıl")
    ay = models.PositiveIntegerField(verbose_name="Ay")
    gun = models.PositiveIntegerField(verbose_name="Gün")
    sayac = models.PositiveIntegerField(default=0, verbose_name="Günlük Sayaç")
    
    class Meta:
        unique_together = ('yil', 'ay', 'gun')
        verbose_name = "Sipariş Numarası"
        verbose_name_plural = "Sipariş Numaraları"
    
    @classmethod
    def sonraki_numara_preview(cls):
        """Sonraki sipariş numarasını preview olarak göster (sayacı artırmaz)"""
        import datetime
        bugun = datetime.date.today()
        
        try:
            obj = cls.objects.get(
                yil=bugun.year,
                ay=bugun.month, 
                gun=bugun.day
            )
            sonraki_numara = obj.sayac + 1
        except cls.DoesNotExist:
            sonraki_numara = 1
        
        return f"SP{bugun.strftime('%Y%m%d')}{sonraki_numara:04d}"
    
    @classmethod
    def sonraki_numara(cls):
        """Sonraki sipariş numarasını oluştur ve sayacı artır"""
        from django.db import transaction
        import datetime
        
        bugun = datetime.date.today()
        
        with transaction.atomic():
            # SELECT FOR UPDATE kullanarak race condition'ı önle
            obj, created = cls.objects.select_for_update().get_or_create(
                yil=bugun.year,
                ay=bugun.month, 
                gun=bugun.day,
                defaults={'sayac': 0}
            )
            
            obj.sayac += 1
            obj.save()
            
            return f"SP{bugun.strftime('%Y%m%d')}{obj.sayac:04d}"


class Satis(models.Model):
    """Ana satış modeli"""
    SATIS_DURUMU = [
        ('beklemede', 'Beklemede'),
        ('tamamlandi', 'Tamamlandı'),
        ('iade', 'İade'),
        ('iptal', 'İptal'),
    ]
    
    # Sipariş bilgileri
    siparis_no = models.CharField(max_length=20, unique=True, verbose_name="Sipariş No", null=True, blank=True)
    satis_no = models.CharField(max_length=20, unique=True, verbose_name="Satış No", null=True, blank=True)
    musteri = models.ForeignKey(Musteri, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Müşteri")
    
    # Tutar bilgileri
    ara_toplam = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ara Toplam")
    indirim_tutari = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="İndirim Tutarı")
    kdv_orani = models.DecimalField(max_digits=5, decimal_places=2, default=18.00, verbose_name="KDV Oranı (%)")
    kdv_tutari = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="KDV Tutarı")
    genel_toplam = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Genel Toplam")
    toplam_tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Toplam Tutar")
    
    # Durum ve tarih bilgileri
    durum = models.CharField(max_length=20, choices=SATIS_DURUMU, default='beklemede', verbose_name="Durum")
    siparis_tarihi = models.DateTimeField(default=timezone.now, verbose_name="Sipariş Tarihi")
    satis_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Satış Tarihi")
    satici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Satıcı")
    
    # Notlar
    notlar = models.TextField(blank=True, null=True, verbose_name="Notlar")

    class Meta:
        verbose_name = "Satış"
        verbose_name_plural = "Satışlar"
        ordering = ['-siparis_tarihi']

    def __str__(self):
        return f"Sipariş {self.siparis_no} - {self.toplam_tutar} TL"

    def save(self, *args, **kwargs):
        # Sipariş numarası otomatik oluştur
        if not self.siparis_no:
            from django.db import transaction, IntegrityError
            max_retries = 10
            for attempt in range(max_retries):
                try:
                    with transaction.atomic():
                        # Sipariş numarasını al
                        temp_siparis_no = SiparisNumarasi.sonraki_numara()
                        
                        # Aynı numaraya sahip başka satış var mı kontrol et
                        if not Satis.objects.filter(siparis_no=temp_siparis_no).exists():
                            self.siparis_no = temp_siparis_no
                            break
                        else:
                            # Eğer numara kullanılmışsa bir sonrakini dene
                            continue
                            
                except IntegrityError as e:
                    if attempt == max_retries - 1:  # Son deneme
                        # Fallback: timestamp ekleyerek unique yap
                        import time
                        self.siparis_no = f"SP{int(time.time())}"
                        break
                    continue
                except Exception as e:
                    if attempt == max_retries - 1:  # Son deneme
                        raise e
                    continue
        
        # Satış numarası (ödeme tamamlandığında oluşturulur)
        if not self.satis_no and self.durum == 'tamamlandi':
            import datetime
            today = datetime.date.today()
            
            # Race condition'ı önlemek için retry mekanizması
            max_attempts = 10
            for attempt in range(max_attempts):
                # Bugün tamamlanan satışları say
                existing_count = Satis.objects.filter(
                    satis_tarihi__date=today, 
                    durum='tamamlandi',
                    satis_no__isnull=False
                ).count()
                
                # Yeni satis_no oluştur
                new_satis_no = f"S{today.strftime('%Y%m%d')}{(existing_count + 1):04d}"
                
                # Bu satis_no daha önce kullanılmış mı kontrol et
                if not Satis.objects.filter(satis_no=new_satis_no).exists():
                    self.satis_no = new_satis_no
                    break
                else:
                    # Eğer varsa bir sonrakini dene
                    continue
            
            # Eğer hiçbir attempt başarılı olamazsa timestamp ekle
            if not self.satis_no:
                from django.utils import timezone
                timestamp = timezone.now().strftime('%H%M%S')
                self.satis_no = f"S{today.strftime('%Y%m%d')}{timestamp}"
            
            if not self.satis_tarihi:
                self.satis_tarihi = timezone.now()
        
        # KDV tutarını hesapla
        self.kdv_tutari = self.ara_toplam * (self.kdv_orani / 100)
        self.toplam_tutar = self.ara_toplam + self.kdv_tutari
        
        super().save(*args, **kwargs)

    @property
    def toplam_urun_adedi(self):
        """Satıştaki toplam ürün adedi"""
        return sum([item.miktar for item in self.satisdetay_set.all()])

    @property
    def kar_tutari(self):
        """Bu satıştan elde edilen toplam kar"""
        toplam_kar = 0
        for item in self.satisdetay_set.all():
            alis_fiyati = item.urun.alis_fiyati * item.miktar
            satis_fiyati = item.birim_fiyat * item.miktar
            toplam_kar += (satis_fiyati - alis_fiyati)
        return toplam_kar

    @property
    def odeme_detaylari(self):
        """Ödeme detaylarını getir"""
        return self.odeme_set.all()

    @property
    def toplam_odenen(self):
        """Toplam ödenen tutarı hesapla"""
        return sum([odeme.tutar for odeme in self.odeme_set.all()])

    @property
    def kalan_tutar(self):
        """Kalan ödenmesi gereken tutar"""
        return max(0, self.genel_toplam - self.toplam_odenen)

    @property
    def para_ustu(self):
        """Para üstü tutarı"""
        return max(0, self.toplam_odenen - self.genel_toplam)


class Odeme(models.Model):
    """Ödeme bilgileri modeli"""
    ODEME_TIPLERI = [
        ('nakit', 'Nakit'),
        ('kart', 'Kart'),
        ('hediye_ceki', 'Hediye Çeki'),
        ('acik_hesap', 'Açık Hesap'),
    ]
    
    satis = models.ForeignKey(Satis, on_delete=models.CASCADE, verbose_name="Satış")
    odeme_tipi = models.CharField(max_length=20, choices=ODEME_TIPLERI, verbose_name="Ödeme Tipi")
    tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tutar")
    
    # Kart ödemesi detayları
    taksit_sayisi = models.PositiveIntegerField(null=True, blank=True, verbose_name="Taksit Sayısı")
    taksit_tutari = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Taksit Tutarı")
    
    # Hediye çeki detayları
    hediye_ceki_kodu = models.CharField(max_length=50, null=True, blank=True, verbose_name="Hediye Çeki Kodu")
    
    # Para üstü (sadece nakit ödemede)
    para_ustu = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Para Üstü")
    
    # Tarih bilgileri
    odeme_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Ödeme Tarihi")
    
    class Meta:
        verbose_name = "Ödeme"
        verbose_name_plural = "Ödemeler"
        ordering = ['-odeme_tarihi']
    
    def __str__(self):
        return f"{self.satis.siparis_no} - {self.get_odeme_tipi_display()} - {self.tutar} TL"
    
    def save(self, *args, **kwargs):
        # Kart taksit tutarını hesapla
        if self.odeme_tipi == 'kart' and self.taksit_sayisi and self.taksit_sayisi > 1:
            self.taksit_tutari = self.tutar / self.taksit_sayisi
        
        super().save(*args, **kwargs)


class SatisDetay(models.Model):
    """Satış detay modeli - her ürün için ayrı kayıt"""
    satis = models.ForeignKey(Satis, on_delete=models.CASCADE, verbose_name="Satış")
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Ürün")
    miktar = models.PositiveIntegerField(verbose_name="Miktar")
    birim_fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Birim Fiyat")
    toplam_fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Toplam Fiyat")
    
    # İndirim bilgisi (isteğe bağlı)
    indirim_orani = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="İndirim Oranı (%)")
    indirim_tutari = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="İndirim Tutarı")

    class Meta:
        verbose_name = "Satış Detay"
        verbose_name_plural = "Satış Detayları"

    def __str__(self):
        return f"{self.satis.satis_no} - {self.urun.ad} x{self.miktar}"

    def save(self, *args, **kwargs):
        # Toplam fiyatı hesapla
        if not self.birim_fiyat:
            self.birim_fiyat = self.urun.satis_fiyati
        
        toplam_without_discount = self.birim_fiyat * self.miktar
        
        # İndirim hesaplaması
        if self.indirim_orani > 0:
            self.indirim_tutari = toplam_without_discount * (self.indirim_orani / 100)
        
        self.toplam_fiyat = toplam_without_discount - self.indirim_tutari
        
        super().save(*args, **kwargs)
        
        # Satış sonrası stok güncelle
        if self.pk:  # Sadece kayıt edildikten sonra
            self.urun.stok_miktari -= self.miktar
            self.urun.save()

    @property
    def ara_toplam(self):
        """Template uyumluluğu için ara_toplam property'si"""
        return self.toplam_fiyat
    
    @property
    def indirimsiz_toplam(self):
        """İndirim öncesi toplam tutar"""
        return self.birim_fiyat * self.miktar


class SatisIptal(models.Model):
    """İptal edilen satışlar için model"""
    satis = models.OneToOneField(Satis, on_delete=models.CASCADE, verbose_name="İptal Edilen Satış")
    iptal_nedeni = models.TextField(verbose_name="İptal Nedeni")
    iptal_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="İptal Tarihi")
    iptal_eden = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="İptal Eden")
    stok_iade_edildi = models.BooleanField(default=False, verbose_name="Stok İade Edildi")

    class Meta:
        verbose_name = "Satış İptal"
        verbose_name_plural = "Satış İptalleri"
        ordering = ['-iptal_tarihi']

    def __str__(self):
        return f"İptal - {self.satis.satis_no}"

    def save(self, *args, **kwargs):
        # İlk kayıtta stokları iade et
        if not self.pk and not self.stok_iade_edildi:
            for detay in self.satis.satisdetay_set.all():
                detay.urun.stok_miktari += detay.miktar
                detay.urun.save()
            self.stok_iade_edildi = True
        
        super().save(*args, **kwargs)
