from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserSession, UserActivityLog, UserProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Özelleştirilmiş kullanıcı admin paneli"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at', 'last_login')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-created_at',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Ek Bilgiler', {
            'fields': ('role', 'phone_number', 'address', 'birth_date', 'created_by')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:  # Düzenleme modunda
            readonly_fields.extend(['username', 'created_by'])
        return readonly_fields


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Kullanıcı profil admin paneli"""
    
    list_display = ('user', 'department', 'hire_date', 'salary')
    list_filter = ('department', 'hire_date')
    search_fields = ('user__username', 'user__email', 'department')
    
    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('user',)
        }),
        ('Profil Bilgileri', {
            'fields': ('profile_picture', 'department', 'hire_date', 'salary')
        }),
        ('İletişim Bilgileri', {
            'fields': ('emergency_contact', 'emergency_phone')
        }),
        ('Notlar', {
            'fields': ('notes',)
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Kullanıcı oturum admin paneli"""
    
    list_display = ('user', 'ip_address', 'login_time', 'logout_time', 'is_active')
    list_filter = ('is_active', 'login_time', 'logout_time')
    search_fields = ('user__username', 'ip_address', 'user_agent')
    ordering = ('-login_time',)
    
    readonly_fields = ('session_key', 'user_agent', 'login_time')
    
    fieldsets = (
        ('Oturum Bilgileri', {
            'fields': ('user', 'session_key', 'ip_address', 'is_active')
        }),
        ('Zaman Bilgileri', {
            'fields': ('login_time', 'logout_time')
        }),
        ('Teknik Bilgiler', {
            'fields': ('user_agent',),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    """Kullanıcı aktivite log admin paneli"""
    
    list_display = ('user', 'action', 'content_type', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp', 'content_type')
    search_fields = ('user__username', 'description', 'ip_address')
    ordering = ('-timestamp',)
    
    readonly_fields = ('user', 'action', 'content_type', 'object_id', 'description', 'ip_address', 'timestamp')
    
    fieldsets = (
        ('Aktivite Bilgileri', {
            'fields': ('user', 'action', 'content_type', 'object_id')
        }),
        ('Detaylar', {
            'fields': ('description', 'ip_address', 'timestamp')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
