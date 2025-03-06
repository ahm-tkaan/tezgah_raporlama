"""
Tezgah duruş analizi ana modülü.
"""

import os
import time
import argparse
import logging
import pandas as pd
import sys
from typing import Dict, List, Tuple, Optional

# Modülleri içe aktar
from config.tezgah_listesi import KISIMLAR_DICT
from src.data_processing import prepare_data_for_analysis, get_latest_week_data
from src.calculations import (
    calculate_stop_time_sum,
    calculate_part_machine_average_time,
    calculate_machine_stop_times,
    calculate_machine_stop_type_times,
    filter_sort_top_stops,
    calculate_part_average_stop_times
)
from src.visualization import (
    visualize_pie,
    visualize_weekly_comparison,
    visualize_bar,
    plot_bar,
    visualize_top_bottom_machines,
    generate_oee_visuals
)

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tezgah_analiz.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    """
    Komut satırı argümanlarını ayrıştırır.
    
    Returns:
        argparse.Namespace: Ayrıştırılmış argümanlar
    """
    parser = argparse.ArgumentParser(description='Tezgah Duruş Analizi')
    parser.add_argument('--durus_file', type=str, default="data/raw/4 Haftalık Duruş.xlsx",
                        help='Duruş verisi Excel dosya yolu')
    parser.add_argument('--calisma_file', type=str, default="data/raw/Günlük Çalışma Süreleri.xlsx",
                        help='Çalışma süresi Excel dosya yolu')
    parser.add_argument('--arizali_file', type=str, default="data/raw/Arızalı Tezgahlar.txt",
                        help='Arızalı tezgah listesi dosya yolu (opsiyonel)')
    parser.add_argument('--show_plots', action='store_true',
                        help='Grafikleri göster')
    parser.add_argument('--save_plots', action='store_true', default=True,
                        help='Grafikleri kaydet')
    parser.add_argument('--export_excel', action='store_true',
                        help='Son haftanın verilerini Excel olarak dışa aktar')
    
    return parser.parse_args()

def check_files_exist(durus_file: str, calisma_file: str, arizali_file: str) -> bool:
    """
    Dosyaların varlığını kontrol eder.
    
    Args:
        durus_file: Duruş verisi dosya yolu
        calisma_file: Çalışma süresi dosya yolu
        arizali_file: Arızalı tezgah listesi dosya yolu
        
    Returns:
        bool: Tüm dosyalar varsa True, aksi halde False
    """
    # Duruş verisi dosyasını kontrol et
    if not os.path.exists(durus_file):
        logger.error(f"Duruş verisi dosyası bulunamadı: {durus_file}")
        print(f"HATA: Duruş verisi dosyası bulunamadı: {durus_file}")
        return False
    
    # Çalışma süresi dosyasını kontrol et
    if not os.path.exists(calisma_file):
        logger.error(f"Çalışma süresi dosyası bulunamadı: {calisma_file}")
        print(f"HATA: Çalışma süresi dosyası bulunamadı: {calisma_file}")
        return False
    
    # Arızalı tezgah listesi dosyasını kontrol et (opsiyonel)
    if arizali_file and not os.path.exists(arizali_file):
        logger.warning(f"Arızalı tezgah listesi dosyası bulunamadı: {arizali_file}")
        print(f"UYARI: Arızalı tezgah listesi dosyası bulunamadı: {arizali_file}")
        # Arızalı tezgah listesi opsiyonel olduğu için False dönme
    
    return True

