from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Musteri, Tahsilat, TahsilatDetay, BorcAlacakHareket
from satis.models import Satis, Odeme
import json
from decimal import Decimal


@login_required
def borc_alacak_listesi(request):
    """Müşteri borç-alacak listesi"""
    # Filtreleme
    search = request.GET.get('search', '')
    durum = request.GET.get('durum', 'all')  # all, borclu, alacakli
    
    # Borcu olan müşteriler (acik_hesap_bakiye > 0)
    musteriler = Musteri.objects.filter(aktif=True)
    
    if search:
        musteriler = musteriler.filter(
            Q(ad__icontains=search) |
            Q(soyad__icontains=search) |
            Q(telefon__icontains=search) |
            Q(firma_adi__icontains=search)
        )
    
    if durum == 'borclu':
        musteriler = musteriler.filter(acik_hesap_bakiye__gt=0)
    elif durum == 'alacakli':
        musteriler = musteriler.filter(acik_hesap_bakiye__lt=0)
    
    # Müşteri bazında istatistikler ekle
    for musteri in musteriler:
        # Son 30 günlük satışlar
        musteri.son_30gun_satis = Satis.objects.filter(
            musteri=musteri,
            durum='tamamlandi',
            satis_tarihi__gte=timezone.now() - timezone.timedelta(days=30)
        ).aggregate(toplam=Sum('toplam_tutar'))['toplam'] or 0
        
        # Son 30 günlük tahsilatlar
        musteri.son_30gun_tahsilat = Tahsilat.objects.filter(
            musteri=musteri,
            durum='tahsil_edildi',
            tahsilat_tarihi__gte=timezone.now() - timezone.timedelta(days=30)
        ).aggregate(toplam=Sum('tutar'))['toplam'] or 0
    
    # Sayfalama
    paginator = Paginator(musteriler.order_by('-acik_hesap_bakiye'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Özet istatistikler
    toplam_borc = musteriler.filter(acik_hesap_bakiye__gt=0).aggregate(
        toplam=Sum('acik_hesap_bakiye'))['toplam'] or 0
    toplam_alacak = abs(musteriler.filter(acik_hesap_bakiye__lt=0).aggregate(
        toplam=Sum('acik_hesap_bakiye'))['toplam'] or 0)
    borclu_musteri_sayisi = musteriler.filter(acik_hesap_bakiye__gt=0).count()
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'durum': durum,
        'toplam_borc': toplam_borc,
        'toplam_alacak': toplam_alacak,
        'borclu_musteri_sayisi': borclu_musteri_sayisi,
        'toplam_musteri_sayisi': musteriler.count(),
    }
    
    return render(request, 'musteri/borc_alacak_listesi.html', context)


@login_required
def musteri_borc_detay(request, musteri_id):
    """Müşteri borç detayı"""
    musteri = get_object_or_404(Musteri, id=musteri_id)
    
    # Veresiye satışlar (açık hesap ödemeli)
    # Açık hesap ödemesi olan satışları bul
    acik_hesap_satis_ids = Odeme.objects.filter(
        odeme_tipi='acik_hesap'
    ).values_list('satis_id', flat=True)
    
    odenmemis_satislar = Satis.objects.filter(
        id__in=acik_hesap_satis_ids,
        musteri=musteri,
        durum='tamamlandi'
    ).order_by('-satis_tarihi')
    
    # Son hareketler
    hareketler = BorcAlacakHareket.objects.filter(
        musteri=musteri
    ).order_by('-hareket_tarihi')[:20]
    
    # Son tahsilatlar
    tahsilatlar = Tahsilat.objects.filter(
        musteri=musteri
    ).order_by('-tahsilat_tarihi')[:10]
    
    context = {
        'musteri': musteri,
        'odenmemis_satislar': odenmemis_satislar,
        'hareketler': hareketler,
        'tahsilatlar': tahsilatlar,
    }
    
    return render(request, 'musteri/musteri_borc_detay.html', context)


@login_required
def tahsilat_formu(request, musteri_id=None):
    """Tahsilat yapma formu"""
    musteri = None
    if musteri_id:
        musteri = get_object_or_404(Musteri, id=musteri_id)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            musteri_id = request.POST.get('musteri_id')
            if not musteri_id and musteri:
                musteri_id = musteri.id
                
            musteri_obj = get_object_or_404(Musteri, id=musteri_id)
            tutar = Decimal(request.POST.get('tutar', '0'))
            tahsilat_tipi = request.POST.get('tahsilat_tipi')
            aciklama = request.POST.get('aciklama', '')
            
            # Çek/Senet için ek bilgiler
            vade_tarihi = request.POST.get('vade_tarihi') if tahsilat_tipi in ['cek', 'senet'] else None
            cek_senet_no = request.POST.get('cek_senet_no') if tahsilat_tipi in ['cek', 'senet'] else None
            banka = request.POST.get('banka') if tahsilat_tipi in ['cek', 'senet'] else None
            
            # Havale/EFT için
            referans_no = request.POST.get('referans_no') if tahsilat_tipi == 'havale' else None
            
            if tutar <= 0:
                messages.error(request, 'Tahsilat tutarı 0\'dan büyük olmalıdır!')
                return redirect('musteri:tahsilat_formu', musteri_id=musteri_obj.id)
            
            if tutar > musteri_obj.acik_hesap_bakiye:
                messages.warning(request, f'Tahsilat tutarı müşteri borcundan ({musteri_obj.acik_hesap_bakiye}₺) büyük!')
            
            # Tahsilat kaydı oluştur
            tahsilat = Tahsilat.objects.create(
                musteri=musteri_obj,
                tutar=tutar,
                tahsilat_tipi=tahsilat_tipi,
                vade_tarihi=vade_tarihi,
                cek_senet_no=cek_senet_no,
                banka=banka,
                referans_no=referans_no,
                aciklama=aciklama,
                tahsilat_eden=request.user,
                durum='tahsil_edildi' if tahsilat_tipi not in ['cek', 'senet'] else 'beklemede'
            )
            
            # Müşteri bakiyesini güncelle (Tahsilat.save() metodunda otomatik yapılıyor)
            # Borç-alacak hareketi ekle
            musteri_obj.alacak_hareket_ekle(
                tutar=tutar,
                aciklama=f'Tahsilat - {tahsilat.tahsilat_no}',
                tahsilat=tahsilat,
                user=request.user
            )
            
            messages.success(request, f'Tahsilat başarıyla kaydedildi. Tahsilat No: {tahsilat.tahsilat_no}')
            return redirect('musteri:tahsilat_detay', tahsilat_id=tahsilat.id)
            
        except Exception as e:
            messages.error(request, f'Tahsilat kaydedilirken hata oluştu: {str(e)}')
    
    # Ödenmemiş satışlar (veresiye satışlar)
    odenmemis_satislar = []
    if musteri:
        # Açık hesap ödemesi olan satışları bul
        acik_hesap_satis_ids = Odeme.objects.filter(
            odeme_tipi='acik_hesap'
        ).values_list('satis_id', flat=True)
        
        odenmemis_satislar = Satis.objects.filter(
            id__in=acik_hesap_satis_ids,
            musteri=musteri,
            durum='tamamlandi'
        ).order_by('-satis_tarihi')
    
    context = {
        'musteri': musteri,
        'odenmemis_satislar': odenmemis_satislar,
    }
    
    return render(request, 'musteri/tahsilat_formu.html', context)


@login_required
def tahsilat_listesi(request):
    """Tahsilat listesi"""
    search = request.GET.get('search', '')
    durum = request.GET.get('durum', 'all')
    baslangic_tarihi = request.GET.get('baslangic_tarihi', '')
    bitis_tarihi = request.GET.get('bitis_tarihi', '')
    
    tahsilatlar = Tahsilat.objects.all()
    
    if search:
        tahsilatlar = tahsilatlar.filter(
            Q(tahsilat_no__icontains=search) |
            Q(musteri__ad__icontains=search) |
            Q(musteri__soyad__icontains=search) |
            Q(musteri__telefon__icontains=search)
        )
    
    if durum != 'all':
        tahsilatlar = tahsilatlar.filter(durum=durum)
    
    if baslangic_tarihi:
        tahsilatlar = tahsilatlar.filter(tahsilat_tarihi__date__gte=baslangic_tarihi)
    
    if bitis_tarihi:
        tahsilatlar = tahsilatlar.filter(tahsilat_tarihi__date__lte=bitis_tarihi)
    
    # Sayfalama
    paginator = Paginator(tahsilatlar.order_by('-tahsilat_tarihi'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Özet
    toplam_tahsilat = tahsilatlar.aggregate(toplam=Sum('tutar'))['toplam'] or 0
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'durum': durum,
        'baslangic_tarihi': baslangic_tarihi,
        'bitis_tarihi': bitis_tarihi,
        'toplam_tahsilat': toplam_tahsilat,
    }
    
    return render(request, 'musteri/tahsilat_listesi.html', context)


@login_required
def tahsilat_detay(request, tahsilat_id):
    """Tahsilat detayı ve fiş"""
    tahsilat = get_object_or_404(Tahsilat, id=tahsilat_id)
    
    context = {
        'tahsilat': tahsilat,
    }
    
    return render(request, 'musteri/tahsilat_detay.html', context)


@login_required
def musteri_arama_ajax(request):
    """AJAX müşteri arama"""
    q = request.GET.get('q', '')
    
    if len(q) < 2:
        return JsonResponse({'results': []})
    
    # Önce tüm müşterileri ara (borç filtresiz)
    musteriler = Musteri.objects.filter(
        Q(ad__icontains=q) |
        Q(soyad__icontains=q) |
        Q(telefon__icontains=q) |
        Q(firma_adi__icontains=q),
        aktif=True
    )[:10]
    
    results = []
    for musteri in musteriler:
        # Borç durumunu kontrol et
        borc_durumu = "Borçlu" if musteri.acik_hesap_bakiye > 0 else "Borçsuz"
        results.append({
            'id': musteri.id,
            'text': f"{musteri} - {musteri.telefon} - {borc_durumu} ({musteri.acik_hesap_bakiye}₺)",
            'borc': float(musteri.acik_hesap_bakiye)
        })
    
    return JsonResponse({'results': results})


@login_required
def tahsilat_iptal(request, tahsilat_id):
    """Tahsilat iptal etme"""
    tahsilat = get_object_or_404(Tahsilat, id=tahsilat_id)
    
    if request.method == 'POST':
        if tahsilat.durum == 'iptal':
            messages.warning(request, 'Bu tahsilat zaten iptal edilmiş!')
            return redirect('musteri:tahsilat_detay', tahsilat_id=tahsilat.id)
        
        try:
            # Müşteri bakiyesini eski haline getir
            tahsilat.musteri.acik_hesap_bakiye += tahsilat.tutar
            tahsilat.musteri.save()
            
            # Tahsilat durumunu iptal et
            tahsilat.durum = 'iptal'
            tahsilat.save()
            
            # İptal hareketi ekle
            tahsilat.musteri.borc_hareket_ekle(
                tutar=tahsilat.tutar,
                aciklama=f'Tahsilat İptal - {tahsilat.tahsilat_no}',
                user=request.user
            )
            
            messages.success(request, 'Tahsilat başarıyla iptal edildi!')
            return redirect('musteri:tahsilat_detay', tahsilat_id=tahsilat.id)
            
        except Exception as e:
            messages.error(request, f'Tahsilat iptal edilirken hata oluştu: {str(e)}')
    
    context = {
        'tahsilat': tahsilat,
    }
    
    return render(request, 'musteri/tahsilat_iptal.html', context)
