from django.shortcuts import render
from django.http import HttpResponse
from datetime import date, datetime
from django.db.models import Sum, Count, Q
from satis.models import Satis, SatisDetay, Odeme
from urun.models import UrunVaryanti
from musteri.models import Musteri
from gider.models import Gider
from kasa.models import Kasa, KasaHareket

def dashboard_view(request):
    context = {'bugun': date.today(), 'toplam_urun': 0, 'toplam_musteri': 0, 'bugunki_satis': 0, 'bugunki_gider_toplam': 0}
    return render(request, 'dashboard.html', context)

def gunluk_rapor_view(request):
    # Tarih parametresi
    tarih = request.GET.get('tarih', date.today().strftime('%Y-%m-%d'))
    
    try:
        secili_tarih = datetime.strptime(tarih, '%Y-%m-%d').date()
    except ValueError:
        secili_tarih = date.today()
    
    # Günlük satışlar
    gunluk_satislar = Satis.objects.filter(
        satis_tarihi__date=secili_tarih,
        durum='tamamlandi'
    )
    
    # Satış istatistikleri
    toplam_satis = gunluk_satislar.aggregate(
        toplam_tutar=Sum('toplam_tutar'),
        satis_adedi=Count('id')
    )
    
    # Ödeme yöntemi bazında satışlar
    nakit_satislar = Odeme.objects.filter(
        satis__satis_tarihi__date=secili_tarih,
        satis__durum='tamamlandi',
        odeme_tipi='nakit'
    ).aggregate(
        toplam=Sum('tutar'), 
        adet=Count('id')
    )
    
    kart_satislar = Odeme.objects.filter(
        satis__satis_tarihi__date=secili_tarih,
        satis__durum='tamamlandi',
        odeme_tipi='kart'
    ).aggregate(
        toplam=Sum('tutar'), 
        adet=Count('id')
    )
    
    hediye_ceki_satislar = Odeme.objects.filter(
        satis__satis_tarihi__date=secili_tarih,
        satis__durum='tamamlandi',
        odeme_tipi='hediye_ceki'
    ).aggregate(
        toplam=Sum('tutar'), 
        adet=Count('id')
    )
    
    # En çok satan ürünler
    en_cok_satan_urunler = SatisDetay.objects.filter(
        satis__satis_tarihi__date=secili_tarih,
        satis__durum='tamamlandi'
    ).values(
        'varyant__urun__ad',
        'varyant__renk__ad',
        'varyant__beden__ad'
    ).annotate(
        toplam_adet=Sum('miktar'),
        toplam_tutar=Sum('toplam_fiyat')
    ).order_by('-toplam_adet')[:10]
    
    # Günlük giderler
    gunluk_giderler = Gider.objects.filter(tarih=secili_tarih)
    toplam_gider = gunluk_giderler.aggregate(toplam=Sum('tutar'))
    
    # Kar hesaplama
    toplam_satis_tutari = toplam_satis['toplam_tutar'] or 0
    toplam_gider_tutari = toplam_gider['toplam'] or 0
    net_kar = toplam_satis_tutari - toplam_gider_tutari
    
    # Kasa bilgileri
    kasalar = Kasa.objects.filter(aktif=True)
    kasa_durumu = []
    
    for kasa in kasalar:
        # Günlük kasa hareketleri
        gunluk_hareketler = KasaHareket.objects.filter(
            kasa=kasa,
            tarih__date=secili_tarih
        )
        
        gunluk_giris = gunluk_hareketler.filter(
            tip='giris'
        ).aggregate(toplam=Sum('tutar'))['toplam'] or 0
        
        gunluk_cikis = gunluk_hareketler.filter(
            tip='cikis'
        ).aggregate(toplam=Sum('tutar'))['toplam'] or 0
        
        gunluk_net = gunluk_giris - gunluk_cikis
        
        kasa_durumu.append({
            'kasa': kasa,
            'gunluk_giris': gunluk_giris,
            'gunluk_cikis': gunluk_cikis,
            'gunluk_net': gunluk_net,
            'mevcut_bakiye': kasa.bakiye()
        })
    
    # Template için uyumlu değişken adları
    satis_ozeti = {
        'toplam_satis_tutari': toplam_satis_tutari,
        'toplam_satis_sayisi': toplam_satis['satis_adedi'] or 0
    }
    
    gider_ozeti = {
        'toplam_gider_tutari': toplam_gider_tutari,
        'toplam_gider_sayisi': gunluk_giderler.count()
    }
    
    toplam_tahsilat = toplam_satis_tutari
    brut_kar = net_kar
    
    context = {
        'secili_tarih': secili_tarih,
        'toplam_satis': toplam_satis,
        'nakit_satislar': nakit_satislar,
        'kart_satislar': kart_satislar,
        'hediye_ceki_satislar': hediye_ceki_satislar,
        'en_cok_satan_urunler': en_cok_satan_urunler,
        'gunluk_giderler': gunluk_giderler,
        'toplam_gider': toplam_gider,
        'net_kar': net_kar,
        'gunluk_satislar': gunluk_satislar,
        'kasa_durumu': kasa_durumu,
        # Template uyumlu değişkenler
        'satis_ozeti': satis_ozeti,
        'gider_ozeti': gider_ozeti,
        'toplam_tahsilat': toplam_tahsilat,
        'brut_kar': brut_kar,
    }
    
    return render(request, 'gunluk_rapor.html', context)

def gunluk_rapor_pdf_view(request):
    return HttpResponse('PDF not available')
