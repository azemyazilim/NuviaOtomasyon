from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from kullanici.models import UserSession


class UserSessionMiddleware(MiddlewareMixin):
    """Kullanıcı oturum yönetimi middleware'i"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            session_key = request.session.session_key
            
            if session_key:
                try:
                    user_session = UserSession.objects.get(
                        user=request.user,
                        session_key=session_key,
                        is_active=True
                    )
                    # Oturum hala aktif
                except UserSession.DoesNotExist:
                    # Oturum bulunamadı, kullanıcıyı çıkart
                    logout(request)
                    return redirect(reverse('kullanici:login'))


class PermissionCheckMiddleware(MiddlewareMixin):
    """Yetki kontrolü middleware'i"""
    
    def process_request(self, request):
        # Login gerektirmeyen sayfalar
        allowed_paths = [
            '/kullanici/login/',
            '/admin/',
            '/favicon.ico',
        ]
        
        # Eğer kullanıcı login olmamışsa ve izin verilen sayfalarda değilse
        if not request.user.is_authenticated:
            # İzin verilen sayfalarda değilse login'e yönlendir
            if not any(request.path.startswith(path) for path in allowed_paths):
                # AJAX istekleri için farklı response
                is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                if is_ajax or request.content_type == 'application/json':
                    from django.http import JsonResponse
                    return JsonResponse({'error': 'Authentication required'}, status=401)
                return redirect(reverse('kullanici:login'))
            return None
        
        # Admin paneli için özel kontrol
        if request.path.startswith('/admin/'):
            if not request.user.is_superuser and request.user.role != 'admin':
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Admin paneline erişim yetkiniz yok.")
        
        return None
