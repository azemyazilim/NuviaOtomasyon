from django import forms
from django.forms.widgets import DateInput, NumberInput, Textarea, Select, FileInput
from .models import Gider, GiderKategori
from datetime import date


class GiderForm(forms.ModelForm):
    """Gider ekleme/düzenleme formu"""
    
    class Meta:
        model = Gider
        fields = [
            'baslik', 'kategori', 'tutar', 'tarih', 'odeme_yontemi', 
            'tedarikci', 'fatura_no', 'aciklama', 'fatura_fotografi', 
            'ek_belge', 'tekrarlayan', 'tekrar_periyodu'
        ]
        widgets = {
            'baslik': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Gider başlığı (örn: Elektrik faturası, ofis kirası)'
            }),
            'kategori': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tutar': NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'tarih': DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'odeme_yontemi': Select(attrs={
                'class': 'form-select'
            }),
            'tedarikci': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Firma/kişi adı (opsiyonel)'
            }),
            'fatura_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Fatura veya fiş numarası (opsiyonel)'
            }),
            'aciklama': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detaylı açıklama (opsiyonel)'
            }),
            'fatura_fotografi': FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'ek_belge': FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png'
            }),
            'tekrarlayan': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tekrar_periyodu': Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Bugünün tarihini varsayılan olarak ayarla
        if not self.instance.pk:
            self.fields['tarih'].initial = date.today()
        
        # Tüm kategorileri göster (artık aktif/pasif ayrımı yok)
        self.fields['kategori'].queryset = GiderKategori.objects.all()
        
        # Tekrar periyodu alanını başlangıçta gizle
        self.fields['tekrar_periyodu'].widget.attrs['style'] = 'display: none;'

    def clean_tutar(self):
        tutar = self.cleaned_data.get('tutar')
        if tutar and tutar <= 0:
            raise forms.ValidationError("Tutar 0'dan büyük olmalıdır.")
        return tutar

    def clean(self):
        cleaned_data = super().clean()
        tekrarlayan = cleaned_data.get('tekrarlayan')
        tekrar_periyodu = cleaned_data.get('tekrar_periyodu')
        
        if tekrarlayan and not tekrar_periyodu:
            raise forms.ValidationError("Tekrarlayan gider için periyot seçilmelidir.")
        
        return cleaned_data


class GiderKategoriForm(forms.ModelForm):
    """Gider kategorisi ekleme/düzenleme formu"""
    
    class Meta:
        model = GiderKategori
        fields = ['ad', 'aciklama', 'renk', 'ikon', 'aktif']
        widgets = {
            'ad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kategori adı (örn: Kira, Elektrik, Personel)'
            }),
            'aciklama': Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Kategori açıklaması (opsiyonel)'
            }),
            'renk': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#6c757d'
            }),
            'ikon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'fas fa-money-bill'
            }),
            'aktif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_ad(self):
        ad = self.cleaned_data.get('ad')
        if not ad:
            raise forms.ValidationError("Kategori adı zorunludur.")
        return ad.strip()


class GiderAramaForm(forms.Form):
    """Gider arama ve filtreleme formu"""
    
    baslik = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Başlık ara...'
        })
    )
    
    kategori = forms.ModelChoiceField(
        queryset=GiderKategori.objects.all(),
        required=False,
        empty_label="Tüm Kategoriler",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    baslangic_tarihi = forms.DateField(
        required=False,
        widget=DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    bitis_tarihi = forms.DateField(
        required=False,
        widget=DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    odeme_yontemi = forms.ChoiceField(
        choices=[('', 'Tüm Ödeme Yöntemleri')] + Gider.ODEME_YONTEMLERI,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    min_tutar = forms.DecimalField(
        required=False,
        min_value=0,
        widget=NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Min. tutar'
        })
    )
    
    max_tutar = forms.DecimalField(
        required=False,
        min_value=0,
        widget=NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Max. tutar'
        })
    )
