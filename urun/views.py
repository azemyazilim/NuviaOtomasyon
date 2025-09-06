from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from .models import Urun, UrunKategoriUst, Renk, Beden, Marka, UrunVaryanti


@login_required
def urun_listesi(request):
    """Ürün listesi"""
    from django.db.models import Sum, Q
    
    # Arama parametreleri
    query = request.GET.get('q', '').strip()
    kategori_filter = request.GET.get('kategori', '')
    durum_filter = request.GET.get('durum', '')
    varyasyonlu_filter = request.GET.get('varyasyonlu', '')  # Yeni varyasyon filtresi
    
    # Base queryset
    urunler = Urun.objects.select_related('kategori', 'marka').prefetch_related('varyantlar').all()
    
    # Arama filtresi
    if query:
        urunler = urunler.filter(
            Q(ad__icontains=query) | 
            Q(urun_kodu__icontains=query) |
            Q(aciklama__icontains=query)
        )
    
    # Kategori filtresi
    if kategori_filter:
        urunler = urunler.filter(kategori_id=kategori_filter)
    
    # Varyasyon filtresi
    if varyasyonlu_filter == '1':
        urunler = urunler.filter(varyasyonlu=True)
    
    # Durum filtresi için ürünleri filtrele
    filtered_urunler = []
    for urun in urunler:
        if durum_filter:
            toplam_stok = urun.toplam_stok
            if durum_filter == 'stokta' and toplam_stok <= 0:
                continue
            elif durum_filter == 'kritik' and not (0 < toplam_stok <= urun.kritik_stok_seviyesi):
                continue
            elif durum_filter == 'tukendi' and toplam_stok != 0:
                continue
        filtered_urunler.append(urun)
    
    # Final liste
    final_urunler = filtered_urunler if durum_filter else urunler
    
    # Her ürün için silme kontrolü ekle
    def silme_kontrolu_hizli(urun):
        """Hızlı silme kontrolü - sadece boolean döner"""
        from satis.models import SatisDetay
        
        # Satış kontrolü
        if SatisDetay.objects.filter(urun=urun).exists():
            return False
        
        # Stok kontrolü
        if urun.toplam_stok > 0:
            return False
            
        # Varyant stok kontrolü
        for varyant in urun.varyantlar.all():
            if varyant.stok_miktari > 0:
                return False
        
        return True
    
    # Her ürüne silme izni bilgisi ekle
    for urun in final_urunler:
        urun.silme_izni = silme_kontrolu_hizli(urun)
    
    # İstatistikler
    tum_urunler = Urun.objects.all()
    toplam_urun = tum_urunler.count()
    aktif_urun = tum_urunler.filter(aktif=True).count()
    kritik_stok = len([u for u in tum_urunler if 0 < u.toplam_stok <= u.kritik_stok_seviyesi])
    tukenen_stok = len([u for u in tum_urunler if u.toplam_stok == 0])
    
    # Kategoriler dropdown için
    kategoriler = UrunKategoriUst.objects.filter(aktif=True).order_by('ad')
    
    # Sayfalama
    paginator = Paginator(final_urunler, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'urunler': page_obj,  # Template uyumluluğu için
        'title': 'Varyasyon Yönetimi' if varyasyonlu_filter == '1' else 'Ürün Listesi',
        'query': query,
        'kategori_filter': kategori_filter,
        'durum_filter': durum_filter,
        'varyasyonlu_filter': varyasyonlu_filter,
        'kategoriler': kategoriler,
        'toplam_urun': toplam_urun,
        'aktif_urun': aktif_urun,
        'kritik_stok': kritik_stok,
        'tukenen_stok': tukenen_stok,
    }
    return render(request, 'urun/liste.html', context)


