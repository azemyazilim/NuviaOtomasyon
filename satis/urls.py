from django.urls import path
from . import views

app_name = 'satis'

urlpatterns = [
    # Satış ekranı
    path('', views.satis_ekrani, name='ekrani'),
    path('ekrani/', views.satis_ekrani, name='ekrani'),
    
    # Satış listesi ve detay
    path('liste/', views.satis_listesi, name='liste'),
    path('<int:pk>/', views.satis_detay, name='detay'),
    path('<int:pk>/yazdır/', views.satis_yazdir, name='yazdir'),
    
    # Satış işlemleri
    path('tamamla/', views.satis_tamamla, name='satis_tamamla'),
    path('<int:pk>/iptal/', views.satis_iptal, name='satis_iptal'),
    
    # İade işlemleri
    path('iade/', views.iade_ana_sayfa, name='iade_ana_sayfa'),
    path('<int:pk>/iade/', views.satis_iade, name='satis_iade'),
    
    # İade işlemleri
    path('iade-fisi/<int:hediye_ceki_id>/', views.iade_fisi, name='iade_fisi'),
    path('iade-fisi/<int:hediye_ceki_id>/pdf/', views.iade_fisi_pdf, name='iade_fisi_pdf'),
    
    # Tahsilat işlemleri
    path('tahsilat/', views.tahsilat_listesi, name='tahsilat_listesi'),
    path('tahsilat/rapor/', views.tahsilat_rapor, name='tahsilat_rapor'),
    
    # Barkod sorgulama
    path('barkod-sorgula/', views.barkod_sorgula, name='barkod_sorgula'),
    
    # AJAX endpoints
    path('ajax/urun-ara/', views.urun_ara, name='urun_ara'),
    path('ajax/sepete-ekle/', views.sepete_ekle, name='sepete_ekle'),
    path('ajax/sepetten-cikar/', views.sepetten_cikar, name='sepetten_cikar'),
    path('ajax/sepet-temizle/', views.sepet_temizle, name='sepet_temizle'),
    path('ajax/musteri-ara/', views.musteri_ara, name='musteri_ara'),
    path('hediye-ceki-sorgula/', views.hediye_ceki_sorgula, name='hediye_ceki_sorgula'),
    path('ajax/yeni-siparis-no/', views.yeni_siparis_no, name='yeni_siparis_no'),
]
