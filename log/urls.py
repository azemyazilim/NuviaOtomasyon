from django.urls import path
from . import views

app_name = 'log'

urlpatterns = [
    # Log görüntüleme
    path('aktivite/', views.aktivite_loglari, name='aktivite_loglari'),
    path('sistem-hatalari/', views.sistem_hatalari, name='sistem_hatalari'),
    path('login-loglari/', views.login_loglari, name='login_loglari'),
    
    # Log detayları
    path('aktivite/<int:pk>/', views.aktivite_detay, name='aktivite_detay'),
    path('hata/<int:pk>/', views.hata_detay, name='hata_detay'),
    
    # Log temizleme
    path('temizle/', views.log_temizle, name='log_temizle'),
]
