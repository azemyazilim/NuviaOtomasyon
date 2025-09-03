from django.urls import path
from . import views

app_name = 'kullanici'

urlpatterns = [
    # Giriş/Çıkış
    path('login/', views.custom_login_view, name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    
    # Kullanıcı Yönetimi
    path('', views.user_list_view, name='user_list'),
    path('create/', views.user_create_view, name='user_create'),
    path('<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('<int:user_id>/delete/', views.user_delete_view, name='user_delete'),
    path('<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
    # Profil Yönetimi
    path('profile/', views.user_profile_view, name='profile'),
    path('password-change/', views.password_change_view, name='password_change'),
    
    # Aktivite Logları
    path('activities/', views.user_activity_log_view, name='activity_log'),
    path('user-activities/', views.user_activity_logs_view, name='user_activity_logs'),
    path('<int:user_id>/activities/', views.user_activity_log_view, name='user_activity_log'),
    
    # Oturum Yönetimi
    path('sessions/', views.user_sessions_view, name='user_sessions'),
    path('sessions/<int:session_id>/terminate/', views.terminate_session, name='terminate_session'),
]
