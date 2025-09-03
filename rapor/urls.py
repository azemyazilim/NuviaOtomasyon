from django.urls import path
from . import views

app_name = 'rapor'

urlpatterns = [
    # Raporlar
    path('gunluk-satis/', views.gunluk_satis, name='gunluk_satis'),
    path('stok-raporu/', views.stok_raporu, name='stok_raporu'),
    path('cok-satan-urunler/', views.cok_satan_urunler, name='cok_satan_urunler'),
    path('kar-zarar/', views.kar_zarar, name='kar_zarar'),
    path('musteri-raporu/', views.musteri_raporu, name='musteri_raporu'),
    
    # Rapor export
    path('export/gunluk-satis-excel/', views.gunluk_satis_excel, name='gunluk_satis_excel'),
    path('export/gunluk-satis-pdf/', views.gunluk_satis_pdf, name='gunluk_satis_pdf'),
    path('export/stok-excel/', views.stok_excel, name='stok_excel'),
    path('export/stok-pdf/', views.stok_pdf, name='stok_pdf'),
    path('export/kar-zarar-excel/', views.kar_zarar_excel, name='kar_zarar_excel'),
    path('export/kar-zarar-pdf/', views.kar_zarar_pdf, name='kar_zarar_pdf'),
]
