from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import CustomUser, UserSession, UserActivityLog, UserProfile
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm, UserProfileForm,
    LoginForm, PasswordChangeForm, UserSearchForm
)


def is_admin(user):
    """Admin kontrolü"""
    return user.is_authenticated and user.role == 'ADMIN'


def is_admin_or_manager(user):
    """Admin veya manager kontrolü"""
    return user.is_authenticated and user.role in ['ADMIN', 'MANAGER']


def get_client_ip(request):
    """İstemci IP adresini al"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_user_activity(user, action, content_type='', object_id=None, description='', request=None):
    """Kullanıcı aktivitesini logla"""
    ip_address = get_client_ip(request) if request else '127.0.0.1'
    
    UserActivityLog.objects.create(
        user=user,
        action=action,
        content_type=content_type,
        object_id=object_id,
        description=description,
        ip_address=ip_address
    )


from django.views.decorators.csrf import csrf_protect
def custom_login_view(request):
    """Özelleştirilmiş giriş görünümü"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Oturum bilgilerini kaydet
            session_key = request.session.session_key
            if session_key:
                UserSession.objects.create(
                    user=user,
                    session_key=session_key,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            
            # Aktiviteyi logla
            log_user_activity(user, 'login', request=request)
            
            messages.success(request, f'Hoş geldiniz, {user.get_full_name() or user.username}!')
            
            # Hatırla beni özelliği
            if form.cleaned_data.get('remember_me'):
                request.session.set_expiry(30 * 24 * 60 * 60)  # 30 gün
            
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
    else:
        form = LoginForm()
    
    return render(request, 'kullanici/login.html', {'form': form})


@login_required
def custom_logout_view(request):
    """Özelleştirilmiş çıkış görünümü"""
    # Oturum bilgilerini güncelle
    session_key = request.session.session_key
    if session_key:
        try:
            user_session = UserSession.objects.get(
                user=request.user,
                session_key=session_key,
                is_active=True
            )
            user_session.logout_time = timezone.now()
            user_session.is_active = False
            user_session.save()
        except UserSession.DoesNotExist:
            pass
    
    # Aktiviteyi logla
    log_user_activity(request.user, 'logout', request=request)
    
    logout(request)
    messages.info(request, 'Başarıyla çıkış yaptınız.')
    return redirect('kullanici:login')


@login_required
@user_passes_test(is_admin)
def user_list_view(request):
    """Kullanıcı listesi görünümü"""
    form = UserSearchForm(request.GET)
    users = CustomUser.objects.all()
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        role = form.cleaned_data.get('role')
        is_active = form.cleaned_data.get('is_active')
        
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        if role:
            users = users.filter(role=role)
        
        if is_active:
            users = users.filter(is_active=is_active == 'true')
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'kullanici/user_list.html', {
        'form': form,
        'page_obj': page_obj,
        'users': page_obj
    })


@login_required
@user_passes_test(is_admin)
def user_create_view(request):
    """Kullanıcı oluşturma görünümü"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.created_by = request.user
            user.save()
            
            # Aktiviteyi logla
            log_user_activity(
                request.user, 'create', 'CustomUser', user.id,
                f'Yeni kullanıcı oluşturuldu: {user.username}', request
            )
            
            messages.success(request, f'Kullanıcı "{user.username}" başarıyla oluşturuldu.')
            return redirect('kullanici:user_detail', user_id=user.id)
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'kullanici/user_form.html', {
        'form': form,
        'title': 'Yeni Kullanıcı Oluştur'
    })


@login_required
@user_passes_test(is_admin_or_manager)
def user_detail_view(request, user_id):
    """Kullanıcı detay görünümü"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Manager sadece kendi oluşturdukları kullanıcıları görebilir
    if request.user.role == 'manager' and user.created_by != request.user:
        return HttpResponseForbidden("Bu kullanıcıyı görme yetkiniz yok.")
    
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    # Son aktiviteler
    recent_activities = UserActivityLog.objects.filter(user=user)[:10]
    
    # Aktif oturumlar
    active_sessions = UserSession.objects.filter(user=user, is_active=True)
    
    return render(request, 'kullanici/user_detail.html', {
        'user_obj': user,
        'profile': profile,
        'recent_activities': recent_activities,
        'active_sessions': active_sessions
    })


@login_required
@user_passes_test(is_admin)
def user_edit_view(request, user_id):
    """Kullanıcı düzenleme görünümü"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            
            # Aktiviteyi logla
            log_user_activity(
                request.user, 'update', 'CustomUser', user.id,
                f'Kullanıcı güncellendi: {user.username}', request
            )
            
            messages.success(request, f'Kullanıcı "{user.username}" başarıyla güncellendi.')
            return redirect('kullanici:user_detail', user_id=user.id)
    else:
        form = CustomUserChangeForm(instance=user)
    
    return render(request, 'kullanici/user_form.html', {
        'form': form,
        'user_obj': user,
        'title': f'Kullanıcı Düzenle: {user.username}'
    })


@login_required
def user_profile_view(request):
    """Kullanıcı profil görünümü"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        user_form = CustomUserChangeForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            # Aktiviteyi logla
            log_user_activity(
                request.user, 'update', 'UserProfile', profile.id,
                'Profil güncellendi', request
            )
            
            messages.success(request, 'Profiliniz başarıyla güncellendi.')
            return redirect('kullanici:profile')
    else:
        user_form = CustomUserChangeForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    return render(request, 'kullanici/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile
    })