@login_required
def urun_ekle(request):
    """Ürün ekleme"""
    if request.method == 'POST':
        try:
            # Temel bilgileri al
            ad = request.POST.get('ad', '').strip()
            aciklama = request.POST.get('aciklama', '').strip()
            kategori_id = request.POST.get('kategori')
            marka_id = request.POST.get('marka') if request.POST.get('marka') else None
            cinsiyet = request.POST.get('cinsiyet', 'kadin')
            birim = request.POST.get('birim', 'adet')
            varyasyonlu = request.POST.get('varyasyonlu') == 'on'
            
            # Fiyat bilgileri
            alis_fiyati = float(request.POST.get('alis_fiyati', 0))
            kar_orani = float(request.POST.get('kar_orani', 50))
            satis_fiyati = float(request.POST.get('satis_fiyati', 0))
            
            # Kategori ve marka objeleri
            kategori = get_object_or_404(UrunKategoriUst, id=kategori_id)
            marka = Marka.objects.get(id=marka_id) if marka_id else None
            
            # Ürün oluştur
            urun = Urun.objects.create(
                ad=ad,
                aciklama=aciklama,
                kategori=kategori,
                marka=marka,
                cinsiyet=cinsiyet,
                birim=birim,
                varyasyonlu=varyasyonlu,
                alis_fiyati=alis_fiyati,
                kar_orani=kar_orani,
                satis_fiyati=satis_fiyati,
                olusturan=request.user
            )
            
            # Varyantları oluştur
            if varyasyonlu:
                # Seçilen renk ve bedenler
                secilen_renkler = request.POST.getlist('renkler')
                secilen_bedenler = request.POST.getlist('bedenler')
                
                if secilen_renkler and secilen_bedenler:
                    # Kombinasyonları oluştur
                    for renk_id in secilen_renkler:
                        for beden_id in secilen_bedenler:
                            renk = Renk.objects.get(id=renk_id)
                            beden = Beden.objects.get(id=beden_id)
                            
                            UrunVaryanti.objects.create(
                                urun=urun,
                                renk=renk,
                                beden=beden,
                                stok_miktari=1,  # Varsayılan stok
                                stok_kaydedildi=False,  # Henüz kaydedilmemiş
                                aktif=True
                            )
                    
                    messages.success(request, f'✅ {urun.ad} ve {len(secilen_renkler) * len(secilen_bedenler)} varyantı eklendi!')
                else:
                    messages.warning(request, 'Varyasyonlu ürün için renk ve beden seçmelisiniz!')
            else:
                # Varyasyonsuz ürün için tek varyant oluştur
                UrunVaryanti.objects.create(
                    urun=urun,
                    renk=None,
                    beden=None,
                    stok_miktari=int(request.POST.get('stok_miktari', 0)),
                    stok_kaydedildi=True,  # Varyasyonsuz ürünler direkt kaydedilmiş sayılır
                    aktif=True
                )
                messages.success(request, f'✅ {urun.ad} ürünü eklendi!')
            
            return redirect('urun:liste')
            
        except Exception as e:
            messages.error(request, f'❌ Ürün eklenirken hata oluştu: {str(e)}')
    
    context = {
        'kategoriler': UrunKategoriUst.objects.filter(aktif=True).order_by('ad'),
        'markalar': Marka.objects.filter(aktif=True).order_by('ad'),
        'renkler': Renk.objects.filter(aktif=True).order_by('sira'),
        'bedenler': Beden.objects.filter(aktif=True).order_by('tip', 'sira'),
        'title': 'Yeni Ürün Ekle'
    }
    return render(request, 'urun/ekle.html', context)


@login_required
def barkod_sorgula(request):
    """Barkod sorgulama"""
    if request.method == 'POST':
        barkod = request.POST.get('barkod', '').strip()
        
        if barkod:
            # Barkod çözümleme
            sonuc = UrunVaryanti.barkod_cozumle(barkod)
            
            if sonuc:
                # Aynı ürünün tüm varyantlarını getir
                tum_varyantlar = UrunVaryanti.objects.filter(
                    urun=sonuc['urun'], 
                    aktif=True
                ).select_related('renk', 'beden')
                
                context = {
                    'sonuc': sonuc,
                    'tum_varyantlar': tum_varyantlar,
                    'barkod': barkod,
                    'title': 'Barkod Sorgulama Sonucu'
                }
                return render(request, 'urun/barkod_sonuc.html', context)
            else:
                messages.error(request, 'Barkod bulunamadı!')
        else:
            messages.error(request, 'Lütfen geçerli bir barkod girin!')
    
    context = {
        'title': 'Barkod Sorgula'
    }
    return render(request, 'urun/barkod.html', context)


