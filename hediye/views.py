from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import HediyeCeki, HediyeCekiKullanim


@login_required
def hediye_ceki_listesi(request):
    """Hediye çeki listesi"""
    # Arama ve filtreleme
    search_query = request.GET.get('search', '')
    durum_filter = request.GET.get('durum', '')
    tarih_filter = request.GET.get('tarih', '')
    
    hediye_cekleri = HediyeCeki.objects.all()
    
    # Arama
    if search_query:
        hediye_cekleri = hediye_cekleri.filter(
            Q(kod__icontains=search_query) |
            Q(musteri__ad__icontains=search_query) |
            Q(musteri__soyad__icontains=search_query) |
            Q(aciklama__icontains=search_query)
        )
    
    # Durum filtresi
    if durum_filter:
        hediye_cekleri = hediye_cekleri.filter(durum=durum_filter)
    
    # Tarih filtresi
    if tarih_filter == 'bugun':
        hediye_cekleri = hediye_cekleri.filter(olusturma_tarihi__date=timezone.now().date())
    elif tarih_filter == 'bu_hafta':
        from datetime import timedelta
        bir_hafta_once = timezone.now().date() - timedelta(days=7)
        hediye_cekleri = hediye_cekleri.filter(olusturma_tarihi__date__gte=bir_hafta_once)
    elif tarih_filter == 'bu_ay':
        hediye_cekleri = hediye_cekleri.filter(
            olusturma_tarihi__year=timezone.now().year,
            olusturma_tarihi__month=timezone.now().month
        )
    elif tarih_filter == 'suresi_dolan':
        hediye_cekleri = hediye_cekleri.filter(gecerlilik_tarihi__lt=timezone.now().date())
    
    # Sıralama
    hediye_cekleri = hediye_cekleri.order_by('-olusturma_tarihi')
    
    # Sayfalama
    paginator = Paginator(hediye_cekleri, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    toplam_cekler = HediyeCeki.objects.count()
    aktif_cekler = HediyeCeki.objects.filter(durum='aktif', aktif=True).count()
    kullanilmis_cekler = HediyeCeki.objects.filter(durum='kullanilmis').count()
    iptal_cekler = HediyeCeki.objects.filter(durum='iptal').count()
    
    toplam_tutar = sum(cek.tutar for cek in HediyeCeki.objects.filter(durum='aktif', aktif=True))
    kalan_tutar = sum(cek.kalan_tutar for cek in HediyeCeki.objects.filter(durum='aktif', aktif=True))
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'durum_filter': durum_filter,
        'tarih_filter': tarih_filter,
        'toplam_cekler': toplam_cekler,
        'aktif_cekler': aktif_cekler,
        'kullanilmis_cekler': kullanilmis_cekler,
        'iptal_cekler': iptal_cekler,
        'toplam_tutar': toplam_tutar,
        'kalan_tutar': kalan_tutar,
        'durum_secenekleri': HediyeCeki.DURUM_SECENEKLERI,
    }
    
    return render(request, 'hediye/liste.html', context)


@login_required
def hediye_ceki_detay(request, pk):
    """Hediye çeki detay sayfası"""
    hediye_ceki = get_object_or_404(HediyeCeki, pk=pk)
    
    # Kullanım geçmişi
    kullanimlar = hediye_ceki.kullanimlar.all().order_by('-kullanim_tarihi')
    
    context = {
        'hediye_ceki': hediye_ceki,
        'kullanimlar': kullanimlar,
    }
    
    return render(request, 'hediye/detay.html', context)


@login_required
def hediye_ceki_iptal(request, pk):
    """Hediye çeki iptal etme"""
    hediye_ceki = get_object_or_404(HediyeCeki, pk=pk)
    
    # Sadece aktif çekler iptal edilebilir
    if hediye_ceki.durum != 'aktif':
        messages.error(request, 'Sadece aktif hediye çekleri iptal edilebilir!')
        return redirect('hediye:detay', pk=pk)
    
    # Kullanılmış çekler iptal edilemez
    if hediye_ceki.kalan_tutar < hediye_ceki.tutar:
        messages.error(request, 'Kısmen veya tamamen kullanılmış hediye çekleri iptal edilemez!')
        return redirect('hediye:detay', pk=pk)
    
    if request.method == 'POST':
        hediye_ceki.durum = 'iptal'
        hediye_ceki.aktif = False
        hediye_ceki.save()
        
        messages.success(request, f'Hediye çeki başarıyla iptal edildi: {hediye_ceki.kod}')
        return redirect('hediye:liste')
    
    return render(request, 'hediye/iptal_onay.html', {'hediye_ceki': hediye_ceki})


@login_required
def hediye_ceki_ajax_sorgula(request):
    """AJAX hediye çeki sorgulama"""
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
            'durum': hediye_ceki.get_durum_display(),
            'musteri': f"{hediye_ceki.musteri.ad} {hediye_ceki.musteri.soyad}" if hediye_ceki.musteri else None
        }
        
        return JsonResponse({'success': True, 'hediye_ceki': data})
        
    except HediyeCeki.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Hediye çeki bulunamadı!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'})


@login_required
def hediye_ceki_yazdir(request, pk):
    """Hediye çeki yazdırma sayfası - 8cm termal yazıcı için optimize edilmiş"""
    hediye_ceki = get_object_or_404(HediyeCeki, pk=pk)
    
    context = {
        'hediye_ceki': hediye_ceki,
    }
    
    return render(request, 'hediye/yazdir.html', context)
