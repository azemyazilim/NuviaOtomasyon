from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from .models import Satis, SatisDetay, Odeme, SiparisNumarasi
from urun.models import Urun, UrunVaryanti
from musteri.models import Musteri
from kasa.models import Kasa, KasaHareket


# @login_required  # TEST İÇİN GEÇİCİ OLARAK KALDIRILDI
def satis_ekrani(request):
    """Satış ekranı view'ı"""
    from django.db.models import Sum, Count
    from datetime import datetime, timedelta
    
    # URL'den müşteri ID'sini al
    musteri_id = request.GET.get('musteri')
    secili_musteri = None
    
    if musteri_id:
        try:
            secili_musteri = Musteri.objects.get(id=musteri_id, aktif=True)
        except Musteri.DoesNotExist:
            messages.warning(request, 'Seçilen müşteri bulunamadı.')
    
    # Bugünün tarih aralığı
    bugun = datetime.now().date()
    bugun_baslangic = datetime.combine(bugun, datetime.min.time())
    bugun_bitis = datetime.combine(bugun, datetime.max.time())
    
    # Bugünkü ödemeleri ödeme türüne göre topla
    bugunun_odeme_toplami = Odeme.objects.filter(
        odeme_tarihi__range=[bugun_baslangic, bugun_bitis]
    ).values('odeme_tipi').annotate(
        toplam_tutar=Sum('tutar'),
        toplam_adet=Count('id')
    ).order_by('odeme_tipi')
    
    # Sonraki sipariş numarasını preview olarak göster (sayacı artırmaz)
    siparis_no_preview = SiparisNumarasi.sonraki_numara_preview()
    
    context = {
        'title': 'Satış Ekranı',
        'secili_musteri': secili_musteri,
        'siparis_no': siparis_no_preview,
        'bugunun_odeme_toplami': bugunun_odeme_toplami,
    }
    return render(request, 'satis/satis_ekrani.html', context)


@login_required
def satis_listesi(request):
    """Satış listesi view'ı"""
    from django.db.models import Sum, Count, Avg
    from datetime import datetime
    
    satislar = Satis.objects.all().order_by('-siparis_tarihi')
    
    # Arama
    query = request.GET.get('q')
    if query:
        satislar = satislar.filter(
            Q(siparis_no__icontains=query) |
            Q(satis_no__icontains=query) |
            Q(musteri__ad__icontains=query) |
            Q(musteri__soyad__icontains=query)
        )
    
    # Tarih filtreleri
    tarih_baslangic = request.GET.get('tarih_baslangic')
    tarih_bitis = request.GET.get('tarih_bitis')
    
    if tarih_baslangic:
        try:
            baslangic = datetime.strptime(tarih_baslangic, '%Y-%m-%d').date()
            satislar = satislar.filter(siparis_tarihi__date__gte=baslangic)
        except ValueError:
            pass
    
    if tarih_bitis:
        try:
            bitis = datetime.strptime(tarih_bitis, '%Y-%m-%d').date()
            satislar = satislar.filter(siparis_tarihi__date__lte=bitis)
        except ValueError:
            pass
    
    # Durum filtresi
    durum = request.GET.get('durum')
    if durum:
        satislar = satislar.filter(durum=durum)
    
    # İstatistikler hesaplama
    istatistikler = satislar.aggregate(
        toplam_tutar=Sum('genel_toplam'),  # genel_toplam alanını kullan
        toplam_adet=Sum('satisdetay__miktar'),
        satış_sayısı=Count('id')
    )
    
    # Ortalama satışı manuel hesapla
    ortalama_satis = 0
    if istatistikler['satış_sayısı'] and istatistikler['satış_sayısı'] > 0:
        ortalama_satis = istatistikler['toplam_tutar'] / istatistikler['satış_sayısı']
    
    # Görünüm modu (card/table)
    view_mode = request.GET.get('view', 'card')  # varsayılan card görünümü
    
    # Sayfalama (görünüm moduna göre sayfa başına öğe sayısı)
    items_per_page = 12 if view_mode == 'card' else 20
    paginator = Paginator(satislar, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Sayfa toplamını hesapla
    sayfa_toplam_tutar = sum([satis.toplam_tutar for satis in page_obj])
    sayfa_toplam_adet = sum([satis.toplam_urun_adedi for satis in page_obj])
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'view_mode': view_mode,
        'toplam_tutar': istatistikler['toplam_tutar'] or 0,
        'toplam_adet': istatistikler['toplam_adet'] or 0,
        'sayfa_toplam_tutar': sayfa_toplam_tutar,
        'sayfa_toplam_adet': sayfa_toplam_adet,
        'ortalama_satis': ortalama_satis,
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
        'durum': durum,
    }
    return render(request, 'satis/satis_listesi.html', context)


@login_required
def satis_detay(request, pk):
    """Satış detay view'ı"""
    satis = get_object_or_404(Satis, pk=pk)
    satis_detaylari = satis.satisdetay_set.all().select_related('urun')
    
    # İndirim hesaplamaları
    toplam_urun_indirimi = sum(detay.indirim_tutari for detay in satis_detaylari)
    genel_indirim = satis.indirim_tutari - toplam_urun_indirimi if satis.indirim_tutari > toplam_urun_indirimi else 0
    
    context = {
        'satis': satis,
        'satis_detaylari': satis_detaylari,
        'odemeler': satis.odeme_set.all(),
        'toplam_urun_adedi': satis_detaylari.count(),
        'toplam_urun_indirimi': toplam_urun_indirimi,
        'genel_indirim': genel_indirim,
    }
    return render(request, 'satis/satis_detay.html', context)