@login_required
def kategori_yonetimi(request):
    """Kategori yönetimi"""
    from django.db.models import Count
    
    kategoriler = UrunKategoriUst.objects.all().order_by('ad')
    
    # Toplam ürün sayısını hesapla
    toplam_urun_sayisi = Urun.objects.count()
    
    context = {
        'kategoriler': kategoriler,
        'ust_kategoriler': kategoriler,  # Template beklenen değişken
        'toplam_urun_sayisi': toplam_urun_sayisi,
        'title': 'Kategori Yönetimi'
    }
    return render(request, 'urun/kategori_yonetimi.html', context)


@login_required
def ust_kategori_ekle(request):
    """Üst kategori ekleme/düzenleme"""
    if request.method == 'POST':
        kategori_id = request.GET.get('edit')
        ad = request.POST.get('ad')
        aciklama = request.POST.get('aciklama', '')
        
        if not ad:
            messages.error(request, 'Kategori adı gereklidir!')
            return redirect('urun:kategori')
        
        try:
            if kategori_id:  # Düzenleme
                kategori = get_object_or_404(UrunKategoriUst, id=kategori_id)
                kategori.ad = ad
                kategori.aciklama = aciklama
                kategori.save()
                messages.success(request, f'{ad} kategorisi başarıyla güncellendi!')
            else:  # Yeni ekleme
                UrunKategoriUst.objects.create(
                    ad=ad,
                    aciklama=aciklama,
                    aktif=True
                )
                messages.success(request, f'{ad} kategorisi başarıyla eklendi!')
        except Exception as e:
            messages.error(request, f'Hata oluştu: {str(e)}')
    
    return redirect('urun:kategori')


@login_required
def ust_kategori_sil(request, kategori_id):
    """Üst kategori silme"""
    if request.method == 'POST':
        try:
            kategori = get_object_or_404(UrunKategoriUst, id=kategori_id)
            kategori_ad = kategori.ad
            
            # Kategoriye bağlı ürün var mı kontrol et
            if kategori.urun_set.exists():
                messages.error(request, f'{kategori_ad} kategorisine bağlı ürünler bulunuyor. Önce ürünleri başka kategoriye taşıyın.')
            else:
                kategori.delete()
                messages.success(request, f'{kategori_ad} kategorisi başarıyla silindi!')
        except Exception as e:
            messages.error(request, f'Hata oluştu: {str(e)}')
    
    return redirect('urun:kategori')


@login_required
def marka_listesi(request):
    """Marka listesi"""
    if request.method == 'POST':
        try:
            ad = request.POST.get('ad', '').strip()
            aciklama = request.POST.get('aciklama', '').strip()
            
            if ad:
                Marka.objects.create(
                    ad=ad,
                    aciklama=aciklama
                )
                messages.success(request, f'{ad} markası başarıyla eklendi!')
            else:
                messages.error(request, 'Marka adı boş olamaz!')
        except Exception as e:
            messages.error(request, f'Hata oluştu: {str(e)}')
        
        return redirect('urun:marka_listesi')
    
    markalar = Marka.objects.all().order_by('ad')
    
    context = {
        'markalar': markalar,
        'title': 'Marka Yönetimi'
    }
    return render(request, 'urun/marka_liste.html', context)


