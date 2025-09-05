#!/usr/bin/env python
"""
Giyim mağazası için veritabanını temizleme ve örnek veri ekleme scripti
"""
import os
import sys
import django

# Django ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stoktakip.settings')
django.setup()

from django.contrib.auth import get_user_model
from urun.models import UrunKategoriUst, Marka, Urun, UrunVaryanti, Beden, Renk
from gider.models import GiderKategori, Gider
from musteri.models import Musteri
from satis.models import Satis, SatisDetay, Odeme
from hediye.models import HediyeCeki

User = get_user_model()

def temizle_veritabani():
    """Admin kullanıcısı dışındaki tüm verileri temizle"""
    print("Veritabanı temizleniyor...")
    
    # Satış ve ödeme kayıtları
    Odeme.objects.all().delete()
    SatisDetay.objects.all().delete()
    Satis.objects.all().delete()
    
    # Ürün ve varyasyonlar
    UrunVaryanti.objects.all().delete()
    Urun.objects.all().delete()
    
    # Kategoriler ve markalar
    UrunKategoriUst.objects.all().delete()
    Marka.objects.all().delete()
    
    # Beden ve renkler
    Beden.objects.all().delete()
    Renk.objects.all().delete()
    
    # Giderler
    Gider.objects.all().delete()
    GiderKategori.objects.all().delete()
    
    # Hediye çekleri
    HediyeCeki.objects.all().delete()
    
    # Müşteriler
    Musteri.objects.all().delete()
    
    # Admin dışındaki kullanıcılar
    User.objects.exclude(is_superuser=True).delete()
    
    print("✅ Veritabanı temizlendi!")

def olustur_renkler():
    """Ana renkleri oluştur"""
    print("Renkler oluşturuluyor...")
    
    renkler = [
        ('Siyah', 'S'), ('Beyaz', 'B'), ('Gri', 'G'), ('Lacivert', 'L'), ('Mavi', 'M'),
        ('Kırmızı', 'K'), ('Yeşil', 'Y'), ('Sarı', 'A'), ('Turuncu', 'T'), ('Mor', 'O'),
        ('Pembe', 'P'), ('Kahverengi', 'H'), ('Bej', 'E'), ('Krem', 'R'), ('Bordo', 'D')
    ]
    
    for renk_adi, renk_kod in renkler:
        Renk.objects.create(ad=renk_adi, kod=renk_kod)
    
    print(f"✅ {len(renkler)} renk oluşturuldu!")

def olustur_bedenler():
    """Rakam ve harf bedenlerini oluştur"""
    print("Bedenler oluşturuluyor...")
    
    # Harf bedenleri
    harf_bedenleri = [
        ('XS', 'A'), ('S', 'B'), ('M', 'C'), ('L', 'D'), 
        ('XL', 'E'), ('XXL', 'F'), ('XXXL', 'G')
    ]
    
    # Rakam bedenleri (Giyim)
    rakam_bedenleri_giyim = [
        ('34', 'H'), ('36', 'I'), ('38', 'J'), ('40', 'K'), ('42', 'L'), 
        ('44', 'M'), ('46', 'N'), ('48', 'O'), ('50', 'P'), ('52', 'Q')
    ]
    
    # Ayakkabı bedenleri
    ayakkabi_bedenleri = [
        ('36 (Ayakkabı)', 'R'), ('37 (Ayakkabı)', 'S'), ('38 (Ayakkabı)', 'T'), 
        ('39 (Ayakkabı)', 'U'), ('40 (Ayakkabı)', 'V'), ('41 (Ayakkabı)', 'W'), 
        ('42 (Ayakkabı)', 'X'), ('43 (Ayakkabı)', 'Y'), ('44 (Ayakkabı)', 'Z'), 
        ('45 (Ayakkabı)', '1')
    ]
    
    for beden_ad, beden_kod in harf_bedenleri:
        Beden.objects.create(ad=beden_ad, kod=beden_kod, tip='harf')
    
    for beden_ad, beden_kod in rakam_bedenleri_giyim:
        Beden.objects.create(ad=beden_ad, kod=beden_kod, tip='rakam')
    
    for beden_ad, beden_kod in ayakkabi_bedenleri:
        Beden.objects.create(ad=beden_ad, kod=beden_kod, tip='rakam')
    
    print(f"✅ {len(harf_bedenleri + rakam_bedenleri_giyim + ayakkabi_bedenleri)} beden oluşturuldu!")

