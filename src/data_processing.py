"""
Veri yükleme, temizleme ve dönüştürme işlemleri için fonksiyonlar.
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import logging

# Konfigürasyon dosyasını içe aktar
from config.tezgah_listesi import KISIMLAR_DICT

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def assign_kisim(makina_kodu: str) -> str:
    """
    Makina koduna göre kısım atar.
    
    Args:
        makina_kodu: Makina kodu
        
    Returns:
        str: Kısım adı
    """
    for kisim, tezgahlar in KISIMLAR_DICT.items():
        if makina_kodu in tezgahlar:
            return kisim
    return "Diğer"

def load_durus_data(file_path: str) -> pd.DataFrame:
    """
    Duruş verilerini yükler.
    
    Args:
        file_path: Excel dosyasının yolu
        
    Returns:
        pd.DataFrame: Yüklenmiş veri
    """
    try:
        logger.info(f"Duruş verisi yükleniyor: {file_path}")
        df = pd.read_excel(
            file_path, 
            usecols=["İş Merkezi Kodu ", "Duruş Adı", "Duruş Başlangıç Tarih", "Duruş Bitiş Tarih"]
        )
        logger.info(f"Duruş verisi yüklendi. Satır sayısı: {len(df)}")
        return df
    except Exception as e:
        logger.error(f"Veri yükleme hatası: {str(e)}")
        raise

def load_calisma_data(file_path: str) -> pd.DataFrame:
    """
    Çalışma süresi verilerini yükler.
    
    Args:
        file_path: Excel dosyasının yolu
        
    Returns:
        pd.DataFrame: Yüklenmiş veri
    """
    try:
        logger.info(f"Çalışma süresi verisi yükleniyor: {file_path}")
        df = pd.read_excel(
            file_path, 
            usecols=["Makina Kodu", "Tarih", "Çalışma Zamanı", "Planlı Duruş",
                    "Plansız Duruş", "Oee", "Performans", "Kullanılabilirlik", "Kalite"]
        )
        logger.info(f"Çalışma süresi verisi yüklendi. Satır sayısı: {len(df)}")
        return df
    except Exception as e:
        logger.error(f"Veri yükleme hatası: {str(e)}")
        raise

def load_arizali_tezgahlar(file_path: str) -> List[str]:
    """
    Arızalı tezgah listesini dosyadan yükler.
    
    Args:
        file_path: Arızalı tezgahların bulunduğu dosya yolu
        
    Returns:
        List[str]: Arızalı tezgah kodları listesi
    """
    try:
        logger.info(f"Arızalı tezgah listesi yükleniyor: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            arizali_tezgahlar = f.read().strip().split("\n")
        logger.info(f"Arızalı tezgah listesi yüklendi. Tezgah sayısı: {len(arizali_tezgahlar)}")
        return arizali_tezgahlar
    except Exception as e:
        logger.error(f"Arızalı tezgah listesi yükleme hatası: {str(e)}")
        return []

def clean_last_rows(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Son satırlardaki verileri temizler (tezgahlara ait olmayan girişleri kaldırır).
    
    Args:
        df: Temizlenecek DataFrame
        column_name: Kontrol edilecek sütun adı
        
    Returns:
        pd.DataFrame: Temizlenmiş DataFrame
    """
    # Orijinal DataFrame'i değiştirmemek için kopyasını oluştur
    cleaned_df = df.copy()
    
    for _ in range(5):  # En fazla 5 kez kontrol et
        if len(cleaned_df) == 0:
            break
            
        tezgah = cleaned_df[column_name].iloc[-1]
        found = False
        
        for kisim_tezgahlar in KISIMLAR_DICT.values():
            if tezgah in kisim_tezgahlar:
                found = True
                break
                
        if not found:
            cleaned_df = cleaned_df.iloc[:-1]
        else:
            break  # Son satır geçerliyse döngüden çık
    
    rows_removed = len(df) - len(cleaned_df)
    if rows_removed > 0:
        logger.info(f"{rows_removed} geçersiz satır temizlendi.")
    
    return cleaned_df

