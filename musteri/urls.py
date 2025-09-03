from django.urls import path
from . import views
from . import tahsilat_views

app_name = 'musteri'

urlpatterns = [
    # Müşteri listesi ve detay
    path('', views.musteri_listesi, name='liste'),
    path('ekle/', views.musteri_ekle, name='ekle'),
    path('<int:pk>/duzenle/', views.musteri_duzenle, name='duzenle'),
    path('<int:pk>/sil/', views.musteri_sil, name='sil'),
    path('<int:pk>/', views.musteri_detay, name='detay'),
    
    # Müşteri grupları
    path('grup/', views.musteri_grup_listesi, name='musteri_grup_listesi'),
    path('grup/ekle/', views.musteri_grup_ekle, name='musteri_grup_ekle'),
    path('grup/<int:pk>/duzenle/', views.musteri_grup_duzenle, name='musteri_grup_duzenle'),
    
    # Borç-Alacak Takip
    path('borc-alacak/', tahsilat_views.borc_alacak_listesi, name='borc_alacak_listesi'),
    path('borc-detay/<int:musteri_id>/', tahsilat_views.musteri_borc_detay, name='musteri_borc_detay'),
    
    # Tahsilat İşlemleri
    path('tahsilat/', tahsilat_views.tahsilat_listesi, name='tahsilat_listesi'),
    path('tahsilat/yeni/', tahsilat_views.tahsilat_formu, name='tahsilat_formu'),
    path('tahsilat/yeni/<int:musteri_id>/', tahsilat_views.tahsilat_formu, name='tahsilat_formu_musteri'),
    path('tahsilat/<int:tahsilat_id>/', tahsilat_views.tahsilat_detay, name='tahsilat_detay'),
    path('tahsilat/<int:tahsilat_id>/iptal/', tahsilat_views.tahsilat_iptal, name='tahsilat_iptal'),
    
    # AJAX endpoints
    path('ajax/telefon-kontrol/', views.telefon_kontrol, name='telefon_kontrol'),
    path('ajax/musteri-ara/', views.musteri_ara, name='musteri_ara'),
    path('ajax/detay/<int:musteri_id>/', views.musteri_ajax_detay, name='ajax_detay'),
    path('ajax/tahsilat-musteri-ara/', tahsilat_views.musteri_arama_ajax, name='tahsilat_musteri_ara'),
]
