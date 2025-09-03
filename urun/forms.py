from django import forms
from .models import Urun, UrunKategoriUst, UrunKategoriAlt, Marka, Varyasyon


class UrunForm(forms.ModelForm):
    """Ürün formu"""
    
    class Meta:
        model = Urun
        fields = [
            'barkod', 'sku', 'ad', 'aciklama', 'kategori', 'marka',
            'varyasyonlar', 'cinsiyet', 'alis_fiyati', 'kar_marji',
            'satis_fiyati', 'stok_miktari', 'minimum_stok', 'resim', 'aktif'
        ]
        
        widgets = {
            'barkod': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Barkod numarasını girin'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ürün kodunu girin (opsiyonel)'
            }),
            'ad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ürün adını girin'
            }),
            'aciklama': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ürün açıklaması (opsiyonel)'
            }),
            'kategori': forms.Select(attrs={
                'class': 'form-select'
            }),
            'marka': forms.Select(attrs={
                'class': 'form-select'
            }),
            'varyasyonlar': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'cinsiyet': forms.Select(attrs={
                'class': 'form-select'
            }),
            'alis_fiyati': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'kar_marji': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '1000',
                'placeholder': '50.00'
            }),
            'satis_fiyati': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'readonly': True
            }),
            'stok_miktari': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'minimum_stok': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '5'
            }),
            'resim': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'aktif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marka alanını opsiyonel yap
        self.fields['marka'].required = False
        self.fields['marka'].empty_label = "Marka Seçin"
        
        # Varyasyonları opsiyonel yap
        self.fields['varyasyonlar'].required = False


class MarkaForm(forms.ModelForm):
    """Marka formu"""
    
    class Meta:
        model = Marka
        fields = ['ad', 'aciklama', 'logo', 'aktif']
        
        widgets = {
            'ad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Marka adını girin'
            }),
            'aciklama': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Marka açıklaması (opsiyonel)'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'aktif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['aciklama'].required = False
        self.fields['logo'].required = False
