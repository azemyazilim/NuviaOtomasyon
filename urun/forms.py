from django import forms
from .models import Urun, UrunKategoriUst, Marka, Varyasyon, UrunVaryanti


class UrunForm(forms.ModelForm):
    """Ana ürün formu"""
    
    class Meta:
        model = Urun
        fields = [
            'sku', 'ad', 'aciklama', 'kategori', 'marka', 'cinsiyet', 'birim',
            'varyasyonlu', 'varyasyon_tipleri', 'temel_alis_fiyati', 'temel_kar_orani',
            'temel_satis_fiyati', 'kritik_stok_seviyesi',
            'resim', 'aktif', 'stok_takibi'
        ]
        
        widgets = {
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Otomatik oluşturulacak'
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
            'cinsiyet': forms.Select(attrs={
                'class': 'form-select'
            }),
            'birim': forms.Select(attrs={
                'class': 'form-select'
            }),
            'varyasyonlu': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'varyasyon_tipleri': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'temel_alis_fiyati': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'temel_kar_orani': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '1000',
                'placeholder': '50.00'
            }),
            'temel_satis_fiyati': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'readonly': True
            }),
            'kritik_stok_seviyesi': forms.NumberInput(attrs={
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
            }),
            'stok_takibi': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marka alanını opsiyonel yap
        self.fields['marka'].required = False
        self.fields['marka'].empty_label = "Marka Seçin"
        
        # Varyasyon tiplerini opsiyonel yap
        self.fields['varyasyon_tipleri'].required = False


class UrunVaryantiForm(forms.ModelForm):
    """Ürün varyantı formu"""
    
    class Meta:
        model = UrunVaryanti
        fields = [
            'barkod', 'renk', 'beden', 'diger_varyasyon',
            'alis_fiyati', 'kar_orani', 'satis_fiyati',
            'stok_miktari', 'ek_aciklama', 'resim', 'aktif'
        ]
        
        widgets = {
            'barkod': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Otomatik oluşturulacak'
            }),
            'renk': forms.Select(attrs={
                'class': 'form-select'
            }),
            'beden': forms.Select(attrs={
                'class': 'form-select'
            }),
            'diger_varyasyon': forms.Select(attrs={
                'class': 'form-select'
            }),
            'alis_fiyati': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'kar_orani': forms.NumberInput(attrs={
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
            'ek_aciklama': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ek açıklama (opsiyonel)'
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
        # Tüm varyasyon alanlarını opsiyonel yap
        self.fields['renk'].required = False
        self.fields['beden'].required = False
        self.fields['diger_varyasyon'].required = False
        
        # Empty label'lar
        self.fields['renk'].empty_label = "Renk Seçin"
        self.fields['beden'].empty_label = "Beden Seçin"
        self.fields['diger_varyasyon'].empty_label = "Diğer Varyasyon Seçin"


class VaryasyonForm(forms.ModelForm):
    """Varyasyon formu"""
    
    class Meta:
        model = Varyasyon
        fields = ['tip', 'deger', 'hex_kodu', 'sira', 'aktif']
        
        widgets = {
            'tip': forms.Select(attrs={
                'class': 'form-select'
            }),
            'deger': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Varyasyon değerini girin'
            }),
            'hex_kodu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '#FF0000 (Sadece renk için)',
                'maxlength': '7'
            }),
            'sira': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'aktif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hex_kodu'].required = False


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