@login_required
def stok_durumu(request):
    """Stok durumu raporu"""
    urunler = Urun.objects.select_related('kategori', 'marka').all().order_by('ad')
    
    # Stok durumu filtresi
    stok_filtre = request.GET.get('stok_filtre', 'tumu')
    if stok_filtre == 'tukenmek_uzere':
        urunler = urunler.filter(stok_miktari__lte=10)
    elif stok_filtre == 'tukenmis':
        urunler = urunler.filter(stok_miktari=0)
    elif stok_filtre == 'stokta_var':
        urunler = urunler.filter(stok_miktari__gt=0)
    
    context = {
        'urunler': urunler,
        'stok_filtre': stok_filtre,
        'title': 'Stok Durumu'
    }
    return render(request, 'urun/stok_raporu.html', context)


@login_required
def en_cok_satanlar(request):
    """En çok satan ürünler raporu"""
    from django.db.models import Sum
    from satis.models import SatisDetay
    
    # En çok satan ürünler (son 30 gün)
    import datetime
    son_30_gun = datetime.date.today() - datetime.timedelta(days=30)
    
    en_cok_satanlar = SatisDetay.objects.filter(
        satis__satis_tarihi__date__gte=son_30_gun
    ).values(
        'urun__ad', 'urun__urun_kodu', 'urun__satis_fiyati',
        'urun__kategori__ad', 'urun__marka__ad'
    ).annotate(
        toplam_miktar=Sum('miktar'),
        toplam_tutar=Sum('toplam_fiyat')
    ).order_by('-toplam_miktar')[:20]
    
    context = {
        'en_cok_satanlar': en_cok_satanlar,
        'title': 'En Çok Satanlar'
    }
    return render(request, 'urun/en_cok_satanlar.html', context)


@login_required
def kar_zarar_raporu(request):
    """Kar zarar raporu"""
    from django.db.models import Sum, F
    from satis.models import SatisItem
    import datetime
    
    # Tarih filtreleri
    bugun = datetime.date.today()
    son_30_gun = bugun - datetime.timedelta(days=30)
    
    # Kar zarar hesaplaması
    satislar = SatisItem.objects.filter(
        satis__tarih__gte=son_30_gun
    ).aggregate(
        toplam_satis=Sum('toplam_fiyat'),
        toplam_miktar=Sum('miktar')
    )
    
    # Ürün bazında kar zarar
    urun_kar_zarar = SatisItem.objects.filter(
        satis__tarih__gte=son_30_gun
    ).values(
        'urun__ad', 'urun__alis_fiyati', 'urun__satis_fiyati'
    ).annotate(
        toplam_miktar=Sum('miktar'),
        toplam_satis=Sum('toplam_fiyat'),
        toplam_maliyet=Sum(F('miktar') * F('urun__alis_fiyati')),
        kar=Sum(F('toplam_fiyat') - (F('miktar') * F('urun__alis_fiyati')))
    ).order_by('-kar')
    
    context = {
        'satislar': satislar,
        'urun_kar_zarar': urun_kar_zarar,
        'title': 'Kar Zarar Raporu'
    }
    return render(request, 'urun/kar_zarar.html', context)


@login_required
def urun_detay(request, urun_id):
    """Ürün detay sayfası"""
    urun = get_object_or_404(Urun, id=urun_id)
    varyantlar = urun.varyantlar.filter(aktif=True).order_by('renk__ad', 'beden__ad')
    
    # Silme kontrolü
    def silme_kontrolu_detay(urun):
        """Detaylı silme kontrolü"""
        from satis.models import SatisDetay
        
        # Satış kontrolü
        if SatisDetay.objects.filter(urun=urun).exists():
            return False, "Bu ürün daha önce satılmıştır."
        
        # Stok kontrolü
        if urun.toplam_stok > 0:
            return False, f"Bu ürünün stoğu bulunmaktadır ({urun.toplam_stok} adet)."
            
        # Varyant stok kontrolü
        for varyant in urun.varyantlar.all():
            if varyant.stok_miktari > 0:
                return False, f"'{varyant.varyasyon_adi}' varyantının stoğu bulunmaktadır."
        
        return True, ""
    
    silme_izni, silme_mesaji = silme_kontrolu_detay(urun)
    
    context = {
        'urun': urun,
        'varyantlar': varyantlar,
        'title': f'{urun.ad} - Detay',
        'silme_izni': silme_izni,
        'silme_mesaji': silme_mesaji
    }
    return render(request, 'urun/detay.html', context)


