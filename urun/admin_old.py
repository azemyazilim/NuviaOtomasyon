from django.contrib import admin
from .models import UrunKategoriUst, Varyasyon, Marka, Urun, UrunVaryanti


@admin.register(UrunKategoriUst)
class UrunKategoriUstAdmin(admin.ModelAdmin):
    list_display = ('ad', 'olusturma_tarihi')
    search_fields = ('ad',)
    ordering = ('ad',)


@admin.register(Varyasyon)
class VaryasyonAdmin(admin.ModelAdmin):
    list_display = ('tip', 'deger', 'hex_kodu', 'sira', 'aktif')
    list_filter = ('tip', 'aktif')
    search_fields = ('deger',)
    ordering = ('tip', 'sira', 'deger')


@admin.register(Marka)
class MarkaAdmin(admin.ModelAdmin):
    list_display = ('ad', 'aktif', 'olusturma_tarihi')
    list_filter = ('aktif',)
    search_fields = ('ad',)
    ordering = ('ad',)


class UrunVaryantiInline(admin.TabularInline):
    model = UrunVaryanti
    extra = 0
    fields = ('barkod', 'renk', 'beden', 'diger_varyasyon', 'alis_fiyati', 'kar_orani', 'satis_fiyati', 'stok_miktari', 'aktif')
    readonly_fields = ('satis_fiyati',)


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ('sku', 'ad', 'kategori', 'marka', 'varyasyonlu', 'aktif', 'toplam_stok')
    list_filter = ('kategori', 'marka', 'varyasyonlu', 'aktif', 'cinsiyet')
    search_fields = ('sku', 'ad', 'aciklama')
    ordering = ('-olusturma_tarihi',)
    filter_horizontal = ('varyasyon_tipleri',)
    inlines = [UrunVaryantiInline]
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('sku', 'ad', 'aciklama', 'kategori', 'marka', 'cinsiyet', 'birim', 'resim')
        }),
        ('Varyasyon Ayarları', {
            'fields': ('varyasyonlu', 'varyasyon_tipleri'),
            'classes': ('collapse',)
        }),
        ('Fiyat ve Stok (Varyasyonsuz Ürünler İçin)', {
            'fields': ('temel_alis_fiyati', 'temel_kar_orani', 'temel_satis_fiyati', 'temel_stok_miktari', 'kritik_stok_seviyesi'),
            'classes': ('collapse',)
        }),
        ('Durum', {
            'fields': ('aktif', 'stok_takibi')
        })
    )
    
    readonly_fields = ('temel_satis_fiyati',)


@admin.register(UrunVaryanti)
class UrunVaryantiAdmin(admin.ModelAdmin):
    list_display = ('barkod', 'urun', 'varyasyon_adi', 'satis_fiyati', 'stok_miktari', 'aktif')
    list_filter = ('urun__kategori', 'renk', 'beden', 'aktif')
    search_fields = ('barkod', 'urun__ad', 'urun__sku')
    ordering = ('urun', 'renk', 'beden')
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('urun', 'barkod', 'ek_aciklama', 'resim')
        }),
        ('Varyasyonlar', {
            'fields': ('renk', 'beden', 'diger_varyasyon')
        }),
        ('Fiyat ve Stok', {
            'fields': ('alis_fiyati', 'kar_orani', 'satis_fiyati', 'stok_miktari')
        }),
        ('Durum', {
            'fields': ('aktif',)
        })
    )
    
    readonly_fields = ('satis_fiyati',)
