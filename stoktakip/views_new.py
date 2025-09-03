from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.http import HttpResponse
from datetime import date, datetime, timedelta


def dashboard_view(request):
    """Ana sayfa dashboard view'ı"""
    
    try:
        # Bugünün tarihi
        bugun = date.today()
        
        # Basit istatistikler
        context = {
            'bugun': bugun,
            'toplam_urun': 0,
            'toplam_musteri': 0,
            'bugunki_satis': 0,
            'bugunki_gider_toplam': 0,
        }
        
        # Güvenli şekilde model sayılarını al
        try:
            from urun.models import Urun
            context['toplam_urun'] = Urun.objects.filter(aktif=True).count()
        except Exception:
            pass
            
        try:
            from musteri.models import Musteri
            context['toplam_musteri'] = Musteri.objects.filter(aktif=True).count()
        except Exception:
            pass
            
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        # Hata durumunda basit bir mesaj döndür
        return render(request, 'dashboard.html', {
            'error': str(e),
            'bugun': date.today(),
            'toplam_urun': 0,
            'toplam_musteri': 0,
            'bugunki_satis': 0,
            'bugunki_gider_toplam': 0,
        })


def gunluk_rapor_view(request):
    """Günlük rapor view'ı"""
    
    # Tarih parametresi (varsayılan bugün)
    tarih_str = request.GET.get('tarih')
    if tarih_str:
        try:
            secili_tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date()
        except ValueError:
            secili_tarih = date.today()
    else:
        secili_tarih = date.today()
    
    context = {
        'secili_tarih': secili_tarih,
        'bugunki_satis': 0,
        'bugunki_gider': 0,
    }
    
    return render(request, 'gunluk_rapor.html', context)


def gunluk_rapor_pdf_view(request):
    """Günlük rapor PDF view'ı"""
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="gunluk_rapor.pdf"'
    
    try:
        from reportlab.pdfgen import canvas
        p = canvas.Canvas(response)
        p.drawString(100, 750, "Günlük Rapor")
        p.save()
    except ImportError:
        response.write(b"PDF library not available")
    
    return response
