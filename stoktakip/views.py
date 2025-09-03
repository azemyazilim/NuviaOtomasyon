from django.shortcuts import render
from django.http import HttpResponse
from datetime import date

def dashboard_view(request):
    context = {'bugun': date.today(), 'toplam_urun': 0, 'toplam_musteri': 0, 'bugunki_satis': 0, 'bugunki_gider_toplam': 0}
    return render(request, 'dashboard.html', context)

def gunluk_rapor_view(request):
    return render(request, 'gunluk_rapor.html', {})

def gunluk_rapor_pdf_view(request):
    return HttpResponse('PDF not available')