@login_required
def urun_duzenle(request, urun_id):
    """Ürün düzenleme sayfası"""
    urun = get_object_or_404(Urun, id=urun_id)
    
    if request.method == 'POST':
        try:
            # Temel bilgileri güncelle
            urun.ad = request.POST.get('ad', '').strip()
            urun.aciklama = request.POST.get('aciklama', '').strip()
            
            # Kategori ve marka güncelle
            kategori_id = request.POST.get('kategori')
            marka_id = request.POST.get('marka') if request.POST.get('marka') else None
            
            urun.kategori = get_object_or_404(UrunKategoriUst, id=kategori_id)
            urun.marka = Marka.objects.get(id=marka_id) if marka_id else None
            
            # Diğer alanları güncelle
            urun.cinsiyet = request.POST.get('cinsiyet', 'unisex')
            urun.birim = request.POST.get('birim', 'adet')
            
            # Fiyat bilgileri
            urun.alis_fiyati = float(request.POST.get('alis_fiyati', 0))
            urun.kar_orani = float(request.POST.get('kar_orani', 50))
            urun.satis_fiyati = float(request.POST.get('satis_fiyati', 0))
            
            # Stok ayarları
            urun.kritik_stok_seviyesi = int(request.POST.get('kritik_stok_seviyesi', 5))
            urun.stok_takibi = request.POST.get('stok_takibi') == 'on'
            urun.aktif = request.POST.get('aktif') == 'on'
            
            urun.save()
            
            messages.success(request, f'✅ {urun.ad} ürünü başarıyla güncellendi!')
            return redirect('urun:detay', urun_id=urun.id)
            
        except Exception as e:
            messages.error(request, f'❌ Hata: {str(e)}')
    
    # Form için gerekli veriler
    kategoriler = UrunKategoriUst.objects.filter(aktif=True).order_by('ad')
    markalar = Marka.objects.filter(aktif=True).order_by('ad')
    
    context = {
        'urun': urun,
        'kategoriler': kategoriler,
        'markalar': markalar,
        'title': f'{urun.ad} - Düzenle'
    }
    return render(request, 'urun/duzenle.html', context)


@login_required
def urun_sil(request, urun_id):
    """Ürün silme"""
    urun = get_object_or_404(Urun, id=urun_id)
    
    # Silme kontrolü - hareket görmüş veya stoğu olan ürünler silinemez
    def silme_kontrolu(urun):
        """Ürünün silinip silinemeyeceğini kontrol eder"""
        from satis.models import SatisDetay
        
        # 1. Satış kontrolü - Bu ürün herhangi bir satışta var mı?
        satis_var = SatisDetay.objects.filter(urun=urun).exists()
        if satis_var:
            return False, "Bu ürün daha önce satılmıştır. Hareket görmüş ürünler silinemez."
        
        # 2. Stok kontrolü - Ürünün toplam stoğu var mı?
        toplam_stok = urun.toplam_stok
        if toplam_stok > 0:
            return False, f"Bu ürünün stoğu bulunmaktadır ({toplam_stok} adet). Stoğu olan ürünler silinemez."
        
        # 3. Varyant kontrolü - Herhangi bir varyantın stoğu var mı?
        for varyant in urun.varyantlar.all():
            if varyant.stok_miktari > 0:
                return False, f"'{varyant.varyasyon_adi}' varyantının stoğu bulunmaktadır ({varyant.stok_miktari} adet). Stoğu olan ürünler silinemez."
        
        return True, ""
    
    if request.method == 'POST':
        urun_adi = urun.ad
        
        # Silme kontrolü yap
        silme_izni, hata_mesaji = silme_kontrolu(urun)
        
        if not silme_izni:
            messages.error(request, f'❌ {hata_mesaji}')
            return redirect('urun:liste')
        
        try:
            # Varyantları da sil
            urun.varyantlar.all().delete()
            # Ürünü sil
            urun.delete()
            messages.success(request, f'✅ {urun_adi} ürünü başarıyla silindi!')
        except Exception as e:
            messages.error(request, f'❌ Silme işlemi sırasında hata: {str(e)}')
        
        return redirect('urun:liste')
    
    # GET isteği - onay sayfası
    # Silme kontrolü yap ve bilgileri template'e gönder
    silme_izni, hata_mesaji = silme_kontrolu(urun)
    
    context = {
        'urun': urun,
        'title': f'{urun.ad} - Sil',
        'silme_izni': silme_izni,
        'hata_mesaji': hata_mesaji
    }
    return render(request, 'urun/sil_onay.html', context)


