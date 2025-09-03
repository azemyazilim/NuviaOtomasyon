from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import authenticate
from .models import CustomUser, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Özelleştirilmiş kullanıcı oluşturma formu"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'E-posta adresi'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ad'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Soyad'
        })
    )
    
    phone_number = forms.CharField(
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+90555123456'
        })
    )
    
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 
                 'phone_number', 'role', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Kullanıcı adı'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Şifre'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Şifre tekrar'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
            # Kullanıcı profili oluştur
            UserProfile.objects.create(user=user)
        return user


class CustomUserChangeForm(UserChangeForm):
    """Özelleştirilmiş kullanıcı düzenleme formu"""
    
    password = None  # Şifre alanını gizle
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 
                 'phone_number', 'address', 'birth_date', 'role', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserProfileForm(forms.ModelForm):
    """Kullanıcı profil formu"""
    
    class Meta:
        model = UserProfile
        fields = ('profile_picture', 'department', 'hire_date', 'salary',
                 'emergency_contact', 'emergency_phone', 'notes')
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class LoginForm(forms.Form):
    """Özelleştirilmiş giriş formu"""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kullanıcı adı',
            'required': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Şifre',
            'required': True
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            self.user_cache = authenticate(
                request=self.request,
                username=username,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError('Geçersiz kullanıcı adı veya şifre.')
            elif not self.user_cache.is_active:
                raise forms.ValidationError('Bu hesap devre dışı bırakılmış.')
        
        return self.cleaned_data
    
    def get_user(self):
        return getattr(self, 'user_cache', None)


class PasswordChangeForm(forms.Form):
    """Şifre değiştirme formu"""
    
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mevcut şifre'
        })
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Yeni şifre'
        })
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Yeni şifre tekrar'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Mevcut şifre yanlış.')
        return old_password
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Şifreler eşleşmiyor.')
        return password2
    
    def save(self, commit=True):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class UserSearchForm(forms.Form):
    """Kullanıcı arama formu"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kullanıcı adı, ad, soyad veya e-posta ile ara...'
        })
    )
    
    role = forms.ChoiceField(
        choices=[('', 'Tüm Roller')] + CustomUser.ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'Tümü'),
            ('true', 'Aktif'),
            ('false', 'Pasif')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