def calculate_durations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Duruş başlangıç ve bitiş tarihlerine göre süreleri hesaplar.
    
    Args:
        df: İşlenecek DataFrame
        
    Returns:
        pd.DataFrame: Süre sütunları eklenmiş DataFrame
    """
    # Orijinal DataFrame'i değiştirmemek için kopyasını oluştur
    result_df = df.copy()
    
    # Tarih sütunlarını datetime formatına dönüştür
    result_df['Duruş Başlangıç Tarih'] = pd.to_datetime(result_df['Duruş Başlangıç Tarih'])
    result_df['Duruş Bitiş Tarih'] = pd.to_datetime(result_df['Duruş Bitiş Tarih'])
    
    # Saniye farkını hesapla
    result_df['Süre (Saniye)'] = (
        result_df['Duruş Bitiş Tarih'] - result_df['Duruş Başlangıç Tarih']
    ).dt.total_seconds().astype(int)
    
    # Dakika farkını hesapla
    result_df['Süre (Dakika)'] = (result_df['Süre (Saniye)'] / 60).astype(int)
    
    return result_df

def process_calisma_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Çalışma süresi verilerini işler.
    
    Args:
        df: İşlenecek çalışma süresi DataFrame'i
        
    Returns:
        pd.DataFrame: İşlenmiş DataFrame
    """
    # Orijinal DataFrame'i değiştirmemek için kopyasını oluştur
    result_df = df.copy()
    
    # Çalışma süresi hesapla
    result_df['Süre (Dakika)'] = (
        result_df['Çalışma Zamanı'] - result_df['Planlı Duruş'] - result_df['Plansız Duruş']
    ).astype(int)
    
    # Sütun isimlerini standardize et
    result_df = result_df.rename(columns={
        'Tarih': 'Duruş Başlangıç Tarih',
        'Makina Kodu': 'İş Merkezi Kodu '
    })
    
    # Çalışma süresi sütununu ekle
    result_df['Duruş Adı'] = "ÇALIŞMA SÜRESİ"
    
    # Sadece gerekli sütunları seç
    columns_to_keep = [
        'İş Merkezi Kodu ', 'Duruş Adı', 'Duruş Başlangıç Tarih', 
        'Süre (Dakika)', 'Oee', 'Performans', 'Kullanılabilirlik', 'Kalite'
    ]
    result_df = result_df[columns_to_keep]
    
    return result_df