@login_required
def password_change_view(request):
    """Şifre değiştirme görünümü"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            
            # Aktiviteyi logla
            log_user_activity(
                request.user, 'update', 'CustomUser', request.user.id,
                'Şifre değiştirildi', request
            )
            
            messages.success(request, 'Şifreniz başarıyla değiştirildi.')
            return redirect('kullanici:profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'kullanici/password_change.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def user_delete_view(request, user_id):
    """Kullanıcı silme görünümü"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user == request.user:
        messages.error(request, 'Kendi hesabınızı silemezsiniz.')
        return redirect('kullanici:user_detail', user_id=user.id)
    
    if request.method == 'POST':
        username = user.username
        
        # Aktiviteyi logla
        log_user_activity(
            request.user, 'delete', 'CustomUser', user.id,
            f'Kullanıcı silindi: {username}', request
        )
        
        user.delete()
        messages.success(request, f'Kullanıcı "{username}" başarıyla silindi.')
        return redirect('kullanici:user_list')
    
    return render(request, 'kullanici/user_confirm_delete.html', {'user_obj': user})


@login_required
@user_passes_test(is_admin_or_manager)
def user_activity_log_view(request, user_id=None):
    """Kullanıcı aktivite log görünümü"""
    if user_id:
        user = get_object_or_404(CustomUser, id=user_id)
        activities = UserActivityLog.objects.filter(user=user)
        title = f'{user.username} Aktivite Logları'
    else:
        activities = UserActivityLog.objects.all()
        title = 'Tüm Kullanıcı Aktiviteleri'
        user = None
    
    # Filtreleme
    action = request.GET.get('action')
    if action:
        activities = activities.filter(action=action)
    
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'kullanici/activity_log.html', {
        'page_obj': page_obj,
        'activities': page_obj,
        'user_obj': user,
        'title': title,
        'action_choices': UserActivityLog.ACTION_CHOICES
    })


@login_required
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    """Kullanıcı durumunu değiştir (aktif/pasif)"""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'})
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user == request.user:
        return JsonResponse({'success': False, 'error': 'Kendi durumunuzu değiştiremezsiniz'})
    
    user.is_active = not user.is_active
    user.save()
    
    # Aktiviteyi logla
    status = 'aktif' if user.is_active else 'pasif'
    log_user_activity(
        request.user, 'update', 'CustomUser', user.id,
        f'Kullanıcı durumu değiştirildi: {status}', request
    )
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': f'Kullanıcı {status} duruma getirildi.'
    })


@login_required
@user_passes_test(is_admin)
def user_sessions_view(request):
    """Aktif kullanıcı oturumları görünümü"""
    active_sessions = UserSession.objects.filter(is_active=True).select_related('user')
    
    paginator = Paginator(active_sessions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'kullanici/user_sessions.html', {
        'page_obj': page_obj,
        'sessions': page_obj
    })


@login_required
@require_http_methods(["POST"])
def terminate_session(request, session_id):
    """Kullanıcı oturumunu sonlandır"""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'})
    
    session = get_object_or_404(UserSession, id=session_id)
    session.logout_time = timezone.now()
    session.is_active = False
    session.save()
    
    # Aktiviteyi logla
    log_user_activity(
        request.user, 'update', 'UserSession', session.id,
        f'Oturum sonlandırıldı: {session.user.username}', request
    )
    
    return JsonResponse({
        'success': True,
        'message': f'{session.user.username} kullanıcısının oturumu sonlandırıldı.'
    })


@login_required
@user_passes_test(is_admin)
def user_activity_logs_view(request):
    """Tüm kullanıcı aktivite logları görünümü"""
    activities = UserActivityLog.objects.all().select_related('user').order_by('-timestamp')
    
    # Arama filtresi
    search_query = request.GET.get('search', '')
    if search_query:
        activities = activities.filter(
            Q(user__username__icontains=search_query) |
            Q(action__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(ip_address__icontains=search_query)
        )
    
    # Tarih filtresi
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        activities = activities.filter(timestamp__date__gte=date_from)
    if date_to:
        activities = activities.filter(timestamp__date__lte=date_to)
    
    # Kullanıcı filtresi
    user_filter = request.GET.get('user')
    if user_filter:
        activities = activities.filter(user_id=user_filter)
    
    # Sayfalama
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Kullanıcı listesi filtreleme için
    users = CustomUser.objects.all().order_by('username')
    
    return render(request, 'kullanici/user_activity_logs.html', {
        'page_obj': page_obj,
        'activities': page_obj,
        'users': users,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'user_filter': user_filter,
    })
