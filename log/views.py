from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import AktiviteLog, SistemHatasi, LoginLog


@login_required
def aktivite_loglari(request):
    """Aktivite logları view'ı"""
    loglar = AktiviteLog.objects.all().order_by('-tarih')
    
    # Filtreler
    aktivite_tipi = request.GET.get('tip')
    if aktivite_tipi:
        loglar = loglar.filter(aktivite_tipi=aktivite_tipi)
    
    kullanici = request.GET.get('kullanici')
    if kullanici:
        loglar = loglar.filter(kullanici__username__icontains=kullanici)
    
    # Tarih aralığı
    baslangic = request.GET.get('baslangic')
    bitis = request.GET.get('bitis')
    if baslangic:
        loglar = loglar.filter(tarih__date__gte=baslangic)
    if bitis:
        loglar = loglar.filter(tarih__date__lte=bitis)
    
    # Sayfalama
    paginator = Paginator(loglar, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Aktivite tipleri listesi
    aktivite_tipleri = AktiviteLog.AKTIVITE_TIPLERI
    
    context = {
        'page_obj': page_obj,
        'aktivite_tipleri': aktivite_tipleri,
        'secili_tip': aktivite_tipi,
        'secili_kullanici': kullanici,
        'baslangic': baslangic,
        'bitis': bitis,
    }
    return render(request, 'log/aktivite_loglari.html', context)


@login_required
def aktivite_detay(request, pk):
    """Aktivite log detay view'ı"""
    log = get_object_or_404(AktiviteLog, pk=pk)
    context = {'log': log}
    return render(request, 'log/aktivite_detay.html', context)


@login_required
def sistem_hatalari(request):
    """Sistem hataları view'ı"""
    hatalar = SistemHatasi.objects.all().order_by('-tarih')
    
    # Filtreler
    seviye = request.GET.get('seviye')
    if seviye:
        hatalar = hatalar.filter(seviye=seviye)
    
    cozuldu = request.GET.get('cozuldu')
    if cozuldu == '1':
        hatalar = hatalar.filter(cozuldu=True)
    elif cozuldu == '0':
        hatalar = hatalar.filter(cozuldu=False)
    
    # Sayfalama
    paginator = Paginator(hatalar, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Hata seviyeleri listesi
    hata_seviyeleri = SistemHatasi.HATA_SEVIYELERI
    
    context = {
        'page_obj': page_obj,
        'hata_seviyeleri': hata_seviyeleri,
        'secili_seviye': seviye,
        'secili_cozuldu': cozuldu,
    }
    return render(request, 'log/sistem_hatalari.html', context)


@login_required
def hata_detay(request, pk):
    """Sistem hatası detay view'ı"""
    hata = get_object_or_404(SistemHatasi, pk=pk)
    
    if request.method == 'POST':
        # Hata çözüm işlemi
        if request.POST.get('action') == 'coz':
            hata.cozuldu = True
            hata.cozum_notu = request.POST.get('cozum_notu', '')
            hata.save()
            messages.success(request, 'Hata çözüldü olarak işaretlendi.')
        elif request.POST.get('action') == 'ac':
            hata.cozuldu = False
            hata.cozum_notu = ''
            hata.save()
            messages.success(request, 'Hata tekrar açıldı.')
    
    context = {'hata': hata}
    return render(request, 'log/hata_detay.html', context)


@login_required
def login_loglari(request):
    """Login logları view'ı"""
    loglar = LoginLog.objects.all().order_by('-giris_tarihi')
    
    # Filtreler
    kullanici = request.GET.get('kullanici')
    if kullanici:
        loglar = loglar.filter(kullanici__username__icontains=kullanici)
    
    basarili = request.GET.get('basarili')
    if basarili == '1':
        loglar = loglar.filter(basarili=True)
    elif basarili == '0':
        loglar = loglar.filter(basarili=False)
    
    # Tarih aralığı
    baslangic = request.GET.get('baslangic')
    bitis = request.GET.get('bitis')
    if baslangic:
        loglar = loglar.filter(giris_tarihi__date__gte=baslangic)
    if bitis:
        loglar = loglar.filter(giris_tarihi__date__lte=bitis)
    
    # Sayfalama
    paginator = Paginator(loglar, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'secili_kullanici': kullanici,
        'secili_basarili': basarili,
        'baslangic': baslangic,
        'bitis': bitis,
    }
    return render(request, 'log/login_loglari.html', context)


@login_required
def log_temizle(request):
    """Log temizleme view'ı"""
    if request.method == 'POST':
        temizle_tipi = request.POST.get('tip')
        gun_sayisi = int(request.POST.get('gun_sayisi', 30))
        
        from datetime import date, timedelta
        cutoff_date = date.today() - timedelta(days=gun_sayisi)
        
        if temizle_tipi == 'aktivite':
            silinen = AktiviteLog.objects.filter(tarih__date__lt=cutoff_date).count()
            AktiviteLog.objects.filter(tarih__date__lt=cutoff_date).delete()
            messages.success(request, f'{silinen} aktivite log kaydı silindi.')
        
        elif temizle_tipi == 'hata':
            silinen = SistemHatasi.objects.filter(tarih__date__lt=cutoff_date, cozuldu=True).count()
            SistemHatasi.objects.filter(tarih__date__lt=cutoff_date, cozuldu=True).delete()
            messages.success(request, f'{silinen} çözülmüş hata kaydı silindi.')
        
        elif temizle_tipi == 'login':
            silinen = LoginLog.objects.filter(giris_tarihi__date__lt=cutoff_date).count()
            LoginLog.objects.filter(giris_tarihi__date__lt=cutoff_date).delete()
            messages.success(request, f'{silinen} login log kaydı silindi.')
        
        elif temizle_tipi == 'hepsi':
            aktivite_silinen = AktiviteLog.objects.filter(tarih__date__lt=cutoff_date).count()
            hata_silinen = SistemHatasi.objects.filter(tarih__date__lt=cutoff_date, cozuldu=True).count()
            login_silinen = LoginLog.objects.filter(giris_tarihi__date__lt=cutoff_date).count()
            
            AktiviteLog.objects.filter(tarih__date__lt=cutoff_date).delete()
            SistemHatasi.objects.filter(tarih__date__lt=cutoff_date, cozuldu=True).delete()
            LoginLog.objects.filter(giris_tarihi__date__lt=cutoff_date).delete()
            
            toplam = aktivite_silinen + hata_silinen + login_silinen
            messages.success(request, f'Toplam {toplam} log kaydı silindi.')
    
    # İstatistikler
    from datetime import date, timedelta
    
    bugun = date.today()
    bir_hafta_once = bugun - timedelta(days=7)
    bir_ay_once = bugun - timedelta(days=30)
    
    stats = {
        'toplam_aktivite': AktiviteLog.objects.count(),
        'haftalik_aktivite': AktiviteLog.objects.filter(tarih__date__gte=bir_hafta_once).count(),
        'aylik_aktivite': AktiviteLog.objects.filter(tarih__date__gte=bir_ay_once).count(),
        
        'toplam_hata': SistemHatasi.objects.count(),
        'cozulmemis_hata': SistemHatasi.objects.filter(cozuldu=False).count(),
        'haftalik_hata': SistemHatasi.objects.filter(tarih__date__gte=bir_hafta_once).count(),
        
        'toplam_login': LoginLog.objects.count(),
        'basarili_login': LoginLog.objects.filter(basarili=True).count(),
        'basarisiz_login': LoginLog.objects.filter(basarili=False).count(),
    }
    
    context = {'stats': stats}
    return render(request, 'log/log_temizle.html', context)
