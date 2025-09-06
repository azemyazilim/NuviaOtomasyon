from django.urls import path
from . import views

app_name = 'urun'

urlpatterns = [
    # Ürün listesi ve ekleme
    path('', views.urun_listesi, name='liste'),
    path('ekle/', views.urun_ekle, name='ekle'),
    path('<int:urun_id>/', views.urun_detay, name='detay'),
    path('<int:urun_id>/duzenle/', views.urun_duzenle, name='duzenle'),
    path('<int:urun_id>/sil/', views.urun_sil, name='sil'),
    
    # Varyasyon yönetimi
    path('<int:urun_id>/varyasyon/', views.varyasyon_yonet, name='varyasyon_yonet'),
    path('<int:urun_id>/varyasyon/olustur/', views.varyasyon_olustur, name='varyasyon_olustur'),
    path('varyant/<int:varyant_id>/duzenle/', views.varyant_duzenle, name='varyant_duzenle'),
    path('varyant/<int:varyant_id>/sil/', views.varyant_sil, name='varyant_sil'),
    path('<int:urun_id>/varyant/toplu-stok/', views.varyant_toplu_stok_guncelle, name='varyant_toplu_stok'),
    
    # Barkod sorgulama
    path('barkod/', views.barkod_sorgula, name='barkod'),
    
    # Kategori yönetimi
    path('kategori/', views.kategori_yonetimi, name='kategori'),
    path('kategori/ust-ekle/', views.ust_kategori_ekle, name='ust_kategori_ekle'),
    path('kategori/ust-sil/<int:kategori_id>/', views.ust_kategori_sil, name='ust_kategori_sil'),
    
    # Marka yönetimi
    path('marka/', views.marka_listesi, name='marka_listesi'),
    
    # Stok raporları
    path('en-cok-satanlar/', views.en_cok_satanlar, name='en_cok_satanlar'),
    path('kar-zarar/', views.kar_zarar_raporu, name='kar_zarar_raporu'),
]
