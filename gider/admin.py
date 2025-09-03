from django.contrib import admin
from .models import Gider, GiderKategori


@admin.register(GiderKategori)
class GiderKategoriAdmin(admin.ModelAdmin):
    list_display = ['ad', 'renk', 'ikon', 'aktif', 'olusturma_tarihi']
    list_filter = ['aktif', 'olusturma_tarihi']
    search_fields = ['ad', 'aciklama']
    list_editable = ['aktif']
    ordering = ['ad']


@admin.register(Gider)
class GiderAdmin(admin.ModelAdmin):
    list_display = ['baslik', 'kategori', 'tutar', 'tarih', 'odeme_yontemi', 'olusturan', 'aktif']
    list_filter = ['kategori', 'odeme_yontemi', 'tarih', 'aktif', 'tekrarlayan']
    search_fields = ['baslik', 'aciklama', 'tedarikci', 'fatura_no']
    list_editable = ['aktif']
    date_hierarchy = 'tarih'
    ordering = ['-tarih', '-olusturma_tarihi']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('baslik', 'kategori', 'tutar', 'tarih', 'odeme_yontemi')
        }),
        ('Detay Bilgileri', {
            'fields': ('tedarikci', 'fatura_no', 'aciklama'),
            'classes': ('collapse',)
        }),
        ('Belgeler', {
            'fields': ('fatura_fotografi', 'ek_belge'),
            'classes': ('collapse',)
        }),
        ('Tekrarlayan Gider', {
            'fields': ('tekrarlayan', 'tekrar_periyodu'),
            'classes': ('collapse',)
        }),
        ('Sistem Bilgileri', {
            'fields': ('aktif', 'olusturan'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Yeni kayıt ise
            obj.olusturan = request.user
        super().save_model(request, obj, form, change)
