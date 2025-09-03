from django.urls import path
from . import views

app_name = 'urun'

urlpatterns = [
    # Ürün listesi ve detay
    path('', views.urun_listesi, name='liste'),
    path('ekle/', views.urun_ekle, name='ekle'),
    path('<int:pk>/duzenle/', views.urun_duzenle, name='duzenle'),
    path('<int:pk>/sil/', views.urun_sil, name='sil'),
    path('<int:pk>/', views.urun_detay, name='detay'),
    
    # Kategori yönetimi
    path('kategori/', views.kategori_yonetimi, name='kategori'),
    path('kategori/ust-ekle/', views.ust_kategori_ekle, name='ust_kategori_ekle'),
    path('kategori/ust-sil/<int:pk>/', views.ust_kategori_sil, name='ust_kategori_sil'),
    
    # Stok yönetimi
    path('stok/', views.stok_durumu, name='stok_durumu'),
    path('stok-guncelle/', views.stok_guncelle, name='stok_guncelle'),
    
    # Raporlar
    path('en-cok-satanlar/', views.en_cok_satanlar, name='en_cok_satanlar'),
    path('kar-zarar-raporu/', views.kar_zarar_raporu, name='kar_zarar_raporu'),
    
    # Barkod sorgulama
    path('barkod/', views.barkod_sorgula, name='barkod'),
    
    # Marka yönetimi
    path('marka/', views.marka_listesi, name='marka_listesi'),
    path('marka/ekle/', views.marka_ekle, name='marka_ekle'),
    path('marka/<int:pk>/duzenle/', views.marka_duzenle, name='marka_duzenle'),
    path('marka/<int:pk>/sil/', views.marka_sil, name='marka_sil'),
    
    # Varyasyon yönetimi
    path('varyasyon/', views.varyasyon_yonetimi, name='varyasyon_yonetimi'),
    path('varyasyon/ekle/', views.varyasyon_ekle, name='varyasyon_ekle'),
    
    # AJAX endpoints
    path('ajax/barkod-kontrol/', views.barkod_kontrol, name='barkod_kontrol'),
]
