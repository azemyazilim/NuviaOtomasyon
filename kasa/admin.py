from django.contrib import admin
from .models import Kasa, KasaHareket, KasaVirman, KasaCikis, KasaGiris


@admin.register(Kasa)
class KasaAdmin(admin.ModelAdmin):
    list_display = ('ad', 'tip', 'guncel_bakiye', 'aktif', 'olusturma_tarihi')
    list_filter = ('tip', 'aktif')
    search_fields = ('ad', 'aciklama')
    ordering = ('tip', 'ad')


@admin.register(KasaHareket)
class KasaHareketAdmin(admin.ModelAdmin):
    list_display = ('kasa', 'tip', 'kaynak', 'tutar', 'tarih', 'kullanici')
    list_filter = ('tip', 'kaynak', 'kasa', 'tarih')
    search_fields = ('aciklama', 'kasa__ad')
    ordering = ('-tarih',)


@admin.register(KasaVirman)
class KasaVirmanAdmin(admin.ModelAdmin):
    list_display = ('kaynak_kasa', 'hedef_kasa', 'tutar', 'tarih', 'kullanici')
    list_filter = ('kaynak_kasa', 'hedef_kasa', 'tarih')
    search_fields = ('aciklama',)
    ordering = ('-tarih',)


@admin.register(KasaCikis)
class KasaCikisAdmin(admin.ModelAdmin):
    list_display = ('kasa', 'tutar', 'sebep', 'tarih', 'kullanici')
    list_filter = ('kasa', 'sebep', 'tarih')
    search_fields = ('aciklama',)
    ordering = ('-tarih',)


@admin.register(KasaGiris)
class KasaGirisAdmin(admin.ModelAdmin):
    list_display = ('kasa', 'tutar', 'sebep', 'tarih', 'kullanici')
    list_filter = ('kasa', 'sebep', 'tarih')
    search_fields = ('aciklama',)
    ordering = ('-tarih',)
