from django.urls import path
from . import views

app_name = 'gider'

urlpatterns = [
    # Gider işlemleri
    path('', views.gider_listesi, name='liste'),
    path('ekle/', views.gider_ekle, name='ekle'),
    path('<int:pk>/duzenle/', views.gider_duzenle, name='duzenle'),
    path('<int:pk>/sil/', views.gider_sil, name='sil'),
    path('<int:pk>/detay/', views.gider_detay, name='detay'),
    
    # Raporlar
    path('rapor/', views.rapor, name='rapor'),
    
    # Kategori işlemleri
    path('kategoriler/', views.kategori_liste, name='kategori_liste'),
    path('kategoriler/ekle/', views.kategori_ekle, name='kategori_ekle'),
    path('kategori/<int:kategori_id>/duzenle/', views.kategori_duzenle, name='kategori_duzenle'),
]
