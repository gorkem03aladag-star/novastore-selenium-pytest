import time
from pathlib import Path
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config_oku import ayarlari_yukle

# Ekranda adımları gözle takip etmek için bekleme süresi (saniye). Eski hız için 0 yap.
HIZ = 1.5


def bekle(saniye=HIZ):
    if saniye > 0:
        time.sleep(saniye)


@pytest.fixture
def tarayici():
    ayarlar = ayarlari_yukle()
    tarayici_adi = ayarlar.get("browser", "chrome").strip().lower()
    magaza_url = ayarlar.get("magaza_url", "").strip()

    if tarayici_adi == "chrome":
        driver = webdriver.Chrome()
    elif tarayici_adi == "edge":
        driver = webdriver.Edge()
    elif tarayici_adi == "firefox":
        driver = webdriver.Firefox()
    else:
        raise ValueError(f"Desteklenmeyen tarayıcı: {tarayici_adi}")

    driver.maximize_window()
    if magaza_url:
        driver.get(magaza_url)
    else:
        html_dosyasi = Path(__file__).parent / "demo_magaza_v2.html"
        if not html_dosyasi.exists():
            html_dosyasi = Path(__file__).parent / "demo_magaza.html"
        driver.get(html_dosyasi.resolve().as_uri())

    yield driver
    driver.quit()


def giris_yap(driver, wait, kullanici="demo_kullanici", sifre="Test1234!"):
    wait.until(EC.presence_of_element_located((By.ID, "username"))).clear()
    driver.find_element(By.ID, "username").send_keys(kullanici)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(sifre)
    driver.find_element(By.ID, "loginBtn").click()
    wait.until(EC.visibility_of_element_located((By.ID, "hosgeldinMesaji")))
    bekle()


def test_kategori_ve_arama_filtreleme(tarayici):
    wait = WebDriverWait(tarayici, 10)
    giris_yap(tarayici, wait)

    tarayici.find_element(By.CSS_SELECTOR, "button.nav-btn[data-kategori='Çevre Birimleri']").click()
    bekle()
    filtre_metni = tarayici.find_element(By.ID, "filtreBilgisi").text
    assert "Çevre Birimleri" in filtre_metni

    kartlar = tarayici.find_elements(By.CSS_SELECTOR, "#urunListesi .urun-kart")
    assert len(kartlar) == 2

    arama_input = tarayici.find_element(By.ID, "aramaInput")
    arama_input.clear()
    arama_input.send_keys("OlmayanUrunXYZ")
    tarayici.find_element(By.ID, "aramaBtn").click()
    bekle()

    bulunamadi = wait.until(EC.visibility_of_element_located((By.ID, "urunBulunamadi"))).text
    assert "bulunamadı" in bulunamadi.lower()

    tarayici.find_element(By.ID, "filtreSifirlaBtn").click()
    bekle()
    tum_kartlar = tarayici.find_elements(By.CSS_SELECTOR, "#urunListesi .urun-kart")
    assert len(tum_kartlar) == 5


