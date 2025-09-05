from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Kasa, KasaHareket, KasaVirman, KasaCikis, KasaGiris
from decimal import Decimal
import json


@login_required
def kasa_dashboard(request):
    """Kasa ana sayfası"""
    kasalar = Kasa.objects.filter(aktif=True).order_by('tip', 'ad')
    
    # Her kasa için güncel bakiye ve bugünkü hareketleri hesapla
    kasa_bilgileri = []
    for kasa in kasalar:
        bugun = timezone.now().date()
        bugunki_giris = kasa.hareketler.filter(
            tip='giris', 
            tarih__date=bugun
        ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0')
        
        bugunki_cikis = kasa.hareketler.filter(
            tip='cikis', 
            tarih__date=bugun
        ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0')
        
        kasa_bilgileri.append({
            'kasa': kasa,
            'bakiye': kasa.guncel_bakiye,
            'bugunki_giris': bugunki_giris,
            'bugunki_cikis': bugunki_cikis,
            'bugunki_net': bugunki_giris - bugunki_cikis
        })
    
    # Son 10 hareket
    son_hareketler = KasaHareket.objects.select_related('kasa').order_by('-tarih')[:10]
    
    # Toplam bakiyeler
    toplam_nakit = sum([k['bakiye'] for k in kasa_bilgileri if k['kasa'].tip == 'nakit'])
    toplam_pos = sum([k['bakiye'] for k in kasa_bilgileri if k['kasa'].tip == 'pos'])
    toplam_kart = sum([k['bakiye'] for k in kasa_bilgileri if k['kasa'].tip == 'kart'])
    toplam_banka = sum([k['bakiye'] for k in kasa_bilgileri if k['kasa'].tip == 'banka'])
    
    context = {
        'kasa_bilgileri': kasa_bilgileri,
        'son_hareketler': son_hareketler,
        'toplam_nakit': toplam_nakit,
        'toplam_pos': toplam_pos,
        'toplam_kart': toplam_kart,
        'toplam_banka': toplam_banka,
        'genel_toplam': toplam_nakit + toplam_pos + toplam_kart + toplam_banka,
    }
    
    return render(request, 'kasa/dashboard.html', context)


@login_required
def kasa_detay(request, kasa_id):
    """Kasa detay sayfası"""
    kasa = get_object_or_404(Kasa, id=kasa_id, aktif=True)
    
    # Tarih filtreleme
    tarih_baslangic = request.GET.get('tarih_baslangic')
    tarih_bitis = request.GET.get('tarih_bitis')
    
    hareketler = kasa.hareketler.all()
    
    if tarih_baslangic:
        try:
            baslangic = datetime.strptime(tarih_baslangic, '%Y-%m-%d').date()
            hareketler = hareketler.filter(tarih__date__gte=baslangic)
        except ValueError:
            pass
    
    if tarih_bitis:
        try:
            bitis = datetime.strptime(tarih_bitis, '%Y-%m-%d').date()
            hareketler = hareketler.filter(tarih__date__lte=bitis)
        except ValueError:
            pass
    
    hareketler = hareketler.order_by('-tarih')
    
    # İstatistikler
    toplam_giris = hareketler.filter(tip='giris').aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0')
    toplam_cikis = hareketler.filter(tip='cikis').aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0')
    
    context = {
        'kasa': kasa,
        'hareketler': hareketler,
        'toplam_giris': toplam_giris,
        'toplam_cikis': toplam_cikis,
        'net_hareket': toplam_giris - toplam_cikis,
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
    }
    
    return render(request, 'kasa/detay.html', context)


@login_required
def virman_yap(request):
    """Kasalar arası virman"""
    if request.method == 'POST':
        try:
            kaynak_kasa_id = request.POST.get('kaynak_kasa')
            hedef_kasa_id = request.POST.get('hedef_kasa')
            tutar = Decimal(request.POST.get('tutar', '0'))
            aciklama = request.POST.get('aciklama', '')
            
            if kaynak_kasa_id == hedef_kasa_id:
                messages.error(request, 'Kaynak ve hedef kasa aynı olamaz!')
                return redirect('kasa:virman')
            
            kaynak_kasa = Kasa.objects.get(id=kaynak_kasa_id, aktif=True)
            hedef_kasa = Kasa.objects.get(id=hedef_kasa_id, aktif=True)
            
            if kaynak_kasa.guncel_bakiye < tutar:
                messages.error(request, f'{kaynak_kasa.ad} kasasında yeterli bakiye yok!')
                return redirect('kasa:virman')
            
            # Virman oluştur
            virman = KasaVirman.objects.create(
                kaynak_kasa=kaynak_kasa,
                hedef_kasa=hedef_kasa,
                tutar=tutar,
                aciklama=aciklama,
                kullanici=request.user
            )
            
            messages.success(request, f'{tutar}₺ {kaynak_kasa.ad} kasasından {hedef_kasa.ad} kasasına aktarıldı.')
            return redirect('kasa:dashboard')
            
        except Exception as e:
            messages.error(request, f'Virman sırasında hata: {str(e)}')
    
    kasalar = Kasa.objects.filter(aktif=True).order_by('tip', 'ad')
    return render(request, 'kasa/virman.html', {'kasalar': kasalar})


@login_required
def para_cikisi(request):
    """Kasadan para çıkışı"""
    if request.method == 'POST':
        try:
            kasa_id = request.POST.get('kasa')
            tutar = Decimal(request.POST.get('tutar', '0'))
            sebep = request.POST.get('sebep')
            aciklama = request.POST.get('aciklama', '')
            
            kasa = Kasa.objects.get(id=kasa_id, aktif=True)
            
            if kasa.guncel_bakiye < tutar:
                messages.error(request, f'{kasa.ad} kasasında yeterli bakiye yok!')
                return redirect('kasa:para_cikisi')
            
            # Para çıkışı oluştur
            cikis = KasaCikis.objects.create(
                kasa=kasa,
                tutar=tutar,
                sebep=sebep,
                aciklama=aciklama,
                kullanici=request.user
            )
            
            messages.success(request, f'{tutar}₺ {kasa.ad} kasasından çıkarıldı.')
            return redirect('kasa:dashboard')
            
        except Exception as e:
            messages.error(request, f'Para çıkışı sırasında hata: {str(e)}')
    
    kasalar = Kasa.objects.filter(aktif=True).order_by('tip', 'ad')
    return render(request, 'kasa/para_cikisi.html', {'kasalar': kasalar})


@login_required
def para_girisi(request):
    """Kasaya para girişi"""
    if request.method == 'POST':
        try:
            kasa_id = request.POST.get('kasa')
            tutar = Decimal(request.POST.get('tutar', '0'))
            sebep = request.POST.get('sebep')
            aciklama = request.POST.get('aciklama', '')
            
            kasa = Kasa.objects.get(id=kasa_id, aktif=True)
            
            # Para girişi oluştur
            giris = KasaGiris.objects.create(
                kasa=kasa,
                tutar=tutar,
                sebep=sebep,
                aciklama=aciklama,
                kullanici=request.user
            )
            
            messages.success(request, f'{tutar}₺ {kasa.ad} kasasına eklendi.')
            return redirect('kasa:dashboard')
            
        except Exception as e:
            messages.error(request, f'Para girişi sırasında hata: {str(e)}')
    
    kasalar = Kasa.objects.filter(aktif=True).order_by('tip', 'ad')
    return render(request, 'kasa/para_girisi.html', {'kasalar': kasalar})


@login_required
def kasa_bakiye_ajax(request):
    """AJAX ile kasa bakiyesi sorgulama"""
    kasa_id = request.GET.get('kasa_id')
    if kasa_id:
        try:
            kasa = Kasa.objects.get(id=kasa_id, aktif=True)
            return JsonResponse({
                'success': True,
                'bakiye': float(kasa.guncel_bakiye),
                'bakiye_str': f'{kasa.guncel_bakiye:,.2f}₺'
            })
        except Kasa.DoesNotExist:
            pass
    
    return JsonResponse({'success': False})
