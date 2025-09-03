from django.urls import path
from . import views

app_name = 'hediye'

urlpatterns = [
    # Hediye çeki listesi ve yönetimi
    path('', views.hediye_ceki_listesi, name='liste'),
    path('<int:pk>/', views.hediye_ceki_detay, name='detay'),
    path('<int:pk>/iptal/', views.hediye_ceki_iptal, name='iptal'),
    
    # AJAX endpoints
    path('ajax/sorgula/', views.hediye_ceki_ajax_sorgula, name='ajax_sorgula'),
]
