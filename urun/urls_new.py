from django.urls import path
from . import views

app_name = 'urun'

urlpatterns = [
    # Ürün listesi ve ekleme
    path('', views.urun_listesi, name='liste'),
    path('ekle/', views.urun_ekle, name='ekle'),
    
    # Barkod sorgulama
    path('barkod/', views.barkod_sorgula, name='barkod'),
]