def create_output_directories():
    """
    Çıktı dizinlerini oluşturur.
    """
    directories = [
        "Raporlar",
        "Raporlar/Genel",
        "Raporlar/Kısımlar/Son Hafta",
        "Raporlar/Kısımlar/4 haftalık",
        "Raporlar/Kısımlar/Son Hafta Tezgah Başına Ortalama",
        "Raporlar/Tezgahlar/Son Hafta",
        "Raporlar/Tezgahlar/4 haftalık",
        "Raporlar/Tee/Genel",
        "Raporlar/Tee/Kısımlar",
        "Raporlar/Tee/Tezgahlar"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main() -> None:
    """
    Ana program akışı.
    """
    # Hoş geldiniz mesajı
    print("=" * 80)
    print("              TEZGAH DURUŞ ANALİZİ PROGRAMI")
    print("=" * 80)
    
    # Başlangıç zamanını kaydet
    start_time = time.time()
    logger.info("Tezgah duruş analizi başlıyor...")
    
    # Çıktı dizinlerini oluştur
    create_output_directories()
    
    # Komut satırı argümanlarını ayrıştır
    args = parse_arguments()
    
    # Dosyaların varlığını kontrol et
    if not check_files_exist(args.durus_file, args.calisma_file, args.arizali_file):
        print("\nDosya yollarını kontrol edin ve tekrar deneyin.")
        print("Program 5 saniye içinde kapanacak...")
        time.sleep(5)
        sys.exit(1)
    
    print(f"\nDuruş verisi dosyası: {args.durus_file}")
    print(f"Çalışma süresi dosyası: {args.calisma_file}")
    print(f"Arızalı tezgah listesi: {args.arizali_file}")
    print("\nVeriler yükleniyor ve işleniyor, lütfen bekleyin...")
    
    try:
        # Veriyi hazırla
        df, kisim_tezgah_sayilari, weeks = prepare_data_for_analysis(
            args.durus_file,
            args.calisma_file,
            args.arizali_file
        )
        
        # Son hafta verisini al
        latest_week_df = get_latest_week_data(df, weeks)
        
        # Excel'e dışa aktarma
        if args.export_excel:
            output_file = 'Son Hafta için Analiz Edilen Veriler.xlsx'
            latest_week_df.to_excel(output_file, index=False)
            logger.info(f"Son hafta verileri dışa aktarıldı: {output_file}")
            print(f"Son hafta verileri dışa aktarıldı: {output_file}")
        
        print("\nVeriler başarıyla yüklendi. Hesaplamalar yapılıyor...")
        
        # Duruş sürelerini hesapla
        toplam_sureler = calculate_stop_time_sum(latest_week_df)
        
        # Kısımlara göre tek tezgah için ortalama süreleri hesapla
        tezgah_basina_kisim_sureleri = calculate_part_machine_average_time(
            latest_week_df, 
            kisim_tezgah_sayilari
        )
        
        # İş merkezlerinin toplam duruş sürelerini hesapla
        tezgah_sureleri = calculate_machine_stop_times(latest_week_df)
        
        # İş merkezleri için duruş tipine göre süreleri hesapla
        tezgah_durus_ozet = calculate_machine_stop_type_times(latest_week_df)
        
        # Haftalar boyunca en büyük 10 duruşu hesapla (kısımlara göre)
        filtered_kisimlar = filter_sort_top_stops(df, weeks[0])
        
        # Haftalar boyunca en büyük 10 duruşu hesapla (tezgahlara göre)
        filtered_machine = filter_sort_top_stops(
            df, 
            weeks[0], 
            gozlemlenecek='İş Merkezi Kodu '
        )
        
        print("\nHesaplamalar tamamlandı. Grafikler oluşturuluyor...")
        
        # ------ Görselleştirmeler ------
        
        # Tüm tezgahlar için toplam duruş süreleri - pasta grafik
        visualize_pie(
            toplam_sureler, 
            threshold=3, 
            baslik="Tüm Tezgahlar Toplam",
            save=args.save_plots, 
            show=args.show_plots,
            category_column="Duruş Adı"
        )
        
        # Tezgah başına ortalama duruş süreleri - pasta grafik
        visualize_pie(
            tezgah_basina_kisim_sureleri, 
            baslik="Tüm Bölümler (Tezgah Başına)",
            save=args.save_plots, 
            show=args.show_plots,
            category_column="KISIM"
        )
        
        # Her kısım için tezgah başına ortalama duruş süreleri - pasta grafik
        for kisim in kisim_tezgah_sayilari.keys():
            kisim_avg_sureler = calculate_part_average_stop_times(
                latest_week_df,
                kisim,
                kisim_tezgah_sayilari
            )
            
            visualize_pie(
                kisim_avg_sureler, 
                baslik=f"{kisim} (Tezgah Başına)", 
                threshold=3,
                save=args.save_plots, 
                show=args.show_plots,
                category_column="Duruş Adı"
            )
        
        # En fazla duruş yapan tezgahlar - çubuk grafik
        visualize_bar(
            tezgah_sureleri, 
            colors="Reds", 
            bundan=-10, 
            baslik="En Fazla Duruş Yapan 10 Tezgah",
            save=args.save_plots, 
            show=args.show_plots
        )
        
        # En az duruş yapan tezgahlar - çubuk grafik
        visualize_bar(
            tezgah_sureleri, 
            colors="Greens", 
            bundan=0, 
            buna=10, 
            baslik="En Az Duruş Yapan 10 Tezgah",
            save=args.save_plots, 
            show=args.show_plots
        )
        
        # En az ve en çok duruş yapan tezgahlar karşılaştırması - çubuk grafik
        visualize_top_bottom_machines(
            tezgah_sureleri,
            save=args.save_plots, 
            show=args.show_plots
        )
        
        # Orta seviyede duruş yapan tezgahlar - çubuk grafik
        visualize_bar(
            tezgah_sureleri, 
            bundan=10, 
            buna=-10, 
            text=0,
            save=args.save_plots, 
            show=args.show_plots
        )
        
        # Her tezgah için duruş nedenleri - çubuk grafik
        plot_bar(
            tezgah_durus_ozet,
            save=args.save_plots, 
            show=args.show_plots
        )
        
        # 4 haftalık kısımlara göre duruş karşılaştırması - çubuk grafik
        visualize_weekly_comparison(
            filtered_kisimlar,
            egiklik=75,  # Eğiklik değerini 75 olarak ayarla
            sort_by_last_week=True,
            target_week=9,
            save=args.save_plots, 
            show=args.show_plots
        )

        # 4 haftalık tezgahlara göre duruş karşılaştırması - çubuk grafik
        visualize_weekly_comparison(
            filtered_machine, 
            gozlem="İş Merkezi Kodu ", 
            egiklik=75,  # Eğiklik değerini kısım grafikleriyle aynı yap (0 yerine 75)
            palet="Accent",
            sort_by_last_week=True,
            target_week=9,
            save=args.save_plots, 
            show=args.show_plots
        )
        # Her bir tezgah için duruş nedenleri pasta grafikleri
        print("\nHer tezgah için duruş nedenleri pasta grafikleri oluşturuluyor...")
        unique_machines = latest_week_df["İş Merkezi Kodu "].unique()
        
        # Tezgahlar için pasta grafik klasörünü oluştur
        tezgah_pasta_path = "Raporlar/Tezgahlar/Son Hafta Pasta"
        os.makedirs(tezgah_pasta_path, exist_ok=True)
        
        for machine_code in unique_machines:
            # Her tezgah için veriyi filtrele
            machine_data = latest_week_df[latest_week_df["İş Merkezi Kodu "] == machine_code]
            
            # ÇALIŞMA SÜRESİ dışındaki duruşları filtrele
            machine_data = machine_data[machine_data["Duruş Adı"] != "ÇALIŞMA SÜRESİ"]
            
            # Toplam süreyi kontrol et
            if machine_data["Süre (Dakika)"].sum() > 0:
                # Duruş adlarına göre grupla ve süreleri topla
                machine_stop_summary = machine_data.groupby("Duruş Adı")["Süre (Dakika)"].sum().reset_index()
                
                # Pasta grafiğini oluştur
                visualize_pie(
                    machine_stop_summary,
                    threshold=3,  # %3'ten küçük olanları "Diğer" kategorisinde topla
                    baslik=f"{machine_code} Duruş Nedenleri",
                    save=args.save_plots,
                    show=args.show_plots,
                    category_column="Duruş Adı"
                )
                
                logger.info(f"{machine_code} tezgahı için duruş nedenleri pasta grafiği oluşturuldu.")        
        
        # OEE ve diğer metrik görselleri
        generate_oee_visuals(df, weeks)
        
        # Program tamamlandı
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Toplam tezgah sayısını hesapla
        total_machines = sum(kisim_tezgah_sayilari.values())
        time_per_machine = elapsed_time / total_machines if total_machines > 0 else 0
        
        logger.info(f"Analiz tamamlandı. Toplam çalışma süresi: {elapsed_time:.2f} saniye.")
        logger.info(f"Tezgah başına işlem süresi: {time_per_machine:.2f} saniye.")
        
        print("\nGrafikler oluşturuldu ve kaydedildi.")
        print(f"Toplam çalışma süresi: {elapsed_time:.2f} saniye.")
        print(f"Tezgah başına işlem süresi: {time_per_machine:.2f} saniye.")
        print("\nSonuçlar 'Raporlar' klasöründe bulunabilir.")
        print("=" * 80)
        print("                 PROGRAM BAŞARIYLA TAMAMLANDI")
        print("=" * 80)
        
        # Kullanıcıdan komut istemi kapatmadan önce bir tuşa basmasını iste
        input("\nÇıkmak için herhangi bir tuşa basın...")
        
    except Exception as e:
        logger.error(f"Program çalıştırılırken bir hata oluştu: {str(e)}", exc_info=True)
        print(f"\nHATA: Program çalıştırılırken bir hata oluştu: {str(e)}")
        print("Detaylı hata bilgileri için 'tezgah_analiz.log' dosyasına bakın.")
        print("Program 5 saniye içinde kapanacak...")
        time.sleep(5)
        sys.exit(1)
    
if __name__ == "__main__":
    main()