def olustur_markalar():
    """Giyim markalarını oluştur"""
    print("Markalar oluşturuluyor...")
    
    markalar = [
        'Nike', 'Adidas', 'Zara', 'H&M', 'LC Waikiki',
        'Koton', 'Defacto', 'Mango', 'Pull & Bear', 'Bershka',
        'Colin\'s', 'LTB', 'Levi\'s', 'Tommy Hilfiger', 'Lacoste',
        'Polo Ralph Lauren', 'Calvin Klein', 'Puma', 'Under Armour', 'Reebok'
    ]
    
    for marka_adi in markalar:
        Marka.objects.create(ad=marka_adi)
    
    print(f"✅ {len(markalar)} marka oluşturuldu!")

def olustur_kategoriler():
    """Giyim kategorilerini oluştur"""
    print("Kategoriler oluşturuluyor...")
    
    kategoriler = [
        'T-Shirt', 'Gömlek', 'Pantolon', 'Etek', 'Elbise',
        'Sweatshirt', 'Hırka', 'Ceket', 'Mont', 'Ayakkabı',
        'Çanta', 'Kemer', 'Şapka', 'Çorap', 'İç Giyim',
        'Gecelik', 'Pijama', 'Mayo', 'Bikini', 'Eşofman'
    ]
    
    for kategori_adi in kategoriler:
        UrunKategoriUst.objects.create(ad=kategori_adi)
    
    print(f"✅ {len(kategoriler)} kategori oluşturuldu!")

def olustur_gider_kategorileri():
    """Gider kategorilerini oluştur"""
    print("Gider kategorileri oluşturuluyor...")
    
    gider_kategorileri = [
        'Kira', 'Elektrik', 'Su', 'Doğalgaz', 'Telefon',
        'İnternet', 'Personel Maaşı', 'SGK Primleri', 'Vergi',
        'Muhasebe', 'Temizlik', 'Güvenlik', 'Reklam', 'Nakliye',
        'Ambalaj', 'Kırtasiye', 'Bakım-Onarım', 'Sigorta', 'Çay-Kahve', 'Diğer'
    ]
    
    for kategori_adi in gider_kategorileri:
        GiderKategori.objects.create(ad=kategori_adi)
    
    print(f"✅ {len(gider_kategorileri)} gider kategorisi oluşturuldu!")