@login_required
def varyasyon_yonet(request, urun_id):
    """Ürün varyasyonlarını yönetme sayfası"""
    urun = get_object_or_404(Urun, id=urun_id)
    
    # Sadece varyasyonlu ürünler için
    if not urun.varyasyonlu:
        messages.error(request, 'Bu ürün varyasyonlu değil!')
        return redirect('urun:detay', urun_id)
    
    # Mevcut varyantları getir
    mevcut_varyantlar = UrunVaryanti.objects.filter(urun=urun).select_related('renk', 'beden')
    
    # Düzenlenebilir varyant var mı kontrol et (stok_kaydedildi=False olanlar)
    has_editable_variants = mevcut_varyantlar.filter(stok_kaydedildi=False).exists()
    
    # Tüm renk ve bedenler
    renkler = Renk.objects.filter(aktif=True).order_by('sira', 'ad')
    bedenler = Beden.objects.filter(aktif=True).order_by('tip', 'sira', 'ad')
    
    context = {
        'urun': urun,
        'mevcut_varyantlar': mevcut_varyantlar,
        'has_editable_variants': has_editable_variants,
        'renkler': renkler,
        'bedenler': bedenler,
        'title': f'{urun.ad} - Varyasyon Yönetimi'
    }
    
    return render(request, 'urun/varyasyon_yonet.html', context)


@login_required
def varyasyon_olustur(request, urun_id):
    """Seçilen renk ve bedenlerle otomatik varyasyon oluşturma"""
    urun = get_object_or_404(Urun, id=urun_id)
    
    if not urun.varyasyonlu:
        return JsonResponse({'success': False, 'error': 'Bu ürün varyasyonlu değil!'})
    
    if request.method == 'POST':
        try:
            # Seçilen renk ve beden ID'lerini al
            renk_ids = request.POST.getlist('renkler')
            beden_ids = request.POST.getlist('bedenler')
            
            if not renk_ids and not beden_ids:
                return JsonResponse({'success': False, 'error': 'En az bir renk veya beden seçmelisiniz!'})
            
            # Eğer hiç renk seçilmemişse None olarak işle
            if not renk_ids:
                renk_ids = [None]
            # Eğer hiç beden seçilmemişse None olarak işle
            if not beden_ids:
                beden_ids = [None]
            
            created_count = 0
            skipped_count = 0
            
            with transaction.atomic():
                # Tüm kombinasyonları oluştur
                for renk_id in renk_ids:
                    for beden_id in beden_ids:
                        # Renk ve beden objelerini al
                        renk = Renk.objects.get(id=renk_id) if renk_id else None
                        beden = Beden.objects.get(id=beden_id) if beden_id else None
                        
                        # Bu kombinasyon zaten var mı kontrol et
                        varyant_exists = UrunVaryanti.objects.filter(
                            urun=urun,
                            renk=renk,
                            beden=beden
                        ).exists()
                        
                        if not varyant_exists:
                            # Yeni varyant oluştur
                            UrunVaryanti.objects.create(
                                urun=urun,
                                renk=renk,
                                beden=beden,
                                stok_miktari=1,  # Başlangıç stoku 1
                                stok_kaydedildi=False,  # Henüz kaydedilmemiş
                                aktif=True
                            )
                            created_count += 1
                        else:
                            skipped_count += 1
            
            return JsonResponse({
                'success': True, 
                'created': created_count,
                'skipped': skipped_count,
                'message': f'{created_count} varyant oluşturuldu, {skipped_count} zaten mevcuttu.'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Hata oluştu: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Geçersiz istek!'})


@login_required
def varyant_duzenle(request, varyant_id):
    """Varyant düzenleme"""
    from .models import StokHareket
    varyant = get_object_or_404(UrunVaryanti, id=varyant_id)
    
    if request.method == 'POST':
        try:
            yeni_stok_miktari = int(request.POST.get('stok_miktari', 0))
            aktif = request.POST.get('aktif') == 'on'
            
            # Eski stok miktarını al
            eski_stok = varyant.stok_miktari
            
            # Eğer stok miktarı değiştiyse stok hareketi oluştur
            if eski_stok != yeni_stok_miktari:
                fark = yeni_stok_miktari - eski_stok
                if fark > 0:
                    hareket_tipi = 'giris'
                    miktar = fark
                    aciklama = f'Manuel stok girişi (+{fark})'
                else:
                    hareket_tipi = 'cikis'
                    miktar = abs(fark)
                    aciklama = f'Manuel stok çıkışı (-{abs(fark)})'
                
                # Stok hareketini oluştur
                StokHareket.stok_hareketi_olustur(
                    varyant=varyant,
                    hareket_tipi=hareket_tipi,
                    miktar=miktar,
                    kullanici=request.user,
                    aciklama=aciklama,
                    referans_id=f'manuel_{varyant.id}'
                )
            else:
                # Sadece aktiflik durumu değişti
                varyant.aktif = aktif
                varyant.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{varyant.varyasyon_adi} başarıyla güncellendi!'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Hata oluştu: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Geçersiz istek!'})