def test_sepet_adet_kupon_ve_3d_odeme(tarayici):
    wait = WebDriverWait(tarayici, 10)
    giris_yap(tarayici, wait)

    tarayici.find_element(By.CSS_SELECTOR, "button.sepete-ekle[data-ad='Kablosuz Kulaklık']").click()
    bekle()
    assert tarayici.find_element(By.ID, "sepetSayaci").text == "1"

    tarayici.find_element(By.ID, "sepetGitBtn").click()
    wait.until(EC.visibility_of_element_located((By.ID, "sepetIcerik")))
    bekle()

    tarayici.find_element(By.CSS_SELECTOR, ".sepet-satir .adet-artir").click()
    bekle()
    assert tarayici.find_element(By.ID, "araToplam").text == "3000"
    assert tarayici.find_element(By.ID, "genelToplam").text == "3000"

    tarayici.find_element(By.ID, "kuponInput").send_keys("INDIRIM10")
    tarayici.find_element(By.ID, "kuponUygulaBtn").click()
    bekle()
    assert tarayici.find_element(By.ID, "indirimTutari").text == "300"
    assert tarayici.find_element(By.ID, "genelToplam").text == "2700"

    tarayici.find_element(By.ID, "sepetOnaylaBtn").click()
    wait.until(EC.visibility_of_element_located((By.ID, "adresAdSoyad"))).send_keys("Görkem Test")
    tarayici.find_element(By.ID, "adresIl").send_keys("İstanbul / Kadıköy")
    tarayici.find_element(By.ID, "adresDetay").send_keys("Örnek Mah. Test Cad. No:12")
    bekle()
    tarayici.find_element(By.ID, "adresDevamBtn").click()
    bekle()

    wait.until(EC.visibility_of_element_located((By.ID, "kartNo"))).send_keys("4543 0000 0000 1234")
    tarayici.find_element(By.ID, "kartSonKullanma").send_keys("12/29")
    tarayici.find_element(By.ID, "kartCvv").send_keys("123")
    bekle()
    tarayici.find_element(By.ID, "odeme3DBtn").click()
    bekle()

    wait.until(EC.visibility_of_element_located((By.ID, "kod3D"))).send_keys("123456")
    tarayici.find_element(By.ID, "siparisiTamamlaBtn").click()
    bekle()

    ozet = wait.until(EC.visibility_of_element_located((By.ID, "siparisOzeti"))).text
    assert "Görkem Test" in ozet
    assert "Kablosuz Kulaklık (x2)" in ozet
    assert "2700 TL" in ozet


def test_gecersiz_kupon_ve_hatali_3d(tarayici):
    wait = WebDriverWait(tarayici, 10)
    giris_yap(tarayici, wait)

    tarayici.find_element(By.CSS_SELECTOR, "button.sepete-ekle[data-ad='Kablosuz Mouse']").click()
    tarayici.find_element(By.ID, "sepetGitBtn").click()
    bekle()

    tarayici.find_element(By.ID, "kuponInput").send_keys("SAHTE_KUPON")
    tarayici.find_element(By.ID, "kuponUygulaBtn").click()
    bekle()
    kupon_mesaj = wait.until(EC.visibility_of_element_located((By.ID, "kuponMesaj"))).text
    assert "Geçersiz indirim kodu!" in kupon_mesaj

    tarayici.find_element(By.ID, "sepetOnaylaBtn").click()
    wait.until(EC.visibility_of_element_located((By.ID, "adresAdSoyad"))).send_keys("Test Kullanıcı")
    tarayici.find_element(By.ID, "adresIl").send_keys("Ankara")
    tarayici.find_element(By.ID, "adresDetay").send_keys("Deneme Sok. No:1")
    bekle()
    tarayici.find_element(By.ID, "adresDevamBtn").click()
    bekle()

    wait.until(EC.visibility_of_element_located((By.ID, "kartNo"))).send_keys("4543 0000 0000 1234")
    tarayici.find_element(By.ID, "kartSonKullanma").send_keys("12/29")
    tarayici.find_element(By.ID, "kartCvv").send_keys("123")
    bekle()
    tarayici.find_element(By.ID, "odeme3DBtn").click()
    bekle()

    wait.until(EC.visibility_of_element_located((By.ID, "kod3D"))).send_keys("000000")
    tarayici.find_element(By.ID, "siparisiTamamlaBtn").click()
    bekle()

    hata_3d = wait.until(EC.visibility_of_element_located((By.ID, "hata3D"))).text
    assert "3D doğrulama kodu hatalı!" in hata_3d


def test_bos_sepet_onaylanamaz(tarayici):
    wait = WebDriverWait(tarayici, 10)
    giris_yap(tarayici, wait)

    tarayici.find_element(By.ID, "sepetGitBtn").click()
    wait.until(EC.visibility_of_element_located((By.ID, "sepetIcerik")))
    bekle()
    tarayici.find_element(By.ID, "sepetOnaylaBtn").click()
    bekle()

    hata = wait.until(EC.visibility_of_element_located((By.ID, "sepetHata"))).text
    assert "Sepet boşken onaylanamaz!" in hata


