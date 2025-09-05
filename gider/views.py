from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth, TruncDay
from datetime import date, datetime, timedelta
from decimal import Decimal
from .models import Gider, GiderKategori
from .forms import GiderForm, GiderKategoriForm, GiderAramaForm
from kasa.models import Kasa, KasaHareket
from log.models import AktiviteLog


# @login_required  # Geçici olarak kaldırıldı - test için
def gider_listesi(request):
    """Gider listesi view'ı"""
    
    # Arama ve filtreleme
    form = GiderAramaForm(request.GET)
    giderler = Gider.objects.filter(aktif=True).select_related('kategori', 'olusturan')
    
    if form.is_valid():
        if form.cleaned_data['baslik']:
            giderler = giderler.filter(baslik__icontains=form.cleaned_data['baslik'])
        
        if form.cleaned_data['kategori']:
            giderler = giderler.filter(kategori=form.cleaned_data['kategori'])
        
        if form.cleaned_data['baslangic_tarihi']:
            giderler = giderler.filter(tarih__gte=form.cleaned_data['baslangic_tarihi'])
        
        if form.cleaned_data['bitis_tarihi']:
            giderler = giderler.filter(tarih__lte=form.cleaned_data['bitis_tarihi'])
        
        if form.cleaned_data['odeme_yontemi']:
            giderler = giderler.filter(odeme_yontemi=form.cleaned_data['odeme_yontemi'])
        
        if form.cleaned_data['min_tutar']:
            giderler = giderler.filter(tutar__gte=form.cleaned_data['min_tutar'])
        
        if form.cleaned_data['max_tutar']:
            giderler = giderler.filter(tutar__lte=form.cleaned_data['max_tutar'])
    
    # Sayfalama
    paginator = Paginator(giderler, 20)  # Sayfa başına 20 gider
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    toplam_tutar = giderler.aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0')
    gider_sayisi = giderler.count()
    
    # Bugünkü giderler
    bugun = date.today()
    bugun_giderler = giderler.filter(tarih=bugun)
    bugun_toplam = bugun_giderler.aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0')
    bugun_sayisi = bugun_giderler.count()
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'toplam_tutar': toplam_tutar,
        'gider_sayisi': gider_sayisi,
        'bugun_toplam': bugun_toplam,
        'bugun_sayisi': bugun_sayisi,
        'title': 'Giderler',
    }
    
    return render(request, 'gider/liste.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def gider_ekle(request):
    """Gider ekleme view'ı"""
    
    if request.method == 'POST':
        form = GiderForm(request.POST, request.FILES)
        if form.is_valid():
            gider = form.save(commit=False)
            gider.olusturan = request.user if request.user.is_authenticated else None
            gider.save()
            
            # Kasa hareketi oluştur
            kasa = None
            if gider.odeme_yontemi == 'nakit':
                kasa = Kasa.objects.filter(tip='nakit', aktif=True).first()
            elif gider.odeme_yontemi == 'kredi_karti':
                kasa = Kasa.objects.filter(tip='kart', aktif=True).first()
            elif gider.odeme_yontemi == 'banka_havalesi':
                kasa = Kasa.objects.filter(tip='banka', aktif=True).first()
            
            if kasa:
                KasaHareket.objects.create(
                    kasa=kasa,
                    tip='cikis',
                    kaynak='gider',
                    tutar=gider.tutar,
                    aciklama=f'Gider - {gider.baslik}',
                    gider_id=gider.id,
                    kullanici=request.user if request.user.is_authenticated else None
                )
            
            # Aktivite logu
            if request.user.is_authenticated:
                AktiviteLog.objects.create(
                    kullanici=request.user,
                    aktivite_tipi='ekleme',
                    baslik='Gider Eklendi',
                    aciklama=f'{gider.baslik} gideri eklendi ({gider.tutar} ₺)',
                    content_object=gider
                )
            
            messages.success(request, f'✅ {gider.baslik} gideri başarıyla eklendi!')
            return redirect('gider:liste')
    else:
        form = GiderForm()
    
    context = {
        'form': form,
        'title': 'Yeni Gider Ekle',
    }
    
    return render(request, 'gider/ekle.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def gider_duzenle(request, pk):
    """Gider düzenleme view'ı"""
    
    gider = get_object_or_404(Gider, pk=pk, aktif=True)
    
    if request.method == 'POST':
        form = GiderForm(request.POST, request.FILES, instance=gider)
        if form.is_valid():
            gider = form.save()
            
            # Aktivite logu
            if request.user.is_authenticated:
                AktiviteLog.objects.create(
                    kullanici=request.user,
                    aktivite_tipi='duzenleme',
                    baslik='Gider Düzenlendi',
                    aciklama=f'{gider.baslik} gideri düzenlendi',
                    content_object=gider
                )
            
            messages.success(request, f'✅ {gider.baslik} gideri başarıyla güncellendi!')
            return redirect('gider:liste')
    else:
        form = GiderForm(instance=gider)
    
    context = {
        'form': form,
        'gider': gider,
        'title': f'Gider Düzenle - {gider.baslik}',
    }
    
    return render(request, 'gider/duzenle.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def gider_sil(request, pk):
    """Gider silme view'ı"""
    
    gider = get_object_or_404(Gider, pk=pk, aktif=True)
    
    if request.method == 'POST':
        baslik = gider.baslik
        gider.aktif = False  # Soft delete
        gider.save()
        
        # Aktivite logu
        if request.user.is_authenticated:
            AktiviteLog.objects.create(
                kullanici=request.user,
                aktivite_tipi='silme',
                baslik='Gider Silindi',
                aciklama=f'{baslik} gideri silindi',
            )
        
        messages.success(request, f'✅ {baslik} gideri başarıyla silindi!')
        return redirect('gider:liste')
    
    context = {
        'gider': gider,
        'title': f'Gider Sil - {gider.baslik}',
    }
    
    return render(request, 'gider/sil.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def gider_detay(request, pk):
    """Gider detay view'ı"""
    
    gider = get_object_or_404(Gider, pk=pk, aktif=True)
    
    context = {
        'gider': gider,
        'title': f'Gider Detayı - {gider.baslik}',
    }
    
    return render(request, 'gider/detay.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def gider_rapor(request):
    """Gider raporları view'ı"""
    
    # Tarih filtreleme
    baslangic_tarihi = request.GET.get('baslangic_tarihi')
    bitis_tarihi = request.GET.get('bitis_tarihi')
    
    # Varsayılan olarak bu ay
    if not baslangic_tarihi:
        baslangic_tarihi = date.today().replace(day=1)
    else:
        baslangic_tarihi = datetime.strptime(baslangic_tarihi, '%Y-%m-%d').date()
    
    if not bitis_tarihi:
        bitis_tarihi = date.today()
    else:
        bitis_tarihi = datetime.strptime(bitis_tarihi, '%Y-%m-%d').date()
    
    # Giderleri filtrele
    giderler = Gider.objects.filter(
        aktif=True,
        tarih__gte=baslangic_tarihi,
        tarih__lte=bitis_tarihi
    ).select_related('kategori')
    
    # Genel istatistikler
    toplam_tutar = giderler.aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0')
    toplam_gider = giderler.count()
    ortalama_gider = toplam_tutar / toplam_gider if toplam_gider > 0 else Decimal('0')
    
    # Kategoriye göre dağılım
    kategori_dagilim = giderler.values('kategori__ad', 'kategori__renk').annotate(
        toplam=Sum('tutar'),
        adet=Count('id')
    ).order_by('-toplam')
    
    # Günlük trend (son 30 gün)
    gunluk_trend = giderler.filter(
        tarih__gte=date.today() - timedelta(days=30)
    ).annotate(
        gun=TruncDay('tarih')
    ).values('gun').annotate(
        toplam=Sum('tutar')
    ).order_by('gun')
    
    # En büyük giderler
    en_buyuk_giderler = giderler.order_by('-tutar')[:10]
    
    context = {
        'baslangic_tarihi': baslangic_tarihi,
        'bitis_tarihi': bitis_tarihi,
        'toplam_tutar': toplam_tutar,
        'toplam_gider': toplam_gider,
        'ortalama_gider': ortalama_gider,
        'kategori_dagilim': kategori_dagilim,
        'gunluk_trend': gunluk_trend,
        'en_buyuk_giderler': en_buyuk_giderler,
        'title': 'Gider Raporları',
    }
    
    return render(request, 'gider/rapor.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def kategori_liste(request):
    """Gider kategorileri listesi"""
    kategoriler = GiderKategori.objects.annotate(
        gider_sayisi=Count('gider')
    ).order_by('ad')
    
    context = {
        'kategoriler': kategoriler,
        'title': 'Gider Kategorileri',
    }
    return render(request, 'gider/kategori_liste.html', context)


# @login_required  # Geçici olarak kaldırıldı - test için
def kategori_ekle(request):
    """Gider kategorisi ekleme"""
    
    if request.method == 'POST':
        ad = request.POST.get('ad')
        aciklama = request.POST.get('aciklama', '')
        renk = request.POST.get('renk', '#007bff')
        ikon = request.POST.get('ikon', 'fas fa-tag')
        
        if ad:
            kategori = GiderKategori.objects.create(
                ad=ad,
                aciklama=aciklama,
                renk=renk,
                ikon=ikon
            )
            messages.success(request, f'✅ {kategori.ad} kategorisi başarıyla eklendi!')
        else:
            messages.error(request, '❌ Kategori adı gereklidir!')
            
        return redirect('gider:kategori_liste')
    
    return redirect('gider:kategori_liste')


# @login_required  # Geçici olarak kaldırıldı - test için
def kategori_duzenle(request, kategori_id):
    """Gider kategorisi düzenleme"""
    kategori = get_object_or_404(GiderKategori, id=kategori_id)
    
    if request.method == 'POST':
        kategori.ad = request.POST.get('ad', kategori.ad)
        kategori.aciklama = request.POST.get('aciklama', kategori.aciklama)
        kategori.renk = request.POST.get('renk', kategori.renk)
        kategori.ikon = request.POST.get('ikon', kategori.ikon)
        kategori.save()
        
        messages.success(request, f'✅ {kategori.ad} kategorisi başarıyla güncellendi!')
        return redirect('gider:kategori_liste')
    
    return redirect('gider:kategori_liste')


# @login_required  # Geçici olarak kaldırıldı - test için
def rapor(request):
    """Gider raporları"""
    bugün = date.today()
    bu_ay_başı = bugün.replace(day=1)
    
    # Temel istatistikler
    bugün_giderleri = Gider.objects.filter(
        tarih=bugün, aktif=True
    ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0')
    
    bu_ay_giderleri = Gider.objects.filter(
        tarih__gte=bu_ay_başı, aktif=True
    ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0')
    
    # Kategori bazında istatistikler
    kategori_istatistikleri = GiderKategori.objects.annotate(
        bu_ay_toplam=Sum('gider__tutar', filter=Q(gider__tarih__gte=bu_ay_başı, gider__aktif=True)),
        gider_adedi=Count('gider', filter=Q(gider__aktif=True))
    ).order_by('-bu_ay_toplam')
    
    # Günlük trend (son 30 gün)
    otuz_gün_önce = bugün - timedelta(days=30)
    günlük_trend = Gider.objects.filter(
        tarih__gte=otuz_gün_önce,
        aktif=True
    ).values('tarih').annotate(
        toplam=Sum('tutar')
    ).order_by('tarih')
    
    # Ödeme yöntemi dağılımı
    ödeme_dağılımı = Gider.objects.filter(
        tarih__gte=bu_ay_başı,
        aktif=True
    ).values('odeme_yontemi').annotate(
        toplam=Sum('tutar'),
        adet=Count('id')
    ).order_by('-toplam')
    
    context = {
        'title': 'Gider Raporları',
        'bugün_giderleri': bugün_giderleri,
        'bu_ay_giderleri': bu_ay_giderleri,
        'kategori_istatistikleri': kategori_istatistikleri,
        'günlük_trend': günlük_trend,
        'ödeme_dağılımı': ödeme_dağılımı,
        'bugün': bugün,
        'bu_ay_başı': bu_ay_başı,
    }
    
    return render(request, 'gider/rapor.html', context)



