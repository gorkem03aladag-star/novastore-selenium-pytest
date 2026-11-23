import configparser
from pathlib import Path

def ayarlari_yukle():
    dosya_yolu = Path(__file__).parent / "config.ini"
    if not dosya_yolu.exists():
        raise FileNotFoundError(f"Konfigürasyon dosyası bulunamadı: {dosya_yolu.resolve()}")

    parser = configparser.ConfigParser()
    parser.read(dosya_yolu, encoding="utf-8")
    return parser["ayarlar"]