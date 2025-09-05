from django.contrib import admin
from .models import UrunKategoriUst, Renk, Beden, Marka, Urun, UrunVaryanti


@admin.register(UrunKategoriUst)
class UrunKategoriUstAdmin(admin.ModelAdmin):
    list_display = ['ad', 'aktif', 'olusturma_tarihi']
    list_filter = ['aktif', 'olusturma_tarihi']
    search_fields = ['ad']
    ordering = ['ad']


@admin.register(Renk)
class RenkAdmin(admin.ModelAdmin):
    list_display = ['ad', 'kod', 'hex_kod', 'sira', 'aktif']
    list_filter = ['aktif']
    search_fields = ['ad', 'kod']
    ordering = ['sira', 'ad']
    list_editable = ['sira', 'aktif']


@admin.register(Beden)
class BedenAdmin(admin.ModelAdmin):
    list_display = ['ad', 'kod', 'tip', 'sira', 'aktif']
    list_filter = ['tip', 'aktif']
    search_fields = ['ad', 'kod']
    ordering = ['tip', 'sira', 'ad']
    list_editable = ['sira', 'aktif']


@admin.register(Marka)
class MarkaAdmin(admin.ModelAdmin):
    list_display = ['ad', 'aktif', 'olusturma_tarihi']
    list_filter = ['aktif', 'olusturma_tarihi']
    search_fields = ['ad']
    ordering = ['ad']


class UrunVaryantiInline(admin.TabularInline):
    model = UrunVaryanti
    extra = 0
    readonly_fields = ['barkod', 'olusturma_tarihi']
    fields = ['renk', 'beden', 'stok_miktari', 'barkod', 'aktif']


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ['urun_kodu', 'ad', 'kategori', 'marka', 'varyasyonlu', 'satis_fiyati', 'toplam_stok', 'aktif']
    list_filter = ['kategori', 'marka', 'varyasyonlu', 'aktif', 'cinsiyet']
    search_fields = ['ad', 'urun_kodu']
    ordering = ['-olusturma_tarihi']
    readonly_fields = ['urun_kodu', 'olusturma_tarihi', 'guncelleme_tarihi']
    inlines = [UrunVaryantiInline]
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('urun_kodu', 'ad', 'aciklama', 'kategori', 'marka', 'cinsiyet', 'birim')
        }),
        ('Varyasyon', {
            'fields': ('varyasyonlu',)
        }),
        ('Fiyat Bilgileri', {
            'fields': ('alis_fiyati', 'kar_orani', 'satis_fiyati')
        }),
        ('Ürün Resmi', {
            'fields': ('resim',)
        }),
        ('Durum', {
            'fields': ('aktif', 'stok_takibi', 'kritik_stok_seviyesi')
        }),
        ('Tarih Bilgileri', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UrunVaryanti)
class UrunVaryantiAdmin(admin.ModelAdmin):
    list_display = ['urun', 'varyasyon_adi', 'barkod', 'stok_miktari', 'aktif']
    list_filter = ['urun__kategori', 'renk', 'beden', 'aktif']
    search_fields = ['urun__ad', 'barkod']
    ordering = ['urun', 'renk', 'beden']
    readonly_fields = ['barkod', 'olusturma_tarihi', 'guncelleme_tarihi']
