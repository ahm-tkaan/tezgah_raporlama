"""
Tezgah duruş analizi için genel ayarlar.
"""

# Dosya ve klasör yolları
DATA_PATHS = {
    "raw_data": "data/raw",
    "processed_data": "data/processed",
    "reports": "reports"
}

# Görselleştirme ayarları
VISUALIZATION_SETTINGS = {
    "dpi": 300,
    "default_figsize": (12, 8),
    "default_threshold": 3.0  # Pasta grafik için eşik değeri (%)
}

# Duruş kategorileri
STOP_CATEGORIES = {
    "yemek": ["YEMEK MOLASI"],
    "tasarim": ["TASARIM"],
    "ayar": ["SMED", "AYAR"],
    "ariza": ["ARIZA", "BOZULMA", "TAMIR"]
}

# Excel sütun isimleri (Orijinal dosyadan farklı olması durumunda)
COLUMN_MAPPINGS = {
    "makine_kodu": "İş Merkezi Kodu ",
    "durus_adi": "Duruş Adı",
    "baslangic_tarih": "Duruş Başlangıç Tarih",
    "bitis_tarih": "Duruş Bitiş Tarih"
}