def add_week_info(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame'e hafta bilgisini ekler.
    """
    # Orijinal DataFrame'i değiştirmemek için kopyasını oluştur
    result_df = df.copy()
    
    # NaN değerlerini filtrele
    result_df = result_df.dropna(subset=['Duruş Başlangıç Tarih'])
    
    # Tarih sütununu datetime formatına dönüştür (eğer değilse)
    if not pd.api.types.is_datetime64_any_dtype(result_df['Duruş Başlangıç Tarih']):
        try:
            # Farklı tarih formatlarını deneyerek dönüştürmeyi dene
            result_df['Duruş Başlangıç Tarih'] = pd.to_datetime(
                result_df['Duruş Başlangıç Tarih'], 
                errors='coerce',
                format=None  # Otomatik format algılama
            )
            # NaN oluşmuş satırları temizle
            result_df = result_df.dropna(subset=['Duruş Başlangıç Tarih'])
        except Exception as e:
            logger.error(f"Tarih dönüşümü hatası: {str(e)}")
    
    # Hafta bilgisini ekle
    try:
        result_df['Hafta'] = result_df['Duruş Başlangıç Tarih'].dt.isocalendar().week
        # Yıl bilgisini de ekleyelim, farklı yıllar varsa hafta numaraları karışabilir
        result_df['Yıl'] = result_df['Duruş Başlangıç Tarih'].dt.isocalendar().year
        # Yıl-Hafta birleşik anahtarı oluştur
        result_df['YılHafta'] = result_df['Yıl'].astype(str) + "-" + result_df['Hafta'].astype(str)
    except Exception as e:
        logger.error(f"Hafta hesaplama hatası: {str(e)}")
        # Basit bir çözüm olarak varsayılan değer ata
        result_df['Hafta'] = 1
        result_df['YılHafta'] = "0000-1"
    
    return result_df

def filter_by_arizali_tezgahlar(
    df: pd.DataFrame, 
    arizali_tezgahlar: List[str], 
    machine_col: str = 'İş Merkezi Kodu '
) -> pd.DataFrame:
    """
    Arızalı tezgahları veri setinden filtreler.
    
    Args:
        df: Filtrelenecek DataFrame
        arizali_tezgahlar: Arızalı tezgah kodları listesi
        machine_col: Makine kodu sütunu adı
        
    Returns:
        pd.DataFrame: Filtrelenmiş DataFrame
    """
    # Orijinal DataFrame'i değiştirmemek için kopyasını oluştur
    result_df = df.copy()
    
    if arizali_tezgahlar:
        logger.info(f"{len(arizali_tezgahlar)} arızalı tezgah filtreleniyor.")
        result_df = result_df[~result_df[machine_col].isin(arizali_tezgahlar)]
        logger.info(f"Filtreleme sonrası satır sayısı: {len(result_df)}")
    
    return result_df

def merge_durus_calisma_data(
    durus_df: pd.DataFrame, 
    calisma_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Duruş ve çalışma verilerini birleştirir.
    
    Args:
        durus_df: Duruş verileri DataFrame'i
        calisma_df: Çalışma verileri DataFrame'i
        
    Returns:
        pd.DataFrame: Birleştirilmiş DataFrame
    """
    # Tarih formatlarını standardize et (sadece tarih, saat olmadan)
    durus_df['Duruş Başlangıç Tarih'] = pd.to_datetime(durus_df['Duruş Başlangıç Tarih']).dt.date
    calisma_df['Duruş Başlangıç Tarih'] = pd.to_datetime(calisma_df['Duruş Başlangıç Tarih']).dt.date
    
    # Duruş verilerindeki eşsiz tarih ve makine kodlarını al
    unique_dates = durus_df['Duruş Başlangıç Tarih'].unique()
    unique_machines = durus_df['İş Merkezi Kodu '].unique()
    
    # Çalışma verilerini filtrele
    filtered_calisma = calisma_df[
        (calisma_df['Duruş Başlangıç Tarih'].isin(unique_dates)) & 
        (calisma_df['İş Merkezi Kodu '].isin(unique_machines))
    ]
    
    # Verileri birleştir
    merged_df = pd.concat([durus_df, filtered_calisma], ignore_index=True)
    
    # Süre değeri 0 olan veya NaN olan satırları filtrele
    merged_df = merged_df[(merged_df['Süre (Dakika)'] != 0) & (merged_df['Süre (Dakika)'].notna())]
    
    # ÇALIŞMA SÜRESİ kayıtları için eksik saniye değerlerini hesapla
    mask = (merged_df['Duruş Adı'] == 'ÇALIŞMA SÜRESİ') & (merged_df['Süre (Saniye)'].isna())
    merged_df.loc[mask, 'Süre (Saniye)'] = merged_df.loc[mask, 'Süre (Dakika)'] * 60
    
    return merged_df

def prepare_data_for_analysis(
    durus_file: str,
    calisma_file: str,
    arizali_file: str = None
) -> Tuple[pd.DataFrame, Dict, List[int]]:
    """
    Analiz için veri setini hazırlar.
    """
    logger.info("Veri hazırlama işlemi başlıyor...")
    
    try:
        # Duruş verilerini yükle
        durus_df = load_durus_data(durus_file)
        logger.info(f"Duruş verileri yüklendi. Satır sayısı: {len(durus_df)}")
        
        # Gerekli sütunları kontrol et
        required_columns = ["İş Merkezi Kodu ", "Duruş Adı", "Duruş Başlangıç Tarih", "Duruş Bitiş Tarih"]
        for col in required_columns:
            if col not in durus_df.columns:
                logger.error(f"Gerekli sütun bulunamadı: {col}")
                raise ValueError(f"Duruş verilerinde gerekli sütun bulunamadı: {col}")
        
        # Son satırları temizle
        durus_df = clean_last_rows(durus_df, "İş Merkezi Kodu ")
        
        # Süreleri hesapla
        durus_df = calculate_durations(durus_df)
        
        # Çalışma verilerini yükle
        calisma_df = load_calisma_data(calisma_file)
        logger.info(f"Çalışma verileri yüklendi. Satır sayısı: {len(calisma_df)}")
        
        # Son satırları temizle
        calisma_df = clean_last_rows(calisma_df, "Makina Kodu")
        
        # Çalışma verilerini işle
        calisma_df = process_calisma_data(calisma_df)
        
        # Arızalı tezgahları yükle (varsa)
        arizali_tezgahlar = []
        if arizali_file and os.path.exists(arizali_file) and os.path.getsize(arizali_file) > 0:
            arizali_tezgahlar = load_arizali_tezgahlar(arizali_file)
        
        # Arızalı tezgahları filtrele
        durus_df = filter_by_arizali_tezgahlar(durus_df, arizali_tezgahlar)
        calisma_df = filter_by_arizali_tezgahlar(calisma_df, arizali_tezgahlar)
        
        # Verileri birleştir
        merged_df = merge_durus_calisma_data(durus_df, calisma_df)
        logger.info(f"Veriler birleştirildi. Satır sayısı: {len(merged_df)}")
        
        # Kısım bilgisini ekle
        merged_df['KISIM'] = merged_df['İş Merkezi Kodu '].apply(assign_kisim)
        
        # Hafta bilgisini ekle (hata ayıklama bilgileriyle)
        merged_df = add_week_info(merged_df)
        logger.info(f"Hafta bilgisi eklendi. Benzersiz hafta sayısı: {merged_df['Hafta'].nunique()}")
        
        # Hafta numaralarını al ve sırala (son hafta ilk sırada)
        weeks = sorted(merged_df['Hafta'].unique(), key=lambda x: (x < 10, x), reverse=True)
        logger.info(f"Sıralanmış hafta listesi: {weeks}")
        
        # Arızalı tezgahlardan etkilenen kısımlar için tezgah sayılarını güncelle
        kisim_tezgah_sayilari = {}
        for kisim, tezgahlar in KISIMLAR_DICT.items():
            kisim_tezgah_sayilari[kisim] = len([t for t in tezgahlar if t not in arizali_tezgahlar])
        
        logger.info("Veri hazırlama işlemi tamamlandı.")
        return merged_df, kisim_tezgah_sayilari, weeks
        
    except Exception as e:
        logger.error(f"Veri hazırlama hatası: {str(e)}", exc_info=True)
        # Boş veri döndürmek yerine hata fırlat
        raise

def get_latest_week_data(df: pd.DataFrame, weeks: List[int]) -> pd.DataFrame:
    """
    En son haftaya ait veriyi filtreler.
    
    Args:
        df: Tüm veri seti
        weeks: Sıralanmış hafta numaraları listesi (son hafta ilk sırada)
        
    Returns:
        pd.DataFrame: Son haftaya ait filtrelenmiş veri
    """
    if not weeks:
        logger.warning("Hafta bilgisi bulunamadı!")
        return pd.DataFrame()
        
    latest_week = weeks[0]  # Sıralanmış listenin ilk elemanı son haftadır
    logger.info(f"Son hafta verisi filtreleniyor: Hafta {latest_week}")
    
    latest_week_df = df[df['Hafta'] == latest_week]
    logger.info(f"Son hafta satır sayısı: {len(latest_week_df)}")
    
    return latest_week_df