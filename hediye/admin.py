from django.contrib import admin
from .models import HediyeCeki, HediyeCekiKullanim


@admin.register(HediyeCeki)
class HediyeCekiAdmin(admin.ModelAdmin):
    list_display = ['kod', 'tutar', 'kalan_tutar', 'durum', 'gecerlilik_tarihi', 'musteri', 'aktif']
    list_filter = ['durum', 'aktif', 'gecerlilik_tarihi', 'olusturma_tarihi']
    search_fields = ['kod', 'musteri__ad', 'musteri__soyad']
    readonly_fields = ['olusturma_tarihi', 'kullanilma_tarihi']
    
    fieldsets = (
        ('Çek Bilgileri', {
            'fields': ('kod', 'tutar', 'kalan_tutar', 'gecerlilik_tarihi')
        }),
        ('İlişkiler', {
            'fields': ('musteri', 'olusturan')
        }),
        ('Durum', {
            'fields': ('durum', 'aktif')
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi', 'kullanilma_tarihi'),
            'classes': ('collapse',)
        }),
        ('Notlar', {
            'fields': ('aciklama',),
            'classes': ('collapse',)
        }),
    )


@admin.register(HediyeCekiKullanim)
class HediyeCekiKullanimAdmin(admin.ModelAdmin):
    list_display = ['hediye_ceki', 'kullanilan_tutar', 'kullanim_tarihi', 'satis_id', 'kullanan']
    list_filter = ['kullanim_tarihi', 'kullanan']
    search_fields = ['hediye_ceki__kod', 'satis_id']
    readonly_fields = ['kullanim_tarihi']