def test_sepet_adet_azaltma_silme_ve_cikis(tarayici):
    wait = WebDriverWait(tarayici, 10)
    giris_yap(tarayici, wait)

    tarayici.find_element(By.CSS_SELECTOR, "button.sepete-ekle[data-ad='Mekanik Klavye']").click()
    tarayici.find_element(By.ID, "sepetGitBtn").click()
    wait.until(EC.visibility_of_element_located((By.ID, "sepetIcerik")))
    bekle()

    tarayici.find_element(By.CSS_SELECTOR, ".sepet-satir .adet-artir").click()
    bekle()
    assert tarayici.find_element(By.ID, "genelToplam").text == "4400"

    tarayici.find_element(By.CSS_SELECTOR, ".sepet-satir .adet-azalt").click()
    bekle()
    assert tarayici.find_element(By.ID, "genelToplam").text == "2200"

    tarayici.find_element(By.CSS_SELECTOR, ".sepet-satir .urun-sil").click()
    bekle()
    assert tarayici.find_element(By.ID, "sepetSayaci").text == "0"
    assert tarayici.find_element(By.ID, "genelToplam").text == "0"

    tarayici.find_element(By.ID, "cikisBtn").click()
    bekle()
    assert wait.until(EC.visibility_of_element_located((By.ID, "loginBtn"))).is_displayed()


def test_eksik_adres_ve_kart_bilgisi_hatalari(tarayici):
    wait = WebDriverWait(tarayici, 10)
    giris_yap(tarayici, wait)

    tarayici.find_element(By.CSS_SELECTOR, "button.sepete-ekle[data-ad='USB-C Çoklayıcı Hub']").click()
    tarayici.find_element(By.ID, "sepetGitBtn").click()
    wait.until(EC.element_to_be_clickable((By.ID, "sepetOnaylaBtn"))).click()
    bekle()

    wait.until(EC.visibility_of_element_located((By.ID, "adresAdSoyad"))).send_keys("Görkem")
    tarayici.find_element(By.ID, "adresDevamBtn").click()
    bekle()
    adres_hata = wait.until(EC.visibility_of_element_located((By.ID, "adresHata"))).text
    assert "Tüm adres alanlarını doldurun!" in adres_hata

    tarayici.find_element(By.ID, "adresIl").send_keys("İstanbul")
    tarayici.find_element(By.ID, "adresDetay").send_keys("Test Sokak No:5")
    tarayici.find_element(By.ID, "adresDevamBtn").click()
    bekle()

    wait.until(EC.visibility_of_element_located((By.ID, "kartNo"))).send_keys("4543 0000 0000 1234")
    tarayici.find_element(By.ID, "odeme3DBtn").click()
    bekle()
    kart_hata = wait.until(EC.visibility_of_element_located((By.ID, "kartHata"))).text
    assert "Kart bilgilerini eksiksiz girin!" in kart_hata


@pytest.mark.parametrize(
    "kullanici,sifre",
    [
        ("demo_kullanici", "YanlisSifre999"),
        ("yanlis_kullanici", "Test1234!"),
        ("", "Test1234!"),
    ],
)
def test_hatali_giris_senaryolari(tarayici, kullanici, sifre):
    wait = WebDriverWait(tarayici, 10)

    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(kullanici)
    tarayici.find_element(By.ID, "password").send_keys(sifre)
    tarayici.find_element(By.ID, "loginBtn").click()
    bekle()

    hata = wait.until(EC.visibility_of_element_located((By.ID, "loginMesaj"))).text
    assert "Hatalı kullanıcı adı veya şifre!" in hata


def test_basarili_giris(tarayici):
    wait = WebDriverWait(tarayici, 10)

    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys("demo_kullanici")
    tarayici.find_element(By.ID, "password").send_keys("Test1234!")
    tarayici.find_element(By.ID, "loginBtn").click()
    bekle()

    hosgeldin = wait.until(EC.visibility_of_element_located((By.ID, "hosgeldinMesaji"))).text
    assert "Hoş geldiniz, demo_kullanici!" in hosgeldin

    aktif_bar = tarayici.find_element(By.ID, "aktifKullaniciBar").text
    assert "demo_kullanici" in aktif_bar

    assert tarayici.find_element(By.ID, "cikisBtn").is_displayed()
    assert len(tarayici.find_elements(By.CSS_SELECTOR, "#urunListesi .urun-kart")) == 5


