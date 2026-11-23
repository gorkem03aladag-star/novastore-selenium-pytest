# NovaStore — E-Ticaret Web Test Otomasyon Projesi (Selenium + pytest)

Bu proje, özel olarak geliştirilmiş **NovaStore** e-ticaret arayüzü (`demo_magaza_v2.html`) üzerinde **Python**, **Selenium WebDriver** ve **`pytest`** kullanılarak oluşturulmuş uçtan uca (E2E) ve fonksiyonel web test otomasyonu çalışmasıdır.

Çalışmada yalnızca "mutlu yol" (happy path) senaryoları değil; sınır değerler, negatif durumlar, form/iş kuralı doğrulamaları, dinamik bekleme mekanizmaları (`WebDriverWait` + `expected_conditions`) ve `pytest-html` ile okunabilir HTML test raporlaması ele alınmıştır.

---

## Proje Yapısı

- `test_novastore_v2.py`: `pytest` fixture'ları, parametreli veri setleri ve 13 ayrı test senaryosunu içeren ana test dosyası.
- `demo_magaza_v2.html`: Giriş, kategori/arama filtreleme, sıralama, sepet, kupon, kargo eşiği, adres, kart, 3D Secure ödeme ve `localStorage` tabanlı *Siparişlerim* akışlarını barındıran e-ticaret arayüzü.
- `config.ini` & `config_oku.py`: Tarayıcı seçimi ve hedef sayfa/URL ayarlarını merkezi olarak yöneten yapılandırma modülü.

## Uygulama Tarafında Kapsanan İş Kuralları (`demo_magaza_v2.html`)

- **Kimlik Doğrulama & Oturum:** Kullanıcı girişi, çıkış işlemi, sepetin sıfırlanması ve oturumsuz kullanıcıların kritik ekranlara yönlendirilmesi.
- **Katalog, Arama, Filtreleme & Sıralama:** Kategori bazlı filtreleme, metin araması, eşleşmeyen sonuç uyarısı, filtre sıfırlama, ürün görsellerinin (`<img>`) görünürlüğü ve fiyata göre sıralama.
- **Sepet & Kargo Eşiği (`2000 TL`):** Adet artırma/azaltma, ürün silme, boş sepet onay engeli ve `2000 TL` altındaki tutarlarda standart kargo (`99 TL`), `2000 TL` ve üzerindeyse ücretsiz kargo (`0 TL`) hesaplaması.
- **Kupon & 3D Secure Ödeme:** `INDIRIM10` (%10 indirim) kupon kontrolü, geçersiz kupon uyarısı, eksik adres/kart alanı kontrolleri ve 6 haneli 3D doğrulama kodu (`123456`) ile sipariş oluşturma.
- **Sipariş Geçmişi (`localStorage`):** Tamamlanan siparişlerin `NV-` ön ekli sipariş numarasıyla tarayıcı belleğine kaydedilmesi ve *Siparişlerim* ekranında listelenmesi.

## Yazılan Test Senaryoları (`13 Test`)

| # | Test Fonksiyonu | Ne Test Ediyor? | Beklenen Sonuç |
| :- | :--- | :--- | :--- |
| 1 | `test_kategori_ve_arama_filtreleme` | Kategori seçimi (`Çevre Birimleri`), olmayan ürün araması ve filtre sıfırlama | İlgili 2 ürün listelenir, olmayan aramada uyarı çıkar, sıfırlamada 5 ürün döner |
| 2 | `test_sepet_adet_kupon_ve_3d_odeme` | Ürün ekleme, adet artırma, `INDIRIM10` kuponu, adres, kart ve 3D onay akışı | İndirim ve genel toplam doğru hesaplanır, sipariş özeti ekranda görünür |
| 3 | `test_gecersiz_kupon_ve_hatali_3d` | Geçersiz kupon (`SAHTE_KUPON`) ve hatalı 3D kodu (`000000`) | Geçersiz kupon ve hatalı 3D doğrulama mesajları görüntülenir |
| 4 | `test_bos_sepet_onaylanamaz` | Sepette ürün yokken *Sepeti Onayla* butonuna basma | Sepetin boş olduğuna dair hata mesajı gösterilir |
| 5 | `test_sepet_adet_azaltma_silme_ve_cikis` | Adet artırma/azaltma, ürün silme ve *Çıkış Yap* akışı | Tutarlar güncellenir, silmede sayaç/toplam `0` olur, çıkışta giriş ekranı açılır |
| 6 | `test_eksik_adres_ve_kart_bilgisi_hatalari` | Eksik bırakılan adres ve kart alanlarıyla ilerleme denemeleri | İlgili form doğrulama hata mesajları tetiklenir |
| 7–9 | `test_hatali_giris_senaryolari` (`@pytest.mark.parametrize`) | Yanlış şifre, yanlış kullanıcı adı ve boş kullanıcı adı kombinasyonları | Her veri seti için hatalı giriş uyarısı doğrulanır |
| 10 | `test_basarili_giris` | Geçerli kullanıcı bilgileriyle oturum açma | Karşılama mesajı, kullanıcı bilgisi, çıkış butonu ve 5 ürün kartı doğrulanır |
| 11 | `test_urun_gorselleri_ve_fiyat_siralama` | 5 ürün görselinin görünürlüğü/`alt` metni ve artan fiyat sıralaması | Görseller görünür gelir, sıralamada en ucuz ve en pahalı ürün sırası doğrulanır |
| 12 | `test_kargo_esigi_2000_tl_hesabi` | `1500 TL` (eşik altı) ve `3000 TL` (eşik üstü) sepet tutarlarında kargo hesabı | `1500 TL`'de `99 TL` kargo (`1599 TL`), `3000 TL`'de `0 TL` ücretsiz kargo (`3000 TL`) |
| 13 | `test_siparis_gecmisi_kaydi_ve_goruntulenmesi` | Sipariş tamamlama sonrası *Siparişlerim* ekranına geçiş | `NV-` sipariş numarası, alıcı adı ve ürün özeti geçmişte listelenir |

---

## Kurulum ve Çalıştırma

1. Gerekli kütüphaneleri yükleyin:

```bash
pip install selenium pytest pytest-html
Testleri çalıştırın ve HTML rapor oluşturun: pytest -v test_novastore_v2.py --html=rapor.html --self-contained-html

