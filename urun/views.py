from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, F, Count
from decimal import Decimal, InvalidOperation
from .models import Urun, UrunKategoriUst, Varyasyon, Marka
from log.models import AktiviteLog


@login_required
def urun_listesi(request):
    """Ürün listesi view'ı"""
    try:
        # ORM kullanarak ürünleri al
        from django.db.models import Case, When, Value, CharField
        
        # Arama parametreleri
        query = request.GET.get('q', '')
        kategori_filter = request.GET.get('kategori', '')
        marka_filter = request.GET.get('marka', '')
        durum_filter = request.GET.get('durum', '')
        
        # Base queryset
        urunler = Urun.objects.select_related('kategori', 'marka').filter(aktif=True)
        
        # Arama filtresi
        if query:
            urunler = urunler.filter(
                Q(ad__icontains=query) | 
                Q(barkod__icontains=query) | 
                Q(kategori__ad__icontains=query)
            )
        
        # Kategori filtresi
        if kategori_filter:
            urunler = urunler.filter(kategori_id=kategori_filter)
        
        # Marka filtresi
        if marka_filter:
            urunler = urunler.filter(marka_id=marka_filter)
        
        # Stok durumu filtresi
        if durum_filter == 'stokta':
            urunler = urunler.filter(stok_miktari__gt=0)
        elif durum_filter == 'kritik':
            urunler = urunler.filter(stok_miktari__gt=0, stok_miktari__lte=F('minimum_stok'))
        elif durum_filter == 'tukendi':
            urunler = urunler.filter(stok_miktari=0)
        
        # Ek bilgiler için annotate (stok durumu vs)
        urunler = urunler.annotate(
            kategori_ad=F('kategori__ad'),
            marka_ad=F('marka__ad')
        ).order_by('-olusturma_tarihi')
        
        # Kategoriler listesi
        kategoriler = UrunKategoriUst.objects.all().order_by('ad')
        
        # Marka listesi  
        markalar = Marka.objects.filter(aktif=True).order_by('ad')
        
        # İstatistikler
        toplam_urun = Urun.objects.filter(aktif=True).count()
        aktif_urun = Urun.objects.filter(aktif=True, stok_miktari__gt=0).count()
        kritik_stok = Urun.objects.filter(aktif=True, stok_miktari__gt=0, stok_miktari__lte=F('minimum_stok')).count()
        
        context = {
            'urunler': urunler,
            'kategoriler': kategoriler,
            'markalar': markalar,
            'query': query,
            'kategori_filter': kategori_filter,
            'marka_filter': marka_filter,
            'durum_filter': durum_filter,
            'toplam_urun': toplam_urun,
            'aktif_urun': aktif_urun,
            'kritik_stok': kritik_stok,
            'tukenen_stok': toplam_urun - aktif_urun,
        }
        
        return render(request, 'urun/liste.html', context)
        
    except Exception as e:
        # Hata durumunda mesaj göster
        messages.error(request, f'Ürün listesi yüklenirken hata oluştu: {str(e)}')
        context = {
            'urunler': [],
            'kategoriler': [],
            'query': '',
            'kategori_filter': '',
            'durum_filter': '',
            'toplam_urun': 0,
            'aktif_urun': 0,
            'kritik_stok': 0,
            'tukenen_stok': 0,
            'error_message': f'Veritabanı hatası: {str(e)}'
        }
        return render(request, 'urun/liste.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def urun_ekle(request):
    """Ürün ekleme view'ı"""
    if request.method == 'POST':
        try:
            # Form verilerini al ve validate et
            ad = request.POST.get('ad', '').strip()
            kategori_id = request.POST.get('kategori')
            marka_id = request.POST.get('marka')  # Marka alanını ekle
            barkod = request.POST.get('barkod', '').strip()
            sku = request.POST.get('sku', '').strip()
            aciklama = ''  # Açıklama alanı kaldırıldı
            alis_fiyati = request.POST.get('alis_fiyati', '').strip()
            satis_fiyati = request.POST.get('satis_fiyati', '').strip()
            stok_miktari = request.POST.get('stok_miktari', '0').strip()
            if not stok_miktari:
                stok_miktari = '0'  # Boşsa 0 yap
            kritik_stok = request.POST.get('kritik_stok', '').strip()
            birim = request.POST.get('birim', '').strip()
            resim = request.FILES.get('resim')
            aktif = request.POST.get('aktif') == 'on'
            stok_takibi = request.POST.get('stok_takibi') == 'on'
            cinsiyet = request.POST.get('cinsiyet', 'kadin').strip()
            
            # Zorunlu alanları kontrol et
            if not ad:
                messages.error(request, 'Ürün adı zorunludur.')
                raise ValueError('Ürün adı boş')
                
            if not kategori_id:
                messages.error(request, 'Kategori seçimi zorunludur.')
                raise ValueError('Kategori seçilmemiş')
                
            if not satis_fiyati:
                messages.error(request, 'Satış fiyatı zorunludur.')
                raise ValueError('Satış fiyatı boş')
                
            if not birim:
                messages.error(request, 'Birim seçimi zorunludur.')
                raise ValueError('Birim seçilmemiş')
            
            # Kategori kontrolü
            try:
                kategori = UrunKategoriUst.objects.get(id=kategori_id)
            except UrunKategoriUst.DoesNotExist:
                messages.error(request, 'Geçersiz kategori seçimi.')
                raise ValueError('Geçersiz kategori')
            
            # Marka kontrolü (opsiyonel)
            marka = None
            if marka_id:
                try:
                    marka = Marka.objects.get(id=marka_id, aktif=True)
                except Marka.DoesNotExist:
                    messages.error(request, 'Geçersiz marka seçimi.')
                    raise ValueError('Geçersiz marka')
            
            # Barkod benzersizlik kontrolü
            if barkod and Urun.objects.filter(barkod=barkod).exists():
                messages.error(request, 'Bu barkod zaten kullanılıyor.')
                raise ValueError('Barkod mevcut')
            
            # Fiyat kontrolü
            try:
                satis_fiyati_decimal = Decimal(satis_fiyati)
                if satis_fiyati_decimal <= 0:
                    messages.error(request, 'Satış fiyatı 0\'dan büyük olmalıdır.')
                    raise ValueError('Geçersiz satış fiyatı')
            except (ValueError, InvalidOperation):
                messages.error(request, 'Geçersiz satış fiyatı formatı.')
                raise ValueError('Geçersiz fiyat formatı')
            
            alis_fiyati_decimal = None
            if alis_fiyati:
                try:
                    alis_fiyati_decimal = Decimal(alis_fiyati)
                    if alis_fiyati_decimal < 0:
                        messages.error(request, 'Alış fiyatı negatif olamaz.')
                        raise ValueError('Negatif alış fiyatı')
                except (ValueError, InvalidOperation):
                    messages.error(request, 'Geçersiz alış fiyatı formatı.')
                    raise ValueError('Geçersiz alış fiyatı formatı')
            
            # Stok kontrolü
            try:
                stok_miktari_int = int(stok_miktari)
                if stok_miktari_int < 0:
                    messages.error(request, 'Stok miktarı negatif olamaz.')
                    raise ValueError('Negatif stok')
            except ValueError:
                messages.error(request, 'Geçersiz stok miktarı formatı.')
                raise ValueError('Geçersiz stok formatı')
            
            kritik_stok_int = 0
            if kritik_stok:
                try:
                    kritik_stok_int = int(kritik_stok)
                    if kritik_stok_int < 0:
                        messages.error(request, 'Kritik stok seviyesi negatif olamaz.')
                        raise ValueError('Negatif kritik stok')
                except ValueError:
                    messages.error(request, 'Geçersiz kritik stok formatı.')
                    raise ValueError('Geçersiz kritik stok formatı')
            
            # Kar marjını hesapla
            kar_marji = 0
            if alis_fiyati_decimal and satis_fiyati_decimal and alis_fiyati_decimal > 0:
                kar_marji = float(((satis_fiyati_decimal - alis_fiyati_decimal) / alis_fiyati_decimal) * 100)
            
            # Ürün oluştur
            urun = Urun.objects.create(
                ad=ad,
                barkod=barkod if barkod else None,
                sku=sku if sku else f'SKU{Urun.objects.count() + 1:05d}',
                kategori=kategori,
                marka=marka,  # Marka alanını ekle
                alis_fiyati=alis_fiyati_decimal or Decimal('0'),
                kar_marji=kar_marji,
                satis_fiyati=satis_fiyati_decimal,  # Eksik olan field!
                stok_miktari=stok_miktari_int,
                minimum_stok=kritik_stok_int,  # Bu da eksikti
                aciklama=aciklama,
                cinsiyet=cinsiyet,
                olusturan=request.user
            )
            
            # Aktivite logu
            AktiviteLog.objects.create(
                kullanici=request.user,
                aktivite_tipi='ekleme',
                baslik='Ürün Eklendi',
                aciklama=f'{urun.ad} ürünü eklendi (Stok: {stok_miktari_int} {birim})',
                content_object=urun
            )
            
            messages.success(request, f'✅ {urun.ad} ürünü başarıyla eklendi!')
            return redirect('urun:liste')
            
        except ValueError:
            # Hata mesajları zaten set edildi
            pass
        except Exception as e:
            messages.error(request, f'❌ Ürün eklenirken beklenmeyen hata oluştu: {str(e)}')
    
    # Kategorileri getir
    ust_kategoriler = UrunKategoriUst.objects.all().order_by('ad')
    varyasyonlar = Varyasyon.objects.all()
    markalar = Marka.objects.filter(aktif=True).order_by('ad')
    
    # Eğer kategori yoksa uyarı ver
    if not ust_kategoriler.exists():
        messages.warning(request, '⚠️ Önce en az bir kategori oluşturmanız gerekiyor.')
    
    # URL'den barkod parametresini al
    barkod_param = request.GET.get('barkod', '')
    
    context = {
        'ust_kategoriler': ust_kategoriler,
        'varyasyonlar': varyasyonlar,
        'markalar': markalar,  # Markaları context'e ekle
        'title': 'Ürün Ekle',
        'form_data': request.POST if request.method == 'POST' else {},
        'barkod_param': barkod_param,  # Barkod parametresini ekle
    }
    return render(request, 'urun/ekle.html', context)


@login_required
def urun_duzenle(request, pk):
    """Ürün düzenleme view'ı"""
    urun = get_object_or_404(Urun, pk=pk)
    
    if request.method == 'POST':
        urun.ad = request.POST.get('ad', urun.ad)
        urun.sku = request.POST.get('sku', urun.sku)
        urun.aciklama = request.POST.get('aciklama', urun.aciklama)
        urun.alis_fiyati = request.POST.get('alis_fiyati', urun.alis_fiyati)
        urun.kar_marji = request.POST.get('kar_marji', urun.kar_marji)
        urun.stok_miktari = request.POST.get('stok_miktari', urun.stok_miktari)
        urun.cinsiyet = request.POST.get('cinsiyet', urun.cinsiyet)
        
        kategori_id = request.POST.get('kategori')
        if kategori_id:
            urun.kategori = get_object_or_404(UrunKategoriUst, pk=kategori_id)
        
        urun.save()
        messages.success(request, f'{urun.ad} başarıyla güncellendi.')
        return redirect('urun_detay', pk=urun.pk)
    
    ust_kategoriler = UrunKategoriUst.objects.all().order_by('ad')
    varyasyonlar = Varyasyon.objects.all()
    
    context = {
        'urun': urun,
        'ust_kategoriler': ust_kategoriler,
        'varyasyonlar': varyasyonlar,
        'title': 'Ürün Düzenle'
    }
    return render(request, 'urun/ekle.html', context)


@login_required
def urun_detay(request, pk):
    """Ürün detay view'ı"""
    urun = get_object_or_404(Urun, pk=pk)
    context = {'urun': urun}
    return render(request, 'urun/urun_detay.html', context)


@login_required
def urun_sil(request, pk):
    """Ürün silme view'ı"""
    urun = get_object_or_404(Urun, pk=pk)
    
    if request.method == 'POST':
        urun.aktif = False
        urun.save()
        messages.success(request, f'{urun.ad} başarıyla silindi.')
        return redirect('urun:liste')
    
    return render(request, 'urun/urun_sil.html', {'urun': urun})


# @login_required  # Geçici olarak kaldırıldı - test için
def kategori_yonetimi(request):
    """Kategori yönetimi view'ı"""
    ust_kategoriler = UrunKategoriUst.objects.all()
    
    context = {
        'ust_kategoriler': ust_kategoriler,
    }
    return render(request, 'urun/kategori_yonetimi.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def ust_kategori_ekle(request):
    """Üst kategori ekleme/düzenleme view'ı"""
    edit_id = request.GET.get('edit')
    
    if request.method == 'POST':
        ad = request.POST.get('ad')
        aciklama = request.POST.get('aciklama', '')
        
        if ad:
            if edit_id:
                # Düzenleme
                kategori = get_object_or_404(UrunKategoriUst, pk=edit_id)
                kategori.ad = ad
                kategori.aciklama = aciklama
                kategori.save()
                messages.success(request, f'✅ {ad} üst kategorisi başarıyla güncellendi.')
            else:
                # Yeni ekleme
                UrunKategoriUst.objects.create(ad=ad, aciklama=aciklama)
                messages.success(request, f'✅ {ad} üst kategorisi başarıyla eklendi.')
            
            return redirect('urun:kategori')
        else:
            messages.error(request, '❌ Kategori adı gerekli.')
    
    return redirect('urun:kategori')


# @login_required  # Geçici olarak kaldırıldı - test için
def ust_kategori_sil(request, pk):
    """Kategori silme view'ı"""
    if request.method == 'POST':
        try:
            kategori = get_object_or_404(UrunKategoriUst, pk=pk)
            kategori_ad = kategori.ad
            
            # Ürünleri kontrol et
            urun_count = kategori.urun_set.count()
            if urun_count > 0:
                messages.error(request, f'❌ {kategori_ad} kategorisi silinemez! {urun_count} adet ürün bulunmaktadır.')
            else:
                kategori.delete()
                messages.success(request, f'✅ {kategori_ad} kategorisi başarıyla silindi.')
                
        except Exception as e:
            messages.error(request, f'❌ Kategori silinirken hata oluştu: {str(e)}')
    
    return redirect('urun:kategori')


@login_required
def stok_durumu(request):
    """Stok durumu view'ı"""
    try:
        # Filtreler
        durum_filter = request.GET.get('durum', '')
        kategori_filter = request.GET.get('kategori', '')
        search = request.GET.get('q', '')
        
        # Base query
        urunler = Urun.objects.filter(aktif=True).select_related('kategori', 'marka')
        
        # Durum filtresi
        if durum_filter == 'tukenen':
            urunler = urunler.filter(stok_miktari=0)
        elif durum_filter == 'kritik':
            urunler = urunler.filter(stok_miktari__gt=0, stok_miktari__lte=F('minimum_stok'))
        elif durum_filter == 'normal':
            urunler = urunler.filter(stok_miktari__gt=F('minimum_stok'))
        
        # Kategori filtresi
        if kategori_filter:
            urunler = urunler.filter(kategori_id=kategori_filter)
        
        # Arama filtresi
        if search:
            urunler = urunler.filter(
                Q(ad__icontains=search) | 
                Q(barkod__icontains=search) | 
                Q(sku__icontains=search) |
                Q(kategori__ad__icontains=search) |
                Q(marka__ad__icontains=search)
            )
        
        # Sıralama
        siralama = request.GET.get('siralama', 'stok_asc')
        if siralama == 'stok_desc':
            urunler = urunler.order_by('-stok_miktari')
        elif siralama == 'stok_asc':
            urunler = urunler.order_by('stok_miktari')
        elif siralama == 'ad_asc':
            urunler = urunler.order_by('ad')
        elif siralama == 'ad_desc':
            urunler = urunler.order_by('-ad')
        elif siralama == 'kritik_once':
            # Önce kritik stok, sonra stok miktarına göre
            from django.db.models import Case, When, BooleanField
            urunler = urunler.annotate(
                kritik_durum=Case(
                    When(stok_miktari__lte=F('minimum_stok'), stok_miktari__gt=0, then=True),
                    default=False,
                    output_field=BooleanField()
                )
            ).order_by('-kritik_durum', 'stok_miktari')
        
        # İstatistikler hesapla
        total_products = Urun.objects.filter(aktif=True).count()
        tukenen = Urun.objects.filter(aktif=True, stok_miktari=0).count()
        kritik = Urun.objects.filter(aktif=True, stok_miktari__gt=0, stok_miktari__lte=F('minimum_stok')).count()
        normal = total_products - tukenen - kritik
        
        # Kritik stok uyarıları
        kritik_urunler = []
        if kritik > 0:
            kritik_urunler = Urun.objects.filter(
                aktif=True, 
                stok_miktari__gt=0, 
                stok_miktari__lte=F('minimum_stok')
            ).select_related('kategori', 'marka').order_by('stok_miktari')[:10]
        
        # Sayfalama
        paginator = Paginator(urunler, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Kategoriler dropdown için
        kategoriler = UrunKategoriUst.objects.all().order_by('ad')
        
        context = {
            'urunler': page_obj,
            'kategoriler': kategoriler,
            'toplam_urun': total_products,
            'normal_stok': normal,
            'kritik_stok': kritik,
            'tukenen_stok': tukenen,
            'kritik_urunler': kritik_urunler,
            'durum_filter': durum_filter,
            'kategori_filter': kategori_filter,
            'search': search,
            'siralama': siralama,
            'title': 'Stok Durumu Yönetimi',
        }
        return render(request, 'urun/stok_durumu.html', context)
        
    except Exception as e:
        messages.error(request, f'Stok durumu yüklenirken hata oluştu: {str(e)}')
        return render(request, 'urun/stok_durumu.html', {
            'urunler': None,
            'kategoriler': [],
            'toplam_urun': 0,
            'normal_stok': 0,
            'kritik_stok': 0,
            'tukenen_stok': 0,
            'kritik_urunler': [],
            'title': 'Stok Durumu Yönetimi',
        })


@login_required
def stok_guncelle(request):
    """Stok güncelleme AJAX view'ı"""
    if request.method == 'POST':
        try:
            urun_id = request.POST.get('urun_id')
            yeni_stok = request.POST.get('yeni_stok')
            aciklama = request.POST.get('aciklama', '')
            
            urun = get_object_or_404(Urun, id=urun_id)
            
            if yeni_stok and yeni_stok.isdigit():
                eski_stok = urun.stok_miktari
                urun.stok_miktari = int(yeni_stok)
                urun.save()
                
                # Aktivite logu ekle
                try:
                    from log.models import AktiviteLog
                    AktiviteLog.objects.create(
                        kullanici=request.user,
                        aktivite_tipi='stok_guncelleme',
                        baslik=f'Stok Güncellendi: {urun.ad}',
                        aciklama=f'Stok {eski_stok} → {yeni_stok}. {aciklama}',
                        urun=urun
                    )
                except:
                    pass  # Log hatası uygulama akışını bozmasın
                
                return JsonResponse({
                    'success': True,
                    'message': f'{urun.ad} stok miktarı başarıyla güncellendi.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Geçerli bir stok miktarı girin.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Hata oluştu: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Geçersiz istek.'
    })


@login_required
def varyasyon_yonetimi(request):
    """Varyasyon yönetimi view'ı"""
    varyasyonlar = Varyasyon.objects.all().order_by('tip', 'deger')
    context = {'varyasyonlar': varyasyonlar}
    return render(request, 'urun/varyasyon_yonetimi.html', context)


@login_required
def varyasyon_ekle(request):
    """Varyasyon ekleme view'ı"""
    if request.method == 'POST':
        tip = request.POST.get('tip')
        deger = request.POST.get('deger')
        
        if tip and deger:
            Varyasyon.objects.create(tip=tip, deger=deger)
            messages.success(request, 'Varyasyon başarıyla eklendi.')
            return redirect('urun:varyasyon_yonetimi')
        else:
            messages.error(request, 'Tip ve değer gerekli.')
    
    return render(request, 'urun/varyasyon_form.html', {'title': 'Varyasyon Ekle'})


# AJAX Views
@login_required
def barkod_kontrol(request):
    """Barkod kontrol AJAX view'ı"""
    barkod = request.GET.get('barkod')
    exists = Urun.objects.filter(barkod=barkod).exists()
    return JsonResponse({'exists': exists})


@login_required
def barkod_sorgula(request):
    """Barkod sorgulama view'ı"""
    context = {}
    
    # GET parametresini al (template form method="get" kullanıyor)
    barkod = request.GET.get('barkod')
    if barkod:
        context['barkod'] = barkod
        try:
            urun = Urun.objects.get(barkod=barkod, aktif=True)
            context['urun'] = urun
            context['success'] = True
        except Urun.DoesNotExist:
            context['error'] = 'Bu barkod ile ürün bulunamadı.'
            context['success'] = False
    
    return render(request, 'urun/barkod_sorgula.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def marka_listesi(request):
    """Marka listesi view'ı"""
    markalar = Marka.objects.annotate(
        urun_sayisi=Count('urun')
    ).order_by('ad')
    
    # Arama
    query = request.GET.get('q')
    if query:
        markalar = markalar.filter(ad__icontains=query)
    
    context = {
        'markalar': markalar,
        'query': query,
        'title': 'Marka Listesi',
    }
    return render(request, 'urun/marka_listesi.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def marka_ekle(request):
    """Marka ekleme view'ı"""
    if request.method == 'POST':
        ad = request.POST.get('ad')
        aciklama = request.POST.get('aciklama', '')
        logo = request.FILES.get('logo')
        
        if ad:
            # Aynı isimde marka var mı kontrol et
            if Marka.objects.filter(ad=ad).exists():
                messages.error(request, f'❌ "{ad}" adında bir marka zaten mevcut!')
                return render(request, 'urun/marka_ekle.html', {
                    'title': 'Yeni Marka Ekle',
                    'ad': ad,
                    'aciklama': aciklama,
                })
            
            marka = Marka.objects.create(
                ad=ad,
                aciklama=aciklama,
                logo=logo
            )
            
            # Aktivite logu
            if request.user.is_authenticated:
                AktiviteLog.objects.create(
                    kullanici=request.user,
                    aktivite_tipi='ekleme',
                    baslik='Marka Eklendi',
                    aciklama=f'{marka.ad} markası eklendi',
                    content_object=marka
                )
            
            messages.success(request, f'✅ {marka.ad} markası başarıyla eklendi!')
            return redirect('urun:marka_listesi')
        else:
            messages.error(request, '❌ Marka adı gereklidir!')
    
    context = {
        'title': 'Yeni Marka Ekle',
    }
    return render(request, 'urun/marka_ekle.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def marka_duzenle(request, pk):
    """Marka düzenleme view'ı"""
    marka = get_object_or_404(Marka, pk=pk)
    
    if request.method == 'POST':
        ad = request.POST.get('ad')
        aciklama = request.POST.get('aciklama', '')
        logo = request.FILES.get('logo')
        
        if ad:
            # Aynı isimde başka marka var mı kontrol et (kendisi hariç)
            if Marka.objects.filter(ad=ad).exclude(pk=marka.pk).exists():
                messages.error(request, f'❌ "{ad}" adında başka bir marka zaten mevcut!')
                return render(request, 'urun/marka_duzenle.html', {
                    'marka': marka,
                    'title': f'Marka Düzenle - {marka.ad}',
                })
            
            marka.ad = ad
            marka.aciklama = aciklama
            if logo:
                marka.logo = logo
            marka.save()
            
            # Aktivite logu
            if request.user.is_authenticated:
                AktiviteLog.objects.create(
                    kullanici=request.user,
                    aktivite_tipi='duzenleme',
                    baslik='Marka Düzenlendi',
                    aciklama=f'{marka.ad} markası düzenlendi',
                    content_object=marka
                )
            
            messages.success(request, f'✅ {marka.ad} markası başarıyla güncellendi!')
            return redirect('urun:marka_listesi')
        else:
            messages.error(request, '❌ Marka adı gereklidir!')
    
    context = {
        'marka': marka,
        'title': f'Marka Düzenle - {marka.ad}',
    }
    return render(request, 'urun/marka_duzenle.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def marka_sil(request, pk):
    """Marka silme view'ı"""
    marka = get_object_or_404(Marka, pk=pk)
    
    # Bu markaya ait ürün var mı kontrol et
    urun_sayisi = marka.urun_set.count()
    
    if request.method == 'POST':
        if urun_sayisi > 0:
            messages.error(request, f'❌ {marka.ad} markasına ait {urun_sayisi} ürün bulunduğu için silinemez!')
            return redirect('urun:marka_listesi')
        
        marka_ad = marka.ad
        marka.delete()
        
        # Aktivite logu
        if request.user.is_authenticated:
            AktiviteLog.objects.create(
                kullanici=request.user,
                aktivite_tipi='silme',
                baslik='Marka Silindi',
                aciklama=f'{marka_ad} markası silindi',
            )
        
        messages.success(request, f'✅ {marka_ad} markası başarıyla silindi!')
        return redirect('urun:marka_listesi')
    
    context = {
        'marka': marka,
        'urun_sayisi': urun_sayisi,
        'title': f'Marka Sil - {marka.ad}',
    }
    return render(request, 'urun/marka_sil.html', context)


@login_required
def en_cok_satanlar(request):
    """En çok satan ürünler listesi"""
    from django.db.models import Sum
    from satis.models import SatisDetay
    from datetime import datetime, timedelta
    
    # Tarih filtresi
    tarih_filtre = request.GET.get('tarih', '30')  # Varsayılan 30 gün
    
    if tarih_filtre == '7':
        baslangic_tarihi = datetime.now() - timedelta(days=7)
        tarih_baslik = 'Son 7 Gün'
    elif tarih_filtre == '30':
        baslangic_tarihi = datetime.now() - timedelta(days=30)
        tarih_baslik = 'Son 30 Gün'
    elif tarih_filtre == '90':
        baslangic_tarihi = datetime.now() - timedelta(days=90)
        tarih_baslik = 'Son 90 Gün'
    elif tarih_filtre == 'tumu':
        baslangic_tarihi = None
        tarih_baslik = 'Tüm Zamanlar'
    else:
        baslangic_tarihi = datetime.now() - timedelta(days=30)
        tarih_baslik = 'Son 30 Gün'
    
    # Base query
    satis_detaylari = SatisDetay.objects.select_related('urun', 'urun__kategori', 'urun__marka')
    
    if baslangic_tarihi:
        satis_detaylari = satis_detaylari.filter(satis__siparis_tarihi__gte=baslangic_tarihi)
    
    # Ürün bazında toplam satış miktarı ve tutarı
    en_cok_satanlar = satis_detaylari.values(
        'urun__id',
        'urun__ad', 
        'urun__barkod',
        'urun__kategori__ad',
        'urun__marka__ad',
        'urun__satis_fiyati',
        'urun__stok_miktari'
    ).annotate(
        toplam_adet=Sum('miktar'),
        toplam_tutar=Sum('toplam_fiyat')
    ).order_by('-toplam_adet')[:50]  # Top 50
    
    # Toplam değerleri hesapla
    toplam_satis_tutari = sum(item['toplam_tutar'] for item in en_cok_satanlar)
    toplam_satis_adedi = sum(item['toplam_adet'] for item in en_cok_satanlar)
    
    context = {
        'title': f'En Çok Satan Ürünler - {tarih_baslik}',
        'en_cok_satanlar': en_cok_satanlar,
        'tarih_filtre': tarih_filtre,
        'tarih_baslik': tarih_baslik,
        'toplam_satis_tutari': toplam_satis_tutari,
        'toplam_satis_adedi': toplam_satis_adedi,
    }
    return render(request, 'urun/en_cok_satanlar.html', context)


@login_required
def kar_zarar_raporu(request):
    """Kar zarar raporu"""
    from django.db.models import Sum, Count
    from satis.models import SatisDetay, Satis
    from datetime import datetime, timedelta
    
    # Tarih filtresi
    tarih_filtre = request.GET.get('tarih', '30')  # Varsayılan 30 gün
    
    if tarih_filtre == 'bugun':
        baslangic_tarihi = datetime.now().date()
        bitis_tarihi = datetime.now().date()
        tarih_baslik = 'Bugün'
    elif tarih_filtre == '7':
        baslangic_tarihi = (datetime.now() - timedelta(days=7)).date()
        bitis_tarihi = datetime.now().date()
        tarih_baslik = 'Son 7 Gün'
    elif tarih_filtre == '30':
        baslangic_tarihi = (datetime.now() - timedelta(days=30)).date()
        bitis_tarihi = datetime.now().date()
        tarih_baslik = 'Son 30 Gün'
    elif tarih_filtre == 'ay':
        baslangic_tarihi = datetime.now().replace(day=1).date()
        bitis_tarihi = datetime.now().date()
        tarih_baslik = 'Bu Ay'
    elif tarih_filtre == 'yil':
        baslangic_tarihi = datetime.now().replace(month=1, day=1).date()
        bitis_tarihi = datetime.now().date()
        tarih_baslik = 'Bu Yıl'
    else:
        baslangic_tarihi = (datetime.now() - timedelta(days=30)).date()
        bitis_tarihi = datetime.now().date()
        tarih_baslik = 'Son 30 Gün'
    
    # Satışları filtrele
    satislar = Satis.objects.filter(
        siparis_tarihi__date__gte=baslangic_tarihi,
        siparis_tarihi__date__lte=bitis_tarihi
    )
    
    # Satış detayları
    satis_detaylari = SatisDetay.objects.filter(
        satis__in=satislar
    ).select_related('urun', 'urun__kategori', 'urun__marka')
    
    # Toplam kar hesaplama
    kar_detaylari = []
    toplam_alis_tutari = 0
    toplam_satis_tutari = 0
    toplam_kar = 0
    toplam_adet = 0
    
    for detay in satis_detaylari:
        alis_tutari = detay.urun.alis_fiyati * detay.miktar
        satis_tutari = detay.toplam_fiyat
        kar = satis_tutari - alis_tutari
        kar_yuzde = (kar / alis_tutari * 100) if alis_tutari > 0 else 0
        
        kar_detaylari.append({
            'urun': detay.urun,
            'miktar': detay.miktar,
            'alis_tutari': alis_tutari,
            'satis_tutari': satis_tutari,
            'kar': kar,
            'kar_yuzde': kar_yuzde,
            'tarih': detay.satis.siparis_tarihi,
        })
        
        toplam_alis_tutari += alis_tutari
        toplam_satis_tutari += satis_tutari
        toplam_kar += kar
        toplam_adet += detay.miktar
    
    # Kar marjı hesaplama
    kar_marji_yuzde = (toplam_kar / toplam_alis_tutari * 100) if toplam_alis_tutari > 0 else 0
    
    # Kategori bazında kar analizi
    from collections import defaultdict
    kategori_kar = defaultdict(lambda: {'alis': 0, 'satis': 0, 'kar': 0, 'adet': 0})
    
    for detay in kar_detaylari:
        kategori = detay['urun'].kategori.ad if detay['urun'].kategori else 'Kategori Yok'
        kategori_kar[kategori]['alis'] += detay['alis_tutari']
        kategori_kar[kategori]['satis'] += detay['satis_tutari']
        kategori_kar[kategori]['kar'] += detay['kar']
        kategori_kar[kategori]['adet'] += detay['miktar']
    
    # Kategori kar marjı hesapla
    for kategori in kategori_kar:
        if kategori_kar[kategori]['alis'] > 0:
            kategori_kar[kategori]['kar_yuzde'] = (
                kategori_kar[kategori]['kar'] / kategori_kar[kategori]['alis'] * 100
            )
        else:
            kategori_kar[kategori]['kar_yuzde'] = 0
    
    context = {
        'title': f'Kar Zarar Raporu - {tarih_baslik}',
        'tarih_filtre': tarih_filtre,
        'tarih_baslik': tarih_baslik,
        'baslangic_tarihi': baslangic_tarihi,
        'bitis_tarihi': bitis_tarihi,
        'kar_detaylari': sorted(kar_detaylari, key=lambda x: x['kar'], reverse=True)[:100],  # Top 100
        'toplam_alis_tutari': toplam_alis_tutari,
        'toplam_satis_tutari': toplam_satis_tutari,
        'toplam_kar': toplam_kar,
        'toplam_adet': toplam_adet,
        'kar_marji_yuzde': kar_marji_yuzde,
        'kategori_kar': dict(kategori_kar),
        'satis_sayisi': satislar.count(),
    }
    return render(request, 'urun/kar_zarar_raporu.html', context)
