"""
Duruş verileri ve tezgah performansları için hesaplama fonksiyonları.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import logging

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("calculations.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def second_to_minute(df: pd.DataFrame, second_col: str = "Süre (Saniye)", 
                    minute_col: str = "Süre (Dakika)") -> pd.DataFrame:
    """
    Saniye cinsinden verilen süreleri dakikaya çevirir.
    
    Args:
        df: İşlenecek DataFrame
        second_col: Saniye sütununun adı
        minute_col: Dakika sütununun adı
        
    Returns:
        pd.DataFrame: Dakika sütunu eklenmiş DataFrame
    """
    # Orijinal DataFrame'i değiştirmemek için kopyasını oluştur
    result_df = df.copy()
    
    # Saniyeyi dakikaya çevir
    result_df[minute_col] = (result_df[second_col] / 60).astype(int)
    
    return result_df

def calculate_stop_time_sum(df: pd.DataFrame) -> pd.DataFrame:
    """
    Duruş adlarına göre süreleri toplar ve benzer duruşları birleştirir.
    
    Args:
        df: İşlenecek DataFrame
        
    Returns:
        pd.DataFrame: Duruş sürelerinin toplamını içeren DataFrame
    """
    logger.info("Duruş süreleri hesaplanıyor...")
    
    # Duruş adlarına göre süreleri topla
    toplam_sureler = df.groupby("Duruş Adı")["Süre (Saniye)"].sum().reset_index()
    toplam_sureler = toplam_sureler.sort_values(by="Süre (Saniye)", ascending=False)

    # Farklı kategorilerde duruşları filtrele
    yemek_molasi = toplam_sureler[toplam_sureler['Duruş Adı'].str.contains("YEMEK MOLASI", case=False)]
    tasarim_duruslari = toplam_sureler[toplam_sureler['Duruş Adı'].str.contains("TASARIM", case=False)]
    smed_duruslari = toplam_sureler[toplam_sureler['Duruş Adı'].str.contains("SMED", case=False)]

    # Süreleri topla
    yemek_molasi_toplam = yemek_molasi['Süre (Saniye)'].sum()
    tasarim_duruslari_toplam = tasarim_duruslari['Süre (Saniye)'].sum()
    smed_duruslari_toplam = smed_duruslari['Süre (Saniye)'].sum()

    # Birleştirilmiş duruş satırları oluştur
    new_data = {
        'Duruş Adı': ['YEMEK MOLASI', 'TASARIM DURUŞLARI', 'AYAR'],
        'Süre (Saniye)': [yemek_molasi_toplam, tasarim_duruslari_toplam, smed_duruslari_toplam]
    }
    new_df = pd.DataFrame(new_data)

    # Yemek molası, tasarım ve SMED duruşlarının eski satırlarını sil
    toplam_sureler = toplam_sureler[
        ~toplam_sureler['Duruş Adı'].str.contains("YEMEK MOLASI|TASARIM|SMED", case=False)
    ]

    # Güncellenmiş DataFrame ile yeni satırları birleştir
    toplam_sureler = pd.concat([toplam_sureler, new_df], ignore_index=True)

    # Süreye göre büyükten küçüğe sırala
    toplam_sureler = toplam_sureler.sort_values(by="Süre (Saniye)", ascending=False).reset_index(drop=True)
    
    # Saniyeden dakikaya çevir
    toplam_sureler = second_to_minute(toplam_sureler)
    
    logger.info("Duruş süreleri hesaplaması tamamlandı.")
    return toplam_sureler

def calculate_part_machine_average_time(
    df: pd.DataFrame, 
    kisim_tezgah_sayilari: Dict[str, int]
) -> pd.DataFrame:
    """
    Kısımlara göre tek tezgah başına ortalama duruş sürelerini hesaplar.
    
    Args:
        df: İşlenecek DataFrame
        kisim_tezgah_sayilari: Kısımlara göre tezgah sayıları
        
    Returns:
        pd.DataFrame: Tezgah başına ortalama duruş sürelerini içeren DataFrame
    """
    logger.info("Kısım başına ortalama duruş süreleri hesaplanıyor...")
    
    # ÇALIŞMA SÜRESİ dışındaki duruşları filtreleme
    filtered_df = df[df["Duruş Adı"] != "ÇALIŞMA SÜRESİ"].copy()
    
    # Kısımlara göre toplam süreleri hesapla
    kisim_sureleri = filtered_df.groupby("KISIM")["Süre (Saniye)"].sum().reset_index()
    kisim_sureleri = kisim_sureleri.sort_values(by="KISIM", ascending=True)

    # KISIM değerlerini tezgah sayılarına bölerek güncelle
    for idx, row in kisim_sureleri.iterrows():
        if row["KISIM"] in kisim_tezgah_sayilari:
            tezgah_sayisi = kisim_tezgah_sayilari[row["KISIM"]]
            kisim_sureleri.at[idx, "Süre (Saniye)"] = row["Süre (Saniye)"] / tezgah_sayisi

    # Diğer satırı varsa sil
    kisim_sureleri = kisim_sureleri[kisim_sureleri['KISIM'] != 'Diğer']
    
    # Saniyeden dakikaya çevir
    kisim_sureleri = second_to_minute(kisim_sureleri)
    
    logger.info("Kısım başına ortalama duruş süreleri hesaplaması tamamlandı.")
    return kisim_sureleri

def calculate_machine_stop_times(df: pd.DataFrame) -> pd.DataFrame:
    """
    İş merkezlerinin toplam duruş sürelerini hesaplar.
    
    Args:
        df: İşlenecek DataFrame
        
    Returns:
        pd.DataFrame: İş merkezlerinin toplam duruş sürelerini içeren DataFrame
    """
    logger.info("Tezgah duruş süreleri hesaplanıyor...")
    
    # ÇALIŞMA SÜRESİ dışındaki duruşları filtreleme
    filtered_df = df[df['Duruş Adı'] != 'ÇALIŞMA SÜRESİ'].copy()
    
    # İş merkezi koduna göre toplam süreleri hesapla
    tezgah_sureleri = filtered_df.groupby("İş Merkezi Kodu ")["Süre (Saniye)"].sum().reset_index()
    
    # Saniyeden dakikaya çevir
    tezgah_sureleri = second_to_minute(tezgah_sureleri)
    
    # Süreye göre sırala
    tezgah_sureleri = tezgah_sureleri.sort_values(by="Süre (Dakika)", ascending=True)
    
    logger.info("Tezgah duruş süreleri hesaplaması tamamlandı.")
    return tezgah_sureleri

def calculate_machine_stop_type_times(df: pd.DataFrame) -> pd.DataFrame:
    """
    İş merkezleri için duruş tipine göre süreleri hesaplar.
    
    Args:
        df: İşlenecek DataFrame
        
    Returns:
        pd.DataFrame: İş merkezleri ve duruş tiplerine göre süreleri içeren DataFrame
    """
    logger.info("Tezgah duruş tipi süreleri hesaplanıyor...")
    
    # Her bir "İş Merkezi Kodu" ve "Duruş Adı" için toplam süreyi hesapla
    tezgah_durus_ozet = df.groupby(["İş Merkezi Kodu ", "Duruş Adı"])["Süre (Saniye)"].sum().reset_index()

    # "YEMEK MOLASI" ve "TASARIM" ile başlayan satırları bul ve toplam sürelerini al
    yemek_molasi = tezgah_durus_ozet[tezgah_durus_ozet['Duruş Adı'].str.startswith("YEMEK MOLASI")]
    tasarim_durusu = tezgah_durus_ozet[tezgah_durus_ozet['Duruş Adı'].str.startswith("TASARIM")]
    smed_durusu = tezgah_durus_ozet[tezgah_durus_ozet['Duruş Adı'].str.contains("SMED", case=False)]

    # İş Merkezi Kodu bazında toplamları al
    yemek_molasi_toplam = yemek_molasi.groupby("İş Merkezi Kodu ")['Süre (Saniye)'].sum().reset_index()
    tasarim_durusu_toplam = tasarim_durusu.groupby("İş Merkezi Kodu ")['Süre (Saniye)'].sum().reset_index()
    smed_durusu_toplam = smed_durusu.groupby("İş Merkezi Kodu ")['Süre (Saniye)'].sum().reset_index()

    # Yeni isimler vererek dataframe'e eklemek için sütun ekle
    yemek_molasi_toplam['Duruş Adı'] = "YEMEK MOLASI"
    tasarim_durusu_toplam['Duruş Adı'] = "TASARIM DURUŞU"
    smed_durusu_toplam['Duruş Adı'] = "AYAR"

    # Ana df'deki "YEMEK MOLASI", "TASARIM" ve "SMED" ile başlayan satırları filtrele
    tezgah_durus_ozet = tezgah_durus_ozet[~tezgah_durus_ozet['Duruş Adı'].str.startswith("YEMEK MOLASI")]
    tezgah_durus_ozet = tezgah_durus_ozet[~tezgah_durus_ozet['Duruş Adı'].str.startswith("TASARIM")]
    tezgah_durus_ozet = tezgah_durus_ozet[~tezgah_durus_ozet['Duruş Adı'].str.contains("SMED")]

    # Yeni toplamları ana dataframe'e ekle
    tezgah_durus_ozet = pd.concat([
        tezgah_durus_ozet, 
        yemek_molasi_toplam, 
        tasarim_durusu_toplam, 
        smed_durusu_toplam
    ], ignore_index=True)

    # Saniyeden dakikaya çevir
    tezgah_durus_ozet = second_to_minute(tezgah_durus_ozet)
    
    logger.info("Tezgah duruş tipi süreleri hesaplaması tamamlandı.")
    return tezgah_durus_ozet

def filter_sort_top_stops(
    df: pd.DataFrame, 
    max_week: int, 
    gozlemlenecek: str = "KISIM"
) -> pd.DataFrame:
    """
    Her bir kısım veya tezgah için en büyük 10 duruşu filtreleyip sıralar.
    
    Args:
        df: İşlenecek DataFrame
        max_week: En son hafta numarası
        gozlemlenecek: Gruplandırma için kullanılacak sütun adı (KISIM veya İş Merkezi Kodu)
        
    Returns:
        pd.DataFrame: Filtrelenmiş ve sıralanmış DataFrame
    """
    logger.info(f"{gozlemlenecek} için en büyük 10 duruş hesaplanıyor...")
    
    # 'Gözlemlenecek', 'Hafta' ve 'Duruş Adı' kolonlarına göre gruplandırıp 
    # 'Süre (Saniye)' kolonunun toplamını hesapla
    grouped_df = df.groupby([gozlemlenecek, 'Hafta', 'Duruş Adı'])['Süre (Saniye)'].sum().reset_index()
    grouped_df = grouped_df[grouped_df[gozlemlenecek] != 'Diğer']
    
    # 'Duruş Adı' değerlerini yeniden sınıflandır
    grouped_df['Duruş Adı'] = grouped_df['Duruş Adı'].apply(
        lambda x: 'YEMEK MOLASI' if 'YEMEK MOLASI' in x 
        else ('TASARIM DURUŞLARI' if 'TASARIM' in x else x)
    )
    
    # Aynı gözlemlenecek, hafta ve duruş adı altında gruplandırıp, 'Süre (Saniye)' kolonunu topla
    grouped_df = grouped_df.groupby([gozlemlenecek, 'Hafta', 'Duruş Adı'], as_index=False)['Süre (Saniye)'].sum()
    
    # Maksimum hafta değerine göre filtreleme
    latest_week_df = grouped_df[grouped_df['Hafta'] == max_week]
    
    # Her gözlemlenecek için en büyük 10 duruşu al
    top10 = (
        latest_week_df.sort_values([gozlemlenecek, 'Süre (Saniye)'], ascending=[True, False])
        .groupby(gozlemlenecek)
        .head(10)
        .reset_index(drop=True)
    )
    
    # top_10_duruslar veri setindeki gözlemlenecek ve Duruş Adı sütunlarına göre grouped_df'yi filtrele
    filtered_df = grouped_df.merge(top10[[gozlemlenecek, 'Duruş Adı']], on=[gozlemlenecek, 'Duruş Adı'])
    
    # Veriyi Süre (Saniye) sütununa göre azalan sırada sırala
    filtered_df = filtered_df.sort_values(by='Süre (Saniye)', ascending=False)
    
    # Saniyeden dakikaya çevir
    filtered_df = second_to_minute(filtered_df)
    
    logger.info(f"{gozlemlenecek} için en büyük 10 duruş hesaplaması tamamlandı.")
    return filtered_df

def calculate_part_average_stop_times(
    df: pd.DataFrame,
    kisim: str,
    kisim_tezgah_sayilari: Dict[str, int]
) -> pd.DataFrame:
    """
    Belirli bir kısım için tezgah başına ortalama duruş sürelerini hesaplar.
    
    Args:
        df: İşlenecek DataFrame
        kisim: Hesaplama yapılacak kısım adı
        kisim_tezgah_sayilari: Kısımlara göre tezgah sayıları
        
    Returns:
        pd.DataFrame: Tezgah başına ortalama duruş sürelerini içeren DataFrame
    """
    logger.info(f"{kisim} için tezgah başına ortalama duruş süreleri hesaplanıyor...")
    
    # Belirli kısım için veri filtrele
    kisim_for_avg = df[df["KISIM"] == kisim].copy()
    
    # Tezgah sayısı
    tezgah_sayisi = kisim_tezgah_sayilari.get(kisim, 1)
    
    # Süreleri tezgah sayısına böl
    kisim_for_avg['Süre (Saniye)'] = (kisim_for_avg['Süre (Saniye)'] / tezgah_sayisi).astype(int)
    
    # Duruş adlarına göre süreleri topla ve benzer duruşları birleştir
    result = calculate_stop_time_sum(kisim_for_avg)
    
    logger.info(f"{kisim} için tezgah başına ortalama duruş süreleri hesaplaması tamamlandı.")
    return result

def calculate_oee_data(
    df: pd.DataFrame, 
    weeks: List[int]
) -> Dict[str, Dict]:
    """
    OEE, performans, kullanılabilirlik ve kalite değerlerini hesaplar.
    
    Args:
        df: İşlenecek DataFrame
        weeks: Hafta numaraları listesi
        
    Returns:
        Dict[str, Dict]: Haftalara ve kısımlara göre OEE verileri
    """
    logger.info("OEE verileri hesaplanıyor...")
    
    oee_data = {}
    
    # Her hafta için hesapla
    for week in weeks:
        week_df = df[df["Hafta"] == week]
        
        # Genel ortalama
        oee_general = week_df["Oee"].mean()
        performans_general = week_df["Performans"].mean()
        kullanilabilirlik_general = week_df["Kullanılabilirlik"].mean()
        kalite_general = week_df["Kalite"].mean()
        
        oee_data[f"Genel_{week}"] = {
            "oee": oee_general,
            "performans": performans_general,
            "kullanilabilirlik": kullanilabilirlik_general,
            "kalite": kalite_general
        }
        
        # Kısımlara göre
        for kisim in week_df["KISIM"].unique():
            if kisim == "Diğer":
                continue
                
            kisim_df = week_df[week_df["KISIM"] == kisim]
            
            oee_part = kisim_df["Oee"].mean()
            performans_part = kisim_df["Performans"].mean()
            kullanilabilirlik_part = kisim_df["Kullanılabilirlik"].mean()
            kalite_part = kisim_df["Kalite"].mean()
            
            oee_data[f"{kisim}_{week}"] = {
                "oee": oee_part,
                "performans": performans_part,
                "kullanilabilirlik": kullanilabilirlik_part,
                "kalite": kalite_part
            }
        
        # Tezgahlara göre
        for machine in week_df["İş Merkezi Kodu "].unique():
            machine_df = week_df[week_df["İş Merkezi Kodu "] == machine]
            
            oee_machine = machine_df["Oee"].mean()
            performans_machine = machine_df["Performans"].mean()
            kullanilabilirlik_machine = machine_df["Kullanılabilirlik"].mean()
            kalite_machine = machine_df["Kalite"].mean()
            
            oee_data[f"{machine}_{week}"] = {
                "oee": oee_machine,
                "performans": performans_machine,
                "kullanilabilirlik": kullanilabilirlik_machine,
                "kalite": kalite_machine
            }
    
    logger.info("OEE verileri hesaplaması tamamlandı.")
    return oee_data