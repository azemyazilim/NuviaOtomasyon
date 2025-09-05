from django.urls import path
from . import views

app_name = 'kasa'

urlpatterns = [
    path('', views.kasa_dashboard, name='dashboard'),
    path('detay/<int:kasa_id>/', views.kasa_detay, name='detay'),
    path('virman/', views.virman_yap, name='virman'),
    path('para-cikisi/', views.para_cikisi, name='para_cikisi'),
    path('para-girisi/', views.para_girisi, name='para_girisi'),
    path('bakiye-ajax/', views.kasa_bakiye_ajax, name='bakiye_ajax'),
]