@login_required
def varyant_sil(request, varyant_id):
    """Varyant silme"""
    varyant = get_object_or_404(UrunVaryanti, id=varyant_id)
    
    if request.method == 'POST':
        try:
            varyasyon_adi = varyant.varyasyon_adi
            varyant.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'{varyasyon_adi} varyantı silindi!'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Hata oluştu: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Geçersiz istek!'})


@login_required
def varyant_toplu_stok_guncelle(request, urun_id):
    """Tüm varyantlar için toplu stok güncelleme - sadece henüz kaydedilmemiş varyantlar"""
    from .models import StokHareket
    urun = get_object_or_404(Urun, id=urun_id)
    
    if request.method == 'POST':
        try:
            updated_count = 0
            skipped_count = 0
            
            with transaction.atomic():
                for key, value in request.POST.items():
                    if key.startswith('stok_'):
                        varyant_id = key.replace('stok_', '')
                        try:
                            varyant = UrunVaryanti.objects.get(id=varyant_id, urun=urun)
                            
                            # Sadece henüz kaydedilmemiş varyantları güncelle
                            if not varyant.stok_kaydedildi:
                                yeni_stok_miktari = int(value) if value else 0
                                eski_stok = varyant.stok_miktari
                                
                                # İlk stok girişi ise stok hareketi oluştur
                                if yeni_stok_miktari > 0:
                                    StokHareket.stok_hareketi_olustur(
                                        varyant=varyant,
                                        hareket_tipi='giris',
                                        miktar=yeni_stok_miktari,
                                        kullanici=request.user,
                                        aciklama=f'İlk stok girişi - {varyant.varyasyon_adi}',
                                        referans_id=f'ilk_stok_{varyant.id}'
                                    )
                                
                                varyant.stok_kaydedildi = True  # Artık kaydedildi olarak işaretle
                                updated_count += 1
                            else:
                                skipped_count += 1
                                
                        except (UrunVaryanti.DoesNotExist, ValueError):
                            continue
            
            message = f'{updated_count} varyant stoku güncellendi!'
            if skipped_count > 0:
                message += f' ({skipped_count} varyant zaten kaydedilmiş olduğu için atlandı)'
            
            return JsonResponse({
                'success': True,
                'message': message
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Hata oluştu: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Geçersiz istek!'})