def test_urun_gorselleri_ve_fiyat_siralama(tarayici):
    wait = WebDriverWait(tarayici, 10)
    giris_yap(tarayici, wait)

    gorseller = tarayici.find_elements(By.CSS_SELECTOR, "#urunListesi .urun-kart img")
    assert len(gorseller) == 5
    for img in gorseller:
        assert img.is_displayed()
        assert img.get_attribute("alt").strip() != ""

    siralama_kutu = tarayici.find_element(By.ID, "siralamaSelect")
    siralama_kutu.click()
    siralama_kutu.find_element(By.CSS_SELECTOR, "option[value='fiyat-artan']").click()
    bekle()

    basliklar = [el.text for el in tarayici.find_elements(By.CSS_SELECTOR, "#urunListesi .urun-baslik")]
    assert basliklar[0] == "USB-C Çoklayıcı Hub"
    assert basliklar[-1] == "Mekanik Klavye"


def test_kargo_esigi_2000_tl_hesabi(tarayici):
    wait = WebDriverWait(tarayici, 10)
    giris_yap(tarayici, wait)

    tarayici.find_element(By.CSS_SELECTOR, "button.sepete-ekle[data-ad='Kablosuz Kulaklık']").click()
    tarayici.find_element(By.ID, "sepetGitBtn").click()
    wait.until(EC.visibility_of_element_located((By.ID, "sepetIcerik")))
    bekle()

    assert tarayici.find_element(By.ID, "araToplam").text == "1500"
    assert tarayici.find_element(By.ID, "kargoUcreti").text == "99"
    assert tarayici.find_element(By.ID, "kargoDurumu").text == "Standart Kargo"
    assert tarayici.find_element(By.ID, "genelToplam").text == "1599"

    tarayici.find_element(By.CSS_SELECTOR, ".sepet-satir .adet-artir").click()
    bekle()

    assert tarayici.find_element(By.ID, "araToplam").text == "3000"
    assert tarayici.find_element(By.ID, "kargoUcreti").text == "0"
    assert tarayici.find_element(By.ID, "kargoDurumu").text == "Ücretsiz"
    assert tarayici.find_element(By.ID, "genelToplam").text == "3000"


def test_siparis_gecmisi_kaydi_ve_goruntulenmesi(tarayici):
    wait = WebDriverWait(tarayici, 10)
    giris_yap(tarayici, wait)

    tarayici.find_element(By.CSS_SELECTOR, "button.sepete-ekle[data-ad='Mekanik Klavye']").click()
    tarayici.find_element(By.ID, "sepetGitBtn").click()
    wait.until(EC.element_to_be_clickable((By.ID, "sepetOnaylaBtn"))).click()
    bekle()

    wait.until(EC.visibility_of_element_located((By.ID, "adresAdSoyad"))).send_keys("Görkem Sipariş")
    tarayici.find_element(By.ID, "adresIl").send_keys("İstanbul / Üsküdar")
    tarayici.find_element(By.ID, "adresDetay").send_keys("Bağlarbaşı Cad. No:8")
    tarayici.find_element(By.ID, "adresDevamBtn").click()
    bekle()

    wait.until(EC.visibility_of_element_located((By.ID, "kartNo"))).send_keys("4543 0000 0000 1234")
    tarayici.find_element(By.ID, "kartSonKullanma").send_keys("12/29")
    tarayici.find_element(By.ID, "kartCvv").send_keys("123")
    tarayici.find_element(By.ID, "odeme3DBtn").click()
    bekle()

    wait.until(EC.visibility_of_element_located((By.ID, "kod3D"))).send_keys("123456")
    tarayici.find_element(By.ID, "siparisiTamamlaBtn").click()
    bekle()

    wait.until(EC.visibility_of_element_located((By.ID, "onaydanSiparislerimeGitBtn"))).click()
    bekle()

    gecmis_metni = wait.until(EC.visibility_of_element_located((By.ID, "siparisGecmisListesi"))).text
    assert "NV-" in gecmis_metni
    assert "Görkem Sipariş" in gecmis_metni
    assert "Mekanik Klavye (x1)" in gecmis_metni