def olustur_ornek_urunler():
    """Örnek ürünler oluştur"""
    print("Örnek ürünler oluşturuluyor...")
    
    # Markaları ve kategorileri al
    markalar = list(Marka.objects.all())
    kategoriler = list(UrunKategoriUst.objects.all())
    renkler = list(Renk.objects.all())
    bedenler = list(Beden.objects.all())
    
    # Örnek ürünler
    ornek_urunler = [
        {
            'ad': 'Erkek Basic T-Shirt',
            'marka': 'Nike',
            'kategori': 'T-Shirt',
            'alis_fiyati': 45.00,
            'satis_fiyati': 89.90
        },
        {
            'ad': 'Kadın Slim Fit Pantolon',
            'marka': 'Zara',
            'kategori': 'Pantolon',
            'alis_fiyati': 120.00,
            'satis_fiyati': 249.90
        },
        {
            'ad': 'Unisex Sweatshirt',
            'marka': 'Adidas',
            'kategori': 'Sweatshirt',
            'alis_fiyati': 180.00,
            'satis_fiyati': 349.90
        },
        {
            'ad': 'Kadın Elbise',
            'marka': 'H&M',
            'kategori': 'Elbise',
            'alis_fiyati': 75.00,
            'satis_fiyati': 159.90
        },
        {
            'ad': 'Erkek Spor Ayakkabı',
            'marka': 'Nike',
            'kategori': 'Ayakkabı',
            'alis_fiyati': 250.00,
            'satis_fiyati': 499.90
        },
        {
            'ad': 'Kadın Deri Çanta',
            'marka': 'Mango',
            'kategori': 'Çanta',
            'alis_fiyati': 150.00,
            'satis_fiyati': 299.90
        },
        {
            'ad': 'Erkek Kot Pantolon',
            'marka': 'Levi\'s',
            'kategori': 'Pantolon',
            'alis_fiyati': 200.00,
            'satis_fiyati': 399.90
        },
        {
            'ad': 'Kadın Bluz',
            'marka': 'Koton',
            'kategori': 'Gömlek',
            'alis_fiyati': 60.00,
            'satis_fiyati': 129.90
        }
    ]
    
    for urun_data in ornek_urunler:
        # Marka ve kategori bul
        marka = next((m for m in markalar if m.ad == urun_data['marka']), markalar[0])
        kategori = next((k for k in kategoriler if k.ad == urun_data['kategori']), kategoriler[0])
        
        # Ürün oluştur
        urun = Urun.objects.create(
            ad=urun_data['ad'],
            kategori=kategori,
            marka=marka,
            alis_fiyati=urun_data['alis_fiyati'],
            satis_fiyati=urun_data['satis_fiyati'],
            varyasyonlu=True
        )
        
        # Her ürün için birkaç varyasyon oluştur
        import random
        secilen_renkler = random.sample(renkler, min(3, len(renkler)))
        secilen_bedenler = random.sample(bedenler, min(4, len(bedenler)))
        
        for renk in secilen_renkler:
            for beden in secilen_bedenler:
                UrunVaryanti.objects.create(
                    urun=urun,
                    renk=renk,
                    beden=beden,
                    stok_miktari=random.randint(5, 25)
                )
    
    print(f"✅ {len(ornek_urunler)} ürün ve varyasyonları oluşturuldu!")

def olustur_ornek_musteriler():
    """Örnek müşteriler oluştur"""
    print("Örnek müşteriler oluşturuluyor...")
    
    musteriler = [
        {
            'ad': 'Ahmet',
            'soyad': 'Yılmaz',
            'telefon': '0532 123 45 67',
            'email': 'ahmet.yilmaz@email.com'
        },
        {
            'ad': 'Ayşe',
            'soyad': 'Kaya',
            'telefon': '0533 234 56 78',
            'email': 'ayse.kaya@email.com'
        },
        {
            'ad': 'Mehmet',
            'soyad': 'Demir',
            'telefon': '0534 345 67 89',
            'email': 'mehmet.demir@email.com'
        },
        {
            'ad': 'Fatma',
            'soyad': 'Şahin',
            'telefon': '0535 456 78 90',
            'email': 'fatma.sahin@email.com'
        },
        {
            'ad': 'Ali',
            'soyad': 'Özkan',
            'telefon': '0536 567 89 01',
            'email': 'ali.ozkan@email.com'
        }
    ]
    
    for musteri_data in musteriler:
        Musteri.objects.create(**musteri_data)
    
    print(f"✅ {len(musteriler)} müşteri oluşturuldu!")

def main():
    """Ana fonksiyon"""
    print("🧹 Giyim Mağazası Veritabanı Kurulum Scripti")
    print("=" * 50)
    
    # Veritabanını temizle
    temizle_veritabani()
    
    # Temel verileri oluştur
    olustur_renkler()
    olustur_bedenler()
    olustur_markalar()
    olustur_kategoriler()
    olustur_gider_kategorileri()
    
    # Örnek verileri oluştur
    olustur_ornek_urunler()
    olustur_ornek_musteriler()
    
    print("\n🎉 Giyim mağazası veritabanı başarıyla kuruldu!")
    print("✅ Sistem artık kullanıma hazır!")

if __name__ == '__main__':
    main()
