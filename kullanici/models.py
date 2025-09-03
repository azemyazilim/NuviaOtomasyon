from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    """Özelleştirilmiş kullanıcı modeli"""
    
    ROLE_CHOICES = [
        ('admin', 'Sistem Yöneticisi'),
        ('manager', 'Mağaza Müdürü'),
        ('cashier', 'Kasiyer'),
        ('stock_clerk', 'Depo Sorumlusu'),
        ('viewer', 'Görüntüleme Yetkisi'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer',
        verbose_name='Rol'
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Telefon numarası '+999999999' formatında olmalıdır. 15 haneden fazla olamaz."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name='Telefon Numarası'
    )
    
    address = models.TextField(
        blank=True,
        verbose_name='Adres'
    )
    
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Doğum Tarihi'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Aktif'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturulma Tarihi'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Güncellenme Tarihi'
    )
    
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        verbose_name='Oluşturan'
    )
    
    class Meta:
        verbose_name = 'Kullanıcı'
        verbose_name_plural = 'Kullanıcılar'
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def get_role_permissions(self):
        """Rol bazlı izinleri döndürür"""
        role_permissions = {
            'admin': [
                'add_user', 'change_user', 'delete_user', 'view_user',
                'add_urun', 'change_urun', 'delete_urun', 'view_urun',
                'add_satis', 'change_satis', 'delete_satis', 'view_satis',
                'add_musteri', 'change_musteri', 'delete_musteri', 'view_musteri',
                'add_gider', 'change_gider', 'delete_gider', 'view_gider',
                'view_rapor', 'view_log',
            ],
            'manager': [
                'view_user',
                'add_urun', 'change_urun', 'view_urun',
                'add_satis', 'change_satis', 'view_satis',
                'add_musteri', 'change_musteri', 'view_musteri',
                'add_gider', 'change_gider', 'view_gider',
                'view_rapor', 'view_log',
            ],
            'cashier': [
                'add_satis', 'view_satis',
                'view_urun',
                'add_musteri', 'change_musteri', 'view_musteri',
            ],
            'stock_clerk': [
                'add_urun', 'change_urun', 'view_urun',
                'view_satis',
            ],
            'viewer': [
                'view_urun', 'view_satis', 'view_musteri', 'view_rapor',
            ],
        }
        return role_permissions.get(self.role, [])
    
    def has_role_permission(self, permission):
        """Kullanıcının belirli bir izni var mı kontrol eder"""
        return permission in self.get_role_permissions()


class UserSession(models.Model):
    """Kullanıcı oturum takibi"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Kullanıcı'
    )
    session_key = models.CharField(
        max_length=40,
        verbose_name='Oturum Anahtarı'
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='IP Adresi'
    )
    user_agent = models.TextField(
        verbose_name='Tarayıcı Bilgisi'
    )
    login_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Giriş Zamanı'
    )
    logout_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Çıkış Zamanı'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Aktif'
    )
    
    class Meta:
        verbose_name = 'Kullanıcı Oturumu'
        verbose_name_plural = 'Kullanıcı Oturumları'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"


class UserActivityLog(models.Model):
    """Kullanıcı aktivite logu"""
    
    ACTION_CHOICES = [
        ('login', 'Giriş'),
        ('logout', 'Çıkış'),
        ('create', 'Oluşturma'),
        ('update', 'Güncelleme'),
        ('delete', 'Silme'),
        ('view', 'Görüntüleme'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Kullanıcı'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='Eylem'
    )
    content_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='İçerik Türü'
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Nesne ID'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Açıklama'
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='IP Adresi'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Zaman'
    )
    
    class Meta:
        verbose_name = 'Kullanıcı Aktivite Logu'
        verbose_name_plural = 'Kullanıcı Aktivite Logları'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp}"


class UserProfile(models.Model):
    """Kullanıcı profil ek bilgileri"""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Kullanıcı'
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        verbose_name='Profil Fotoğrafı'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Departman'
    )
    hire_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='İşe Başlama Tarihi'
    )
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Maaş'
    )
    emergency_contact = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Acil Durum İletişim'
    )
    emergency_phone = models.CharField(
        max_length=17,
        blank=True,
        verbose_name='Acil Durum Telefonu'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notlar'
    )
    
    class Meta:
        verbose_name = 'Kullanıcı Profili'
        verbose_name_plural = 'Kullanıcı Profilleri'
    
    def __str__(self):
        return f"{self.user.username} Profili"