@csrf_exempt
@login_required
def satis_tamamla(request):
    """Satış tamamlama view'ı"""
    if request.method == 'POST':
        import json
        from decimal import Decimal
        from datetime import datetime
        
        try:
            # JSON verisini parse et
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                sepet_data = data.get('sepet', [])
                musteri_id = data.get('musteri_id')
                odeme_detaylari = data.get('odeme_detaylari', {})
            else:
                # Form verisini al
                sepet_data = request.session.get('sepet', {})
                musteri_id = request.POST.get('musteri_id')
                odeme_detaylari = {
                    'tip': 'tek',
                    'odeme_yontemi': request.POST.get('odeme_yontemi', 'nakit')
                }
            
            if not sepet_data:
                return JsonResponse({'success': False, 'message': 'Sepet boş!'})
            
            # Müşteri kontrol
            musteri = None
            if musteri_id:
                try:
                    musteri = Musteri.objects.get(pk=musteri_id, aktif=True)
                except Musteri.DoesNotExist:
                    pass
            
            # Satış toplamını hesapla
            ara_toplam = Decimal('0')
            toplam_urun_indirimi = Decimal('0')
            
            for item in sepet_data:
                if isinstance(item, dict):  # JSON format
                    fiyat = Decimal(str(item['fiyat']))
                    miktar = int(item['miktar'])
                    urun_indirimi = Decimal(str(item.get('urun_indirim', item.get('indirim', 0))))
                    toplam_urun_indirimi += urun_indirimi
                    ara_toplam += (fiyat * miktar) - urun_indirimi
                else:  # Session format
                    fiyat = Decimal(str(sepet_data[item]['fiyat']))
                    miktar = int(sepet_data[item]['miktar'])
                    ara_toplam += fiyat * miktar
            
            # Genel indirim
            genel_indirim = Decimal(str(data.get('genel_indirim', 0)))
            toplam_indirim = toplam_urun_indirimi + genel_indirim
            
            # Genel indirim sonrası ara toplam (KDV hesaplaması kaldırıldı)
            indirim_sonrasi_toplam = ara_toplam - genel_indirim
            
            # Fiyatlar zaten KDV dahil olduğu için ayrıca KDV hesaplaması yapılmıyor
            genel_toplam = indirim_sonrasi_toplam
            
            # Açıklama bilgisini al
            aciklama = data.get('aciklama', '').strip() if data else ''
            
            # Satış oluştur
            satis = Satis.objects.create(
                musteri=musteri,
                ara_toplam=ara_toplam,  # İndirim öncesi ara toplam
                indirim_tutari=toplam_indirim,  # Toplam indirim
                kdv_orani=Decimal('0'),  # KDV ayrı hesaplanmıyor
                kdv_tutari=Decimal('0'),  # KDV ayrı hesaplanmıyor
                genel_toplam=genel_toplam,
                toplam_tutar=genel_toplam,
                durum='tamamlandi',
                satici=request.user,
                satis_tarihi=datetime.now(),
                notlar=aciklama,  # Açıklama/not bilgisini kaydet
            )
            
            # Satış detaylarını oluştur ve stokları güncelle
            for item in sepet_data:
                if isinstance(item, dict):  # JSON format
                    urun = Urun.objects.get(pk=item['id'])
                    varyant_id = item.get('varyant_id')
                    miktar = int(item['miktar'])
                    birim_fiyat = Decimal(str(item['fiyat']))
                    indirim_tutari = Decimal(str(item.get('urun_indirim', item.get('indirim', 0))))
                else:  # Session format
                    urun = Urun.objects.get(pk=item)
                    varyant_id = sepet_data[item].get('varyant_id')
                    miktar = int(sepet_data[item]['miktar'])
                    birim_fiyat = Decimal(str(sepet_data[item]['fiyat']))
                    indirim_tutari = Decimal('0')
                
                indirimsiz_toplam = birim_fiyat * miktar
                toplam_fiyat = indirimsiz_toplam - indirim_tutari
                
                # Varyant bazlı stok kontrolü
                if varyant_id:
                    try:
                        varyant = UrunVaryanti.objects.get(pk=varyant_id, aktif=True)
                        if varyant.stok_miktari < miktar:
                            satis.delete()  # Satışı iptal et
                            return JsonResponse({
                                'success': False, 
                                'message': f'{urun.ad} ({varyant.varyasyon_adi}) için yeterli stok yok! Mevcut: {varyant.stok_miktari}'
                            })
                    except UrunVaryanti.DoesNotExist:
                        satis.delete()  # Satışı iptal et
                        return JsonResponse({
                            'success': False, 
                            'message': f'{urun.ad} için geçerli varyant bulunamadı!'
                        })
                else:
                    # Toplam stok kontrolü
                    if urun.toplam_stok < miktar:
                        satis.delete()  # Satışı iptal et
                        return JsonResponse({
                            'success': False, 
                            'message': f'{urun.ad} için yeterli stok yok! Mevcut: {urun.toplam_stok}'
                        })
                
                # Satış detayı oluştur
                SatisDetay.objects.create(
                    satis=satis,
                    urun=urun,
                    miktar=miktar,
                    birim_fiyat=birim_fiyat,
                    indirim_tutari=indirim_tutari,
                    toplam_fiyat=toplam_fiyat
                )
                
                # Varyant stoktan düş
                if varyant_id:
                    varyant.stok_miktari -= miktar
                    varyant.save()
                else:
                    # İlk varyantın stokunu düş
                    first_variant = urun.varyantlar.filter(aktif=True, stok_miktari__gt=0).first()
                    if first_variant:
                        first_variant.stok_miktari -= miktar
                        first_variant.save()
            
            # Ödeme kayıtlarını oluştur
            if odeme_detaylari.get('tip') == 'karma':
                # Karma ödeme detaylarını al
                karma_detay = odeme_detaylari.get('karma_detay', {})
                nakit_tutar = Decimal(str(karma_detay.get('nakit', 0)))
                kart_tutar = Decimal(str(karma_detay.get('kart', 0)))
                havale_tutar = Decimal(str(karma_detay.get('havale', 0)))
                hediye_ceki_tutar = Decimal(str(karma_detay.get('hediye_ceki', 0)))
                
                # Karma ödeme validasyonu
                toplam_odeme = nakit_tutar + kart_tutar + havale_tutar + hediye_ceki_tutar
                if abs(toplam_odeme - genel_toplam) > Decimal('0.01'):
                    satis.delete()
                    return JsonResponse({
                        'success': False, 
                        'message': f'Ödeme tutarları eşleşmiyor! Toplam: {genel_toplam}, Ödenen: {toplam_odeme}'
                    })
                
                # Nakit ödeme kaydı
                if nakit_tutar > 0:
                    Odeme.objects.create(
                        satis=satis,
                        odeme_tipi='nakit',
                        tutar=nakit_tutar,
                    )
                    # Kasa hareketi - nakit kasasına giriş
                    nakit_kasa = Kasa.objects.filter(tip='nakit', aktif=True).first()
                    if nakit_kasa:
                        KasaHareket.objects.create(
                            kasa=nakit_kasa,
                            tip='giris',
                            kaynak='satis',
                            tutar=nakit_tutar,
                            aciklama=f'Satış #{satis.satis_no} - Nakit Ödeme',
                            satis_id=satis.id,
                            kullanici=request.user
                        )
                
                # Kart ödeme kaydı
                if kart_tutar > 0:
                    Odeme.objects.create(
                        satis=satis,
                        odeme_tipi='kart',
                        tutar=kart_tutar,
                    )
                    # Kasa hareketi - POS kasasına giriş
                    pos_kasa = Kasa.objects.filter(tip='pos', aktif=True).first()
                    if pos_kasa:
                        KasaHareket.objects.create(
                            kasa=pos_kasa,
                            tip='giris',
                            kaynak='satis',
                            tutar=kart_tutar,
                            aciklama=f'Satış #{satis.satis_no} - Kart Ödeme',
                            satis_id=satis.id,
                            kullanici=request.user
                        )
                
                # Havale ödeme kaydı
                if havale_tutar > 0:
                    Odeme.objects.create(
                        satis=satis,
                        odeme_tipi='havale',
                        tutar=havale_tutar,
                    )
                    # Kasa hareketi - banka kasasına giriş
                    banka_kasa = Kasa.objects.filter(tip='banka', aktif=True).first()
                    if banka_kasa:
                        KasaHareket.objects.create(
                            kasa=banka_kasa,
                            tip='giris',
                            kaynak='satis',
                            tutar=havale_tutar,
                            aciklama=f'Satış #{satis.satis_no} - Havale Ödeme',
                            satis_id=satis.id,
                            kullanici=request.user
                        )
                
                # Hediye çeki ödemesi
                if hediye_ceki_tutar > 0 and data.get('hediye_ceki'):
                    from hediye.models import HediyeCeki, HediyeCekiKullanim
                    
                    hediye_ceki_data = data.get('hediye_ceki')
                    try:
                        hediye_ceki = HediyeCeki.objects.get(
                            kod=hediye_ceki_data['kod'],
                            durum='aktif'
                        )
                        
                        # Hediye çeki kullanım kaydı oluştur
                        HediyeCekiKullanim.objects.create(
                            hediye_ceki=hediye_ceki,
                            kullanilan_tutar=hediye_ceki_tutar,
                            satis_id=satis.id,
                            kullanan=request.user,
                            aciklama=f'Satış #{satis.satis_no} - Karma Ödeme'
                        )
                        
                        # Hediye çeki bakiyesini güncelle
                        hediye_ceki.kalan_tutar -= hediye_ceki_tutar
                        if hediye_ceki.kalan_tutar <= 0:
                            hediye_ceki.durum = 'kullanilmis'
                        hediye_ceki.save()
                        
                        # Ödeme kaydı oluştur
                        Odeme.objects.create(
                            satis=satis,
                            odeme_tipi='hediye_ceki',
                            tutar=hediye_ceki_tutar,
                            hediye_ceki_kodu=hediye_ceki.kod
                        )
                        
                    except HediyeCeki.DoesNotExist:
                        satis.delete()
                        return JsonResponse({
                            'success': False, 
                            'message': f'Hediye çeki bulunamadı: {hediye_ceki_data["kod"]}'
                        })
                        
            elif odeme_detaylari.get('odeme_yontemi') == 'acik_hesap':
                # Açık hesap - müşteri gerekli
                if not musteri:
                    return JsonResponse({'success': False, 'message': 'Açık hesap satışı için müşteri seçmelisiniz!'})
                
                # Açık hesap bakiyesini güncelle (borç ekle)
                musteri.acik_hesap_bakiye = (musteri.acik_hesap_bakiye or Decimal('0')) + genel_toplam
                musteri.save()
                
                # Ödeme kaydı oluştur
                Odeme.objects.create(
                    satis=satis,
                    odeme_tipi='acik_hesap',
                    tutar=genel_toplam,
                    aciklama=f'Açık hesap borcu - {musteri.ad} {musteri.soyad}'
                )
                    
            else:
                # Tek ödeme
                odeme_yontemi = odeme_detaylari.get('odeme_yontemi', 'nakit')
                taksit_sayisi = odeme_detaylari.get('taksit_sayisi', 1)
                
                # Ödeme tipi dönüşümü
                if odeme_yontemi in ['kart', 'kredi_karti']:
                    odeme_tipi = 'kart'
                elif odeme_yontemi == 'havale':
                    odeme_tipi = 'havale'
                elif odeme_yontemi == 'hediye_ceki':
                    odeme_tipi = 'hediye_ceki'
                elif odeme_yontemi == 'acik_hesap':
                    odeme_tipi = 'acik_hesap'
                    # Veresiye satış - müşteri borcunu artır
                    if satis.musteri:
                        satis.musteri.borc_hareket_ekle(
                            tutar=genel_toplam,
                            aciklama=f'Veresiye Satış - {satis.satis_no}',
                            satis_id=satis.id,
                            user=request.user
                        )
                        # Açık hesap satışları veresiye olarak işaretlenir
                        # Ödeme durumu Odeme modeli üzerinden takip edilir
                else:
                    odeme_tipi = 'nakit'
                
                # Veresiye satış değilse ödeme kaydı oluştur
                if odeme_tipi != 'acik_hesap':
                    Odeme.objects.create(
                        satis=satis,
                        odeme_tipi=odeme_tipi,
                        tutar=genel_toplam,
                        taksit_sayisi=taksit_sayisi if odeme_tipi == 'kart' and taksit_sayisi > 1 else None,
                    )
                    
                    # Kasa hareketi oluştur
                    kasa = None
                    if odeme_tipi == 'nakit':
                        kasa = Kasa.objects.filter(tip='nakit', aktif=True).first()
                        aciklama = f'Satış #{satis.satis_no} - Nakit Ödeme'
                    elif odeme_tipi == 'kart':
                        kasa = Kasa.objects.filter(tip='pos', aktif=True).first()
                        aciklama = f'Satış #{satis.satis_no} - Kart Ödeme'
                    elif odeme_tipi == 'havale':
                        kasa = Kasa.objects.filter(tip='banka', aktif=True).first()
                        aciklama = f'Satış #{satis.satis_no} - Havale Ödeme'
                    
                    if kasa:
                        KasaHareket.objects.create(
                            kasa=kasa,
                            tip='giris',
                            kaynak='satis',
                            tutar=genel_toplam,
                            aciklama=aciklama,
                            satis_id=satis.id,
                            kullanici=request.user
                        )
            
            # Session'ı temizle
            if 'sepet' in request.session:
                del request.session['sepet']
            
            return JsonResponse({
                'success': True,
                'message': 'Satış başarıyla tamamlandı!',
                'satis_id': satis.id,
                'siparis_no': satis.siparis_no,
                'satis_no': satis.satis_no,
                'toplam': str(genel_toplam)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek!'})


@login_required
def satis_iptal(request, pk):
    """Satış iptal view'ı"""
    satis = get_object_or_404(Satis, pk=pk)
    
    if request.method == 'POST':
        satis.durum = 'iptal'
        satis.save()
        messages.success(request, f'Satış #{satis.satis_no} iptal edildi.')
        return redirect('satis:liste')
    
    return render(request, 'satis/satis_iptal.html', {'satis': satis})


@login_required
def iade_ana_sayfa(request):
    """Genel iade ana sayfası - satış seçme ekranı"""
    from datetime import datetime, timedelta
    from django.db.models import Q
    
    # Son 30 günün satışlarını getir
    son_tarih = datetime.now() - timedelta(days=30)
    
    # Arama parametresi
    search = request.GET.get('search', '')
    
    # Temel sorgu - sadece tamamlanmış satışlar
    satislar = Satis.objects.filter(
        durum='tamamlandi',
        satis_tarihi__gte=son_tarih
    ).order_by('-satis_tarihi')
    
    # Arama filtresi
    if search:
        satislar = satislar.filter(
            Q(satis_no__icontains=search) |
            Q(musteri__ad__icontains=search) |
            Q(musteri__soyad__icontains=search) |
            Q(musteri__telefon__icontains=search)
        )
    
    # Sayfalama
    from django.core.paginator import Paginator
    paginator = Paginator(satislar, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search,
    }
    
    return render(request, 'satis/iade_ana_sayfa.html', context)


@login_required
def satis_iade(request, pk):
    """Satış iade view'ı - Basit ve stabil versiyon"""
    from hediye.models import HediyeCeki
    from django.utils import timezone
    from datetime import timedelta
    import string
    import random
    from decimal import Decimal
    
    satis = get_object_or_404(Satis, pk=pk)
    
    # Sadece tamamlanmış satışlar iade edilebilir
    if satis.durum != 'tamamlandi':
        messages.error(request, 'Sadece tamamlanmış satışlar iade edilebilir!')
        return redirect('satis:liste')
    
    # Satış kalemlerini al
    kalemler = satis.satisdetay_set.all()
    
    if request.method == 'POST':
        try:
            print("� İade işlemi başlatıldı")
            
            # Form verilerini basit şekilde al
            iade_edilecek_urunler = []
            toplam_iade_tutari = Decimal('0')
            
            # Her kalem için kontrol et
            for kalem in kalemler:
                iade_miktar_str = request.POST.get(f'iade_miktar_{kalem.id}', '0')
                
                try:
                    iade_miktar = int(iade_miktar_str) if iade_miktar_str else 0
                except ValueError:
                    iade_miktar = 0
                
                if iade_miktar > 0:
                    # Miktar kontrolü
                    if iade_miktar > kalem.miktar:
                        messages.error(request, f'{kalem.urun.ad} için iade miktarı stok miktarından fazla olamaz!')
                        return render(request, 'satis/satis_iade_yeni.html', {
                            'satis': satis, 
                            'kalemler': kalemler
                        })
                    
                    # İade hesapla
                    iade_tutar = Decimal(str(kalem.birim_fiyat)) * Decimal(str(iade_miktar))
                    toplam_iade_tutari += iade_tutar
                    
                    iade_edilecek_urunler.append({
                        'kalem': kalem,
                        'miktar': iade_miktar,
                        'tutar': iade_tutar
                    })
            
            # Hiç ürün seçilmediyse hata ver
            if not iade_edilecek_urunler:
                messages.error(request, 'İade edilecek en az bir ürün seçmelisiniz!')
                return render(request, 'satis/satis_iade_yeni.html', {
                    'satis': satis, 
                    'kalemler': kalemler
                })
            
            print(f"✅ {len(iade_edilecek_urunler)} ürün iade edilecek, toplam: {toplam_iade_tutari} ₺")
            
            # Hediye çeki oluştur
            hediye_kodu = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            hediye_ceki = HediyeCeki.objects.create(
                kod=hediye_kodu,
                tutar=toplam_iade_tutari,
                kalan_tutar=toplam_iade_tutari,
                gecerlilik_tarihi=timezone.now().date() + timedelta(days=365),
                olusturan=request.user,
                musteri=satis.musteri,
                durum='aktif',
                aktif=True,
                aciklama=f'İade - Satış #{satis.satis_no} ({satis.siparis_tarihi.strftime("%d.%m.%Y")})'
            )
            
            print(f"✅ Hediye çeki oluşturuldu: {hediye_ceki.kod}")
            
            # Stok güncellemeleri ve satış kalem düzenlemeleri
            for item in iade_edilecek_urunler:
                # Varyant bazlı stok güncelle
                # SatisDetay'da hangi varyantın satıldığını bulmalıyız
                # Bu bilgi direkt SatisDetay'da yok, bu yüzden ilk varyanta ekleyelim
                urun = item['kalem'].urun
                first_variant = urun.varyantlar.filter(aktif=True).first()
                if first_variant:
                    first_variant.stok_miktari += item['miktar']
                    first_variant.save()
                
                # Kalem güncelle
                if item['miktar'] == item['kalem'].miktar:
                    # Tamamen iade edildi, kalemi sil
                    item['kalem'].delete()
                else:
                    # Kısmi iade, miktarı azalt
                    item['kalem'].miktar -= item['miktar']
                    item['kalem'].toplam_fiyat = item['kalem'].birim_fiyat * item['kalem'].miktar
                    item['kalem'].save()
            
            # Satış tutarını güncelle
            satis.toplam_tutar -= toplam_iade_tutari
            satis.save()
            
            # Eğer hiç kalem kalmadıysa satışı iade olarak işaretle
            if not satis.satisdetay_set.exists():
                satis.durum = 'iade'
                satis.save()
            
            messages.success(request, f'İade başarılı! Hediye çeki: {hediye_ceki.kod} ({toplam_iade_tutari} ₺)')
            return redirect('satis:iade_fisi', hediye_ceki_id=hediye_ceki.pk)
            
        except Exception as e:
            print(f"❌ İade hatası: {str(e)}")
            messages.error(request, f'İade işlemi başarısız: {str(e)}')
            return render(request, 'satis/satis_iade_yeni.html', {
                'satis': satis, 
                'kalemler': kalemler
            })
    
    # GET request - formu göster
    return render(request, 'satis/satis_iade_yeni.html', {
        'satis': satis, 
        'kalemler': kalemler
    })


@login_required
def iade_fisi(request, hediye_ceki_id):
    """İade fişi görüntüleme"""
    from hediye.models import HediyeCeki
    
    hediye_ceki = get_object_or_404(HediyeCeki, pk=hediye_ceki_id)
    
    # Sadece oluşturan kullanıcı veya admin görebilir
    if request.user != hediye_ceki.olusturan and not request.user.is_staff:
        messages.error(request, 'Bu fişi görüntüleme yetkiniz yok!')
        return redirect('satis:liste')
    
    context = {
        'hediye_ceki': hediye_ceki,
        'print_mode': request.GET.get('print', False)
    }
    
    return render(request, 'satis/iade_fisi.html', context)


@login_required
def iade_fisi_pdf(request, hediye_ceki_id):
    """İade fişi PDF çıktısı"""
    from hediye.models import HediyeCeki
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, A5
    from reportlab.lib.colors import black, blue, green
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.units import inch, mm
    from reportlab.lib import colors
    import io
    import os
    from django.conf import settings
    
    hediye_ceki = get_object_or_404(HediyeCeki, pk=hediye_ceki_id)
    
    # Sadece oluşturan kullanıcı veya admin indirebilir
    if request.user != hediye_ceki.olusturan and not request.user.is_staff:
        messages.error(request, 'Bu fişi indirme yetkiniz yok!')
        return redirect('satis:liste')
    
    # Font sistemi (daha önce kullandığımız sistem)
    def detect_font():
        """Windows TTF fontlarını algıla"""
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        
        fonts_to_try = [
            (r"C:\Windows\Fonts\arialuni.ttf", "Arial Unicode MS"),
            (r"C:\Windows\Fonts\calibri.ttf", "Calibri"),
            (r"C:\Windows\Fonts\times.ttf", "Times New Roman")
        ]
        
        for font_path, font_name in fonts_to_try:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    return font_name
                except:
                    continue
        
        # Fallback font
        return "Helvetica"
    
    font_name = detect_font()
    
    # PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="iade_fisi_{hediye_ceki.kod}.pdf"'
    
    # PDF oluştur
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    # Stiller
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=1,  # Center
        textColor=colors.darkblue,
        fontName=font_name
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=15,
        textColor=colors.darkgreen,
        fontName=font_name
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name,
        leftIndent=10
    )
    
    # İçerik
    story = []
    
    # Başlık
    story.append(Paragraph("İADE FİŞİ", title_style))
    story.append(Spacer(1, 20))
    
    # Hediye çeki bilgileri
    story.append(Paragraph("HEDİYE ÇEKİ BİLGİLERİ", heading_style))
    
    hediye_data = [
        ['Hediye Çeki Kodu:', hediye_ceki.kod],
        ['Tutar:', f"{hediye_ceki.tutar:.2f} ₺"],
        ['Geçerlilik Tarihi:', hediye_ceki.gecerlilik_tarihi.strftime('%d.%m.%Y')],
        ['Oluşturma Tarihi:', hediye_ceki.olusturma_tarihi.strftime('%d.%m.%Y %H:%M')],
    ]
    
    if hediye_ceki.musteri:
        hediye_data.append(['Müşteri:', f"{hediye_ceki.musteri.ad} {hediye_ceki.musteri.soyad}"])
    
    hediye_table = Table(hediye_data, colWidths=[1.5*inch, 2*inch])
    hediye_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(hediye_table)
    story.append(Spacer(1, 20))
    
    # İade açıklaması
    if hediye_ceki.aciklama:
        story.append(Paragraph("İADE SEBEBİ", heading_style))
        story.append(Paragraph(hediye_ceki.aciklama, normal_style))
        story.append(Spacer(1, 20))
    
    # Kullanım bilgileri
    story.append(Paragraph("KULLANIM BİLGİLERİ", heading_style))
    story.append(Paragraph("• Bu hediye çeki tek seferlik kullanılabilir.", normal_style))
    story.append(Paragraph("• Mağazamızda geçerlidir.", normal_style))
    story.append(Paragraph("• Para üstü verilmez.", normal_style))
    story.append(Paragraph(f"• Geçerlilik tarihi: {hediye_ceki.gecerlilik_tarihi.strftime('%d.%m.%Y')}", normal_style))
    
    # PDF'i oluştur
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


@login_required
def satis_yazdir(request, pk):
    """Satış yazdırma view'ı"""
    satis = get_object_or_404(Satis, pk=pk)
    
    # Sadece tamamlanmış satışları yazdırabilir
    if satis.durum != 'tamamlandi':
        messages.error(request, 'Sadece tamamlanmış satışlar yazdırılabilir.')
        return redirect('satis:detay', pk=pk)
    
    # Satış detayları
    satis_detaylari = satis.satisdetay_set.all().select_related('urun')
    
    # İndirim hesaplamaları
    toplam_urun_indirimi = sum(detay.indirim_tutari for detay in satis_detaylari)
    genel_indirim = satis.indirim_tutari - toplam_urun_indirimi if satis.indirim_tutari > toplam_urun_indirimi else 0
    
    context = {
        'satis': satis,
        'satis_detaylari': satis_detaylari,
        'odemeler': satis.odeme_set.all(),
        'toplam_urun_indirimi': toplam_urun_indirimi,
        'genel_indirim': genel_indirim,
    }
    return render(request, 'satis/satis_yazdir.html', context)


# @login_required  # TEST İÇİN GEÇİCİ OLARAK KALDIRILDI
def barkod_sorgula(request):
    """Barkod sorgulama AJAX view'ı"""
    from urun.models import UrunVaryanti
    
    barkod = request.GET.get('barkod')
    
    if barkod:
        try:
            # Barkod UrunVaryanti modelinde bulunuyor
            varyant = UrunVaryanti.objects.get(barkod=barkod, aktif=True)
            urun = varyant.urun
            
            if varyant.stok_miktari > 0 and urun.aktif:
                data = {
                    'success': True,
                    'urun': {
                        'id': urun.id,
                        'varyant_id': varyant.id,
                        'ad': urun.ad,
                        'varyasyon': varyant.varyasyon_adi,
                        'beden': varyant.beden.ad if varyant.beden else 'Tek Beden',
                        'renk': varyant.renk.ad if varyant.renk else 'Standart',
                        'barkod': varyant.barkod,
                        'satis_fiyati': str(urun.satis_fiyati),
                        'stok_miktari': varyant.stok_miktari,
                        'kategori': str(urun.kategori)
                    }
                }
            else:
                data = {'success': False, 'message': 'Ürün stokta yok!'}
        except UrunVaryanti.DoesNotExist:
            data = {'success': False, 'message': 'Barkod bulunamadı!'}
    else:
        data = {'success': False, 'message': 'Barkod girilmedi!'}
    
    return JsonResponse(data)


# AJAX Views
# @login_required  # TEST İÇİN GEÇİCİ OLARAK KALDIRILDI
def urun_ara(request):
    """Ürün arama AJAX view'ı"""
    from urun.models import UrunVaryanti
    
    query = request.GET.get('q', '')
    
    if len(query) >= 2:
        # Hem ürün adı hem de barkod ile arama yap
        varyantlar = UrunVaryanti.objects.filter(
            Q(urun__ad__icontains=query) | Q(barkod__icontains=query) | Q(urun__urun_kodu__icontains=query),
            aktif=True,
            urun__aktif=True,
            stok_miktari__gt=0
        )[:10]
        
        data = []
        for varyant in varyantlar:
            data.append({
                'id': varyant.urun.id,
                'varyant_id': varyant.id,
                'ad': varyant.urun.ad,
                'varyasyon': varyant.varyasyon_adi,
                'beden': varyant.beden.ad if varyant.beden else 'Tek Beden',
                'renk': varyant.renk.ad if varyant.renk else 'Standart',
                'barkod': varyant.barkod,
                'urun_kodu': varyant.urun.urun_kodu,
                'satis_fiyati': str(varyant.urun.satis_fiyati),
                'stok_miktari': varyant.stok_miktari,
                'kategori': str(varyant.urun.kategori) if varyant.urun.kategori else 'Kategori Yok'
            })
        
        return JsonResponse({'success': True, 'urunler': data})
    
    return JsonResponse({'success': False, 'urunler': []})


@login_required
def sepete_ekle(request):
    """Sepete ekleme AJAX view'ı"""
    from urun.models import UrunVaryanti
    
    if request.method == 'POST':
        varyant_id = request.POST.get('varyant_id')
        urun_id = request.POST.get('urun_id')  # Eski sistemle uyumluluk için
        miktar = int(request.POST.get('miktar', 1))
        
        try:
            # Önce varyant_id ile dene, yoksa urun_id ile ilk varyantı al
            if varyant_id:
                varyant = UrunVaryanti.objects.get(pk=varyant_id, aktif=True, urun__aktif=True)
            elif urun_id:
                varyant = UrunVaryanti.objects.filter(urun_id=urun_id, aktif=True, urun__aktif=True).first()
                if not varyant:
                    return JsonResponse({'success': False, 'message': 'Ürün varyantı bulunamadı!'})
            else:
                return JsonResponse({'success': False, 'message': 'Ürün ID eksik!'})
            
            if varyant.stok_miktari < miktar:
                return JsonResponse({'success': False, 'message': 'Yeterli stok yok!'})
            
            # Session'dan sepeti al
            sepet = request.session.get('sepet', {})
            
            sepet_key = f"v_{varyant.id}"  # Varyant bazlı key
            
            if sepet_key in sepet:
                sepet[sepet_key]['miktar'] += miktar
            else:
                sepet[sepet_key] = {
                    'varyant_id': varyant.id,
                    'urun_id': varyant.urun.id,
                    'ad': varyant.urun.ad,
                    'varyasyon': varyant.varyasyon_adi,
                    'barkod': varyant.barkod,
                    'fiyat': str(varyant.urun.satis_fiyati),
                    'miktar': miktar,
                }
            
            # Toplam hesapla
            sepet[sepet_key]['toplam'] = str(
                float(sepet[sepet_key]['fiyat']) * sepet[sepet_key]['miktar']
            )
            
            # Session'a kaydet
            request.session['sepet'] = sepet
            
            return JsonResponse({'success': True, 'message': 'Ürün sepete eklendi'})
            
        except UrunVaryanti.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Ürün varyantı bulunamadı!'})
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek!'})


@login_required
def sepetten_cikar(request):
    """Sepetten çıkarma AJAX view'ı"""
    if request.method == 'POST':
        urun_id = request.POST.get('urun_id')
        
        sepet = request.session.get('sepet', {})
        
        if str(urun_id) in sepet:
            del sepet[str(urun_id)]
            request.session['sepet'] = sepet
            return JsonResponse({'success': True, 'message': 'Ürün sepetten çıkarıldı'})
        
        return JsonResponse({'success': False, 'message': 'Ürün sepette bulunamadı!'})
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek!'})


@login_required
def sepet_temizle(request):
    """Sepet temizleme AJAX view'ı"""
    if request.method == 'POST':
        request.session['sepet'] = {}
        return JsonResponse({'success': True, 'message': 'Sepet temizlendi'})
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek!'})


# @login_required  # TEST İÇİN GEÇİCİ OLARAK KALDIRILDI
def musteri_ara(request):
    """Müşteri arama AJAX view'ı"""
    query = request.GET.get('q', '')
    
    if len(query) >= 2:
        musteriler = Musteri.objects.filter(
            Q(ad__icontains=query) | 
            Q(soyad__icontains=query) | 
            Q(telefon__icontains=query) |
            Q(firma_adi__icontains=query),
            aktif=True
        )[:10]
        
        data = []
        for musteri in musteriler:
            data.append({
                'id': musteri.id,
                'ad': musteri.ad,
                'soyad': musteri.soyad,
                'telefon': musteri.telefon or 'Telefon yok',
                'tip': musteri.tip,
                'firma_adi': musteri.firma_adi or '',
                'acik_hesap_bakiye': float(musteri.acik_hesap_bakiye or 0),
                'acik_hesap_limit': float(musteri.acik_hesap_limit or 0),
                'tam_ad': musteri.firma_adi if musteri.tip == 'kurumsal' and musteri.firma_adi else f"{musteri.ad} {musteri.soyad}"
            })
        
        return JsonResponse({'success': True, 'musteriler': data})
    
    return JsonResponse({'success': False, 'musteriler': []})


@login_required
def hediye_ceki_sorgula(request):
    """Hediye çeki sorgulama AJAX view'ı"""
    from hediye.models import HediyeCeki
    from django.utils import timezone
    
    kod = request.GET.get('kod', '').strip()
    
    if not kod:
        return JsonResponse({'success': False, 'message': 'Hediye çeki kodu gerekli!'})
    
    try:
        hediye_ceki = HediyeCeki.objects.get(kod=kod, aktif=True)
        
        # Hediye çeki kullanılabilir mi kontrol et
        if not hediye_ceki.kullanilabilir_mi:
            reasons = []
            if hediye_ceki.durum != 'aktif':
                reasons.append(f"Durum: {hediye_ceki.get_durum_display()}")
            if hediye_ceki.kalan_tutar <= 0:
                reasons.append("Bakiye kalmamış")
            if hediye_ceki.gecerlilik_tarihi < timezone.now().date():
                reasons.append("Süresi dolmuş")
            
            return JsonResponse({
                'success': False, 
                'message': f"Hediye çeki kullanılamaz: {', '.join(reasons)}"
            })
        
        # Hediye çeki bilgilerini döndür
        data = {
            'kod': hediye_ceki.kod,
            'tutar': float(hediye_ceki.tutar),
            'kalan_tutar': float(hediye_ceki.kalan_tutar),
            'gecerlilik_tarihi': hediye_ceki.gecerlilik_tarihi.strftime('%d.%m.%Y'),
            'durum': hediye_ceki.get_durum_display()
        }
        
        return JsonResponse({'success': True, 'hediye_ceki': data})
        
    except HediyeCeki.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Hediye çeki bulunamadı!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'})


@login_required
def yeni_siparis_no(request):
    """Yeni sipariş numarası preview getir"""
    siparis_no_preview = SiparisNumarasi.sonraki_numara_preview()
    
    return JsonResponse({
        'success': True,
        'siparis_no': siparis_no_preview
    })


@login_required
def tahsilat_listesi(request):
    """Tahsilat listesi view'ı"""
    from django.db.models import Sum, Count, Q
    from datetime import datetime, date, timedelta
    
    # Tüm ödemeleri getir
    odemeler = Odeme.objects.select_related('satis', 'satis__musteri', 'satis__satici').order_by('-odeme_tarihi')
    
    # Arama
    query = request.GET.get('q')
    if query:
        odemeler = odemeler.filter(
            Q(satis__siparis_no__icontains=query) |
            Q(satis__satis_no__icontains=query) |
            Q(satis__musteri__ad__icontains=query) |
            Q(satis__musteri__soyad__icontains=query) |
            Q(hediye_ceki_kodu__icontains=query)
        )
    
    # Tarih filtreleri
    tarih_baslangic = request.GET.get('tarih_baslangic')
    tarih_bitis = request.GET.get('tarih_bitis')
    
    if tarih_baslangic:
        try:
            baslangic = datetime.strptime(tarih_baslangic, '%Y-%m-%d').date()
            odemeler = odemeler.filter(odeme_tarihi__date__gte=baslangic)
        except ValueError:
            pass
    
    if tarih_bitis:
        try:
            bitis = datetime.strptime(tarih_bitis, '%Y-%m-%d').date()
            odemeler = odemeler.filter(odeme_tarihi__date__lte=bitis)
        except ValueError:
            pass
    
    # Ödeme tipi filtresi
    odeme_tipi = request.GET.get('odeme_tipi')
    if odeme_tipi:
        odemeler = odemeler.filter(odeme_tipi=odeme_tipi)
    
    # Görünüm modu (card/table)
    view_mode = request.GET.get('view', 'table')  # varsayılan table görünümü
    
    # İstatistikler hesaplama
    istatistikler = odemeler.aggregate(
        toplam_tutar=Sum('tutar'),
        odeme_sayisi=Count('id')
    )
    
    # Bugünkü tahsilatlar
    bugun = date.today()
    bugun_odemeler = odemeler.filter(odeme_tarihi__date=bugun)
    bugun_toplam = bugun_odemeler.aggregate(toplam=Sum('tutar'))['toplam'] or 0
    bugun_sayisi = bugun_odemeler.count()
    
    # Sayfalama
    from django.core.paginator import Paginator
    items_per_page = 12 if view_mode == 'card' else 25
    paginator = Paginator(odemeler, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Sayfa toplamını hesapla
    sayfa_toplam_tutar = sum([odeme.tutar for odeme in page_obj])
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'view_mode': view_mode,
        'toplam_tutar': istatistikler['toplam_tutar'] or 0,
        'odeme_sayisi': istatistikler['odeme_sayisi'] or 0,
        'sayfa_toplam_tutar': sayfa_toplam_tutar,
        'bugun_toplam': bugun_toplam,
        'bugun_sayisi': bugun_sayisi,
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
        'odeme_tipi': odeme_tipi,
        'odeme_tipleri': Odeme.ODEME_TIPLERI,
        'title': 'Tahsilat Listesi',
    }
    
    return render(request, 'satis/tahsilat_listesi.html', context)


@login_required
def tahsilat_rapor(request):
    """Tahsilat raporları view'ı"""
    from django.db.models import Sum, Count, Q
    from datetime import date, timedelta
    
    bugün = date.today()
    bu_ay_başı = bugün.replace(day=1)
    
    # Temel istatistikler
    bugün_tahsilat = Odeme.objects.filter(
        odeme_tarihi__date=bugün
    ).aggregate(toplam=Sum('tutar'))['toplam'] or 0
    
    bu_ay_tahsilat = Odeme.objects.filter(
        odeme_tarihi__date__gte=bu_ay_başı
    ).aggregate(toplam=Sum('tutar'))['toplam'] or 0
    
    # Ödeme tipi bazında istatistikler
    odeme_tipi_istatistikleri = []
    for kod, ad in Odeme.ODEME_TIPLERI:
        bu_ay_toplam = Odeme.objects.filter(
            odeme_tipi=kod,
            odeme_tarihi__date__gte=bu_ay_başı
        ).aggregate(toplam=Sum('tutar'))['toplam'] or 0
        
        odeme_adedi = Odeme.objects.filter(
            odeme_tipi=kod,
            odeme_tarihi__date__gte=bu_ay_başı
        ).count()
        
        if bu_ay_toplam > 0 or odeme_adedi > 0:
            odeme_tipi_istatistikleri.append({
                'kod': kod,
                'ad': ad,
                'bu_ay_toplam': bu_ay_toplam,
                'odeme_adedi': odeme_adedi,
                'renk': {
                    'nakit': '#28a745',
                    'kart': '#007bff', 
                    'hediye_ceki': '#ffc107',
                    'acik_hesap': '#dc3545'
                }.get(kod, '#6c757d'),
                'ikon': {
                    'nakit': 'fas fa-money-bill-wave',
                    'kart': 'fas fa-credit-card',
                    'hediye_ceki': 'fas fa-gift',
                    'acik_hesap': 'fas fa-handshake'
                }.get(kod, 'fas fa-coins')
            })
    
    # Günlük trend (son 30 gün)
    otuz_gün_önce = bugün - timedelta(days=30)
    günlük_trend = Odeme.objects.filter(
        odeme_tarihi__date__gte=otuz_gün_önce
    ).extra(
        select={'tarih': 'DATE(odeme_tarihi)'}
    ).values('tarih').annotate(
        toplam=Sum('tutar'),
        adet=Count('id')
    ).order_by('tarih')
    
    # En büyük tahsilatlar (bu ay)
    en_buyuk_tahsilatlar = Odeme.objects.filter(
        odeme_tarihi__date__gte=bu_ay_başı
    ).select_related('satis', 'satis__musteri').order_by('-tutar')[:10]
    
    # Satıcı bazında tahsilat
    satici_tahsilat = Odeme.objects.filter(
        odeme_tarihi__date__gte=bu_ay_başı
    ).values(
        'satis__satici__first_name',
        'satis__satici__last_name',
        'satis__satici__username'
    ).annotate(
        toplam_tahsilat=Sum('tutar'),
        tahsilat_adedi=Count('id')
    ).order_by('-toplam_tahsilat')[:10]
    
    context = {
        'title': 'Tahsilat Raporları',
        'bugün_tahsilat': bugün_tahsilat,
        'bu_ay_tahsilat': bu_ay_tahsilat,
        'odeme_tipi_istatistikleri': odeme_tipi_istatistikleri,
        'günlük_trend': günlük_trend,
        'en_buyuk_tahsilatlar': en_buyuk_tahsilatlar,
        'satici_tahsilat': satici_tahsilat,
        'bugün': bugün,
        'bu_ay_başı': bu_ay_başı,
    }
    
    return render(request, 'satis/tahsilat_rapor.html', context)
