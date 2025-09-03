from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """
    Belirli rollere sahip kullanıcıları kontrol eden decorator
    
    Kullanım:
    @role_required('admin', 'manager')
    def my_view(request):
        pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Bu sayfaya erişim yetkiniz bulunmuyor.')
                return HttpResponseForbidden("Bu sayfaya erişim yetkiniz bulunmuyor.")
        return _wrapped_view
    return decorator


def permission_required(permission):
    """
    Belirli izinlere sahip kullanıcıları kontrol eden decorator
    
    Kullanım:
    @permission_required('add_urun')
    def my_view(request):
        pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.has_role_permission(permission):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Bu işlem için yetkiniz bulunmuyor.')
                return HttpResponseForbidden("Bu işlem için yetkiniz bulunmuyor.")
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """
    Sadece admin kullanıcıları kabul eden decorator
    
    Kullanım:
    @admin_required
    def my_view(request):
        pass
    """
    return role_required('admin')(view_func)


def manager_or_admin_required(view_func):
    """
    Manager veya admin kullanıcıları kabul eden decorator
    
    Kullanım:
    @manager_or_admin_required
    def my_view(request):
        pass
    """
    return role_required('admin', 'manager')(view_func)


def cashier_or_above_required(view_func):
    """
    Kasiyer veya üstü yetkiye sahip kullanıcıları kabul eden decorator
    
    Kullanım:
    @cashier_or_above_required
    def my_view(request):
        pass
    """
    return role_required('admin', 'manager', 'cashier')(view_func)


def can_view_user_details(user, target_user):
    """
    Kullanıcının başka bir kullanıcının detaylarını görüp göremeyeceğini kontrol eder
    """
    if user.role == 'admin':
        return True
    elif user.role == 'manager':
        # Manager sadece kendi oluşturdukları kullanıcıları görebilir
        return target_user.created_by == user
    else:
        # Sadece kendi profilini görebilir
        return user == target_user


def can_edit_user(user, target_user):
    """
    Kullanıcının başka bir kullanıcıyı düzenleyip düzenleyemeyeceğini kontrol eder
    """
    if user.role == 'admin':
        return True
    else:
        # Sadece kendi profilini düzenleyebilir
        return user == target_user


def can_delete_user(user, target_user):
    """
    Kullanıcının başka bir kullanıcıyı silip silemeyeceğini kontrol eder
    """
    if user.role == 'admin' and user != target_user:
        return True
    return False


class PermissionMixin:
    """
    View'lar için permission kontrolü sağlayan mixin
    """
    required_permissions = []
    required_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('kullanici:login')
        
        # Rol kontrolü
        if self.required_roles and request.user.role not in self.required_roles:
            messages.error(request, 'Bu sayfaya erişim yetkiniz bulunmuyor.')
            return HttpResponseForbidden("Bu sayfaya erişim yetkiniz bulunmuyor.")
        
        # İzin kontrolü
        for permission in self.required_permissions:
            if not request.user.has_role_permission(permission):
                messages.error(request, 'Bu işlem için yetkiniz bulunmuyor.')
                return HttpResponseForbidden("Bu işlem için yetkiniz bulunmuyor.")
        
        return super().dispatch(request, *args, **kwargs)
