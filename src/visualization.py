"""
Tezgah duruş analizleri için görselleştirme fonksiyonları.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple, Optional, Union
import logging

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("visualization.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def ensure_dir(directory: str) -> None:
    """
    Belirtilen dizinin var olduğundan emin olur, yoksa oluşturur.
    
    Args:
        directory: Oluşturulacak dizin yolu
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Dizin oluşturuldu: {directory}")

def visualize_pie(
    data: pd.DataFrame, 
    threshold: float = 2, 
    baslik: str = "Pasta Grafik",
    save: bool = True,
    show: bool = True,
    category_column: str = None  # Yeni parametre ekleyelim
) -> None:
    """
    Duruş sürelerini pasta grafik olarak görselleştirir.
    
    Args:
        data: Görselleştirilecek DataFrame
        threshold: Eşik değeri, bu değerden düşük yüzdeli duruşlar "Diğer" olarak gruplandırılır
        baslik: Grafik başlığı
        save: Grafiği kaydetme bayrağı
        show: Grafiği gösterme bayrağı
        category_column: Kategori sütunu adı (None ise otomatik tespit edilir)
    """
    logger.info(f"Pasta grafik oluşturuluyor: {baslik}")
    
    if "KISIM" in baslik:
        folder_path = 'Raporlar/Kısımlar/Son Hafta'
    else:
        folder_path = 'Raporlar/Genel'
    
    ensure_dir(folder_path)
    
    # Veri çerçevesini kopyala
    data = data.copy()
    
    # Kategori sütununu belirle
    if category_column is None:
        # Otomatik olarak kategori sütununu belirle
        if 'Duruş Adı' in data.columns:
            category_column = 'Duruş Adı'
        elif 'KISIM' in data.columns:
            category_column = 'KISIM'
        elif 'İş Merkezi Kodu ' in data.columns:
            category_column = 'İş Merkezi Kodu '
        else:
            # Eğer uygun sütun bulunamazsa, indeksi kullan
            data = data.reset_index()
            if 'index' in data.columns:
                category_column = 'index'
            else:
                logger.error("Veri çerçevesinde kategori sütunu bulunamadı!")
                return
    
    # Kategori sütunu olup olmadığını kontrol et
    if category_column not in data.columns:
        logger.error(f"Kategori sütunu '{category_column}' veri çerçevesinde bulunamadı!")
        return
    
    # Toplam süreyi hesapla
    total_time = data["Süre (Dakika)"].sum()
    
    # Yüzdeleri hesapla
    data["Yüzde"] = (data["Süre (Dakika)"] / total_time * 100)
    
    # Eşik değerinden küçük olanları "Diğer" olarak grupla
    diger_sure = data[data["Yüzde"] < threshold]["Süre (Dakika)"].sum()
    diger_df = data[data["Yüzde"] >= threshold].copy()
    
    # "Diğer" satırını yeni DataFrame'e ekle
    if diger_sure > 0:
        diger_row = pd.DataFrame({
            category_column: ["Diğer"],
            "Süre (Dakika)": [diger_sure],
            "Yüzde": [(diger_sure / total_time * 100)]
        })
        diger_df = pd.concat([diger_df, diger_row])
    
    # Pasta grafik oluşturma
    plt.figure(figsize=(12, 12))
    myexplode = [0.1] * len(diger_df)  # Patlatma ayarları
    
    # Pasta grafiği
    wedges, texts, autotexts = plt.pie(
        diger_df["Süre (Dakika)"], 
        labels=diger_df[category_column],  # Etiketleri doğrudan ver
        wedgeprops=dict(width=0.7),
        autopct=lambda p: '{:.1f}%'.format(p) if p > threshold else '',  # threshold'tan küçük yüzdeleri göstermeme
        startangle=90,
        colors=sns.color_palette("Pastel2", len(diger_df)),
        explode=myexplode,
        shadow=True
    )
    
    # Wedge'lar üzerinde kutucuklarla bilgi ekleme
    for i, wedge in enumerate(wedges):
        ang = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
        y = np.sin(np.deg2rad(ang)) * 1.2
        x = np.cos(np.deg2rad(ang)) * 1.6
    
        # Ok çizme
        plt.annotate('', xy=(x*0.75, y*0.95), xytext=(np.cos(np.deg2rad(ang)) * 0.9, np.sin(np.deg2rad(ang)) * 0.9),
                     arrowprops=dict(arrowstyle='->', color='black', lw=1))
    
        # Bilgi kutucuğu ekleme
        plt.text(x, y, f"{diger_df.iloc[i][category_column]}: {diger_df['Süre (Dakika)'].iloc[i]:.0f} dk", 
                 ha='center', fontsize=10,
                 bbox=dict(facecolor='white', alpha=0.5, edgecolor='blue', boxstyle='round,pad=0.5'))
    
    plt.title(f"{baslik} Toplam Süre (Dakika)", fontsize=14, pad=15)
    plt.axis('equal')  # Eşit oranlar için
    
    if save:
        plt.savefig(os.path.join(folder_path, f"{baslik}.png"), dpi=300, bbox_inches='tight')
        logger.info(f"Grafik kaydedildi: {os.path.join(folder_path, f'{baslik}.png')}")
    
    if show:
        plt.show()
    
    plt.close()

def visualize_weekly_comparison(
    df: pd.DataFrame, 
    gozlem: str = "KISIM", 
    egiklik: int = 75, 
    palet: str = "tab20",
    save: bool = True,
    show: bool = True,
    sort_by_last_week: bool = True
) -> None:
    """
    4 haftalık duruş karşılaştırmasını görselleştirir.
    
    Args:
        df: Görselleştirilecek DataFrame
        gozlem: Gruplandırma için kullanılacak sütun adı (KISIM veya İş Merkezi Kodu)
        egiklik: Etiket metin açısı
        palet: Renk paleti
        save: Grafiği kaydetme bayrağı
        show: Grafiği gösterme bayrağı
        sort_by_last_week: Son haftaya göre sıralama bayrağı
    """
    logger.info(f"{gozlem} için 4 haftalık karşılaştırma grafikleri oluşturuluyor...")
    
    if gozlem == "KISIM":
        # Klasör yolunu tanımlama
        folder_path = 'Raporlar/Kısımlar/4 haftalık'  # Klasör adı
    else:
        folder_path = 'Raporlar/Tezgahlar/4 haftalık'
    
    ensure_dir(folder_path)
    
    # Hafta listesini al ve son haftayı belirle
    weeks = sorted(df["Hafta"].unique(), reverse=True)
    last_week = weeks[0] if weeks else None
    
    # Her gözlem değeri için grafik oluştur
    for gozlemlenen, data in df.groupby(gozlem):
        plt.figure(figsize=(14, 8))
        
        # Eğer son haftaya göre sıralama isteniyorsa
        if sort_by_last_week and last_week:
            # Son haftaya ait veriyi al
            last_week_data = data[data['Hafta'] == last_week]
            
            # Son haftaya göre duruş adlarını sırala
            if not last_week_data.empty:
                sorted_stops = last_week_data.sort_values('Süre (Dakika)', ascending=False)['Duruş Adı'].unique()
                
                # Tüm duruş adları içinde olmayanları ekle
                all_stops = data['Duruş Adı'].unique()
                for stop in all_stops:
                    if stop not in sorted_stops:
                        sorted_stops = np.append(sorted_stops, stop)
                
                # Kategorik ekseni oluştur
                data['Duruş Adı'] = pd.Categorical(data['Duruş Adı'], categories=sorted_stops, ordered=True)
                
                # Sıralı veriyi kullanarak grafik oluştur
                data = data.sort_values('Duruş Adı')
        
        # Çubuk grafiğini oluştur
        ax = sns.barplot(data=data, x='Duruş Adı', y='Süre (Dakika)', hue='Hafta', palette=palet)
    
        # Y-ekseni üst sınırını genişlet
        max_height = max([p.get_height() for p in ax.patches]) if ax.patches else 0
        ax.set_ylim(0, max_height * 1.1)  # Y-ekseni üst sınırını %10 arttır
    
        # Çubukların üstüne dik metin ekle
        for i, p in enumerate(ax.patches):
            # Her çubuğa farklı bir ofset ekleyerek konumlandırma
            offset = (i % len(weeks)) * 5  # Haftaların sayısına göre ofset belirleme
            height = p.get_height()
            # Yüksekliği sıfırdan büyük olan çubuklar için metin ekle
            if height > 0:
                ax.annotate(f'{height:.0f}', 
                            (p.get_x() + p.get_width() / 2, height + offset), 
                            ha='center', va='bottom', 
                            fontsize=10, color='black', 
                            rotation=egiklik,  # Metni belirtilen açıda yazdır
                            xytext=(0, 5), textcoords='offset points')
    
        plt.title(f'{gozlemlenen} - 4 Haftalık En Büyük 10 Duruş Karşılaştırması')
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Hafta')
        plt.tight_layout()
        
        if save:
            plt.savefig(os.path.join(folder_path, f"{gozlemlenen} - 4 HAFTALIK.png"), dpi=300, bbox_inches='tight')
            logger.info(f"Grafik kaydedildi: {os.path.join(folder_path, f'{gozlemlenen} - 4 HAFTALIK.png')}")
        
        if show:
            plt.show()
        
        plt.close()
    
    logger.info(f"{gozlem} için 4 haftalık karşılaştırma grafikleri oluşturuldu.")
    
def visualize_bar(
    data: pd.DataFrame, 
    colors: str = "Accent", 
    bundan: Optional[int] = None, 
    buna: Optional[int] = None, 
    text: int = 1, 
    baslik: str = "Tüm İş Merkezleri",
    save: bool = True,
    show: bool = True
) -> None:
    """
    Duruş sürelerini çubuk grafik olarak görselleştirir.
    
    Args:
        data: Görselleştirilecek DataFrame
        colors: Renk paleti
        bundan: Başlangıç indeksi
        buna: Bitiş indeksi
        text: Metin gösterme bayrağı
        baslik: Grafik başlığı
        save: Grafiği kaydetme bayrağı
        show: Grafiği gösterme bayrağı
    """
    logger.info(f"Çubuk grafik oluşturuluyor: {baslik}")
    
    # Toplam süreyi hesapla
    total_time = data["Süre (Dakika)"].sum()
    
    # Grafik oluşturma
    plt.figure(figsize=(12, 8))

    # Klasör yolunu belirle
    if " (Tezgah Başına)" in baslik:
        folder_path = 'Raporlar/Kısımlar/Son Hafta Tezgah Başına Ortalama'
    else:
        folder_path = 'Raporlar/Genel'
    ensure_dir(folder_path)
    
    # İndeksleri kontrol et
    if bundan is None:
        bundan = 0
    if buna is None:
        buna = len(data)
    
    # Renk paleti oluştur
    filtered_data = data.iloc[bundan:buna]
    colors_palette = sns.color_palette(colors, len(filtered_data["İş Merkezi Kodu "]))
    
    # Yüzde hesapla
    filtered_data = filtered_data.copy()  # Orijinal DataFrame'i değiştirmemek için
    filtered_data["Yüzde"] = (filtered_data["Süre (Dakika)"] / total_time) * 100
    
    # Bar grafiği çizdir
    bars = plt.bar(filtered_data["İş Merkezi Kodu "], filtered_data["Süre (Dakika)"], color=colors_palette)
    
    if text:
        # Yüzdeleri her bir barın üstüne ekle
        for bar in bars:
            height = bar.get_height()
            percentage = (height / total_time) * 100  # Yüzde hesaplama
            plt.text(
                bar.get_x() + bar.get_width() / 2, height, 
                f"{height} ({percentage:.1f}%)",  # Hem süre hem de yüzde gösterme
                ha='center', va='bottom', fontsize=10, color='black', weight='bold'
            )
    
    # Grafik başlık ve eksen etiketleri
    plt.title(f"{baslik}", fontsize=14, pad=15)
    plt.xlabel("İş Merkezi Kodu", fontsize=12)
    plt.ylabel("Süre (Dakika)", fontsize=12)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    if save:
        plt.savefig(os.path.join(folder_path, f"{baslik}.png"), dpi=300, bbox_inches='tight')
        logger.info(f"Grafik kaydedildi: {os.path.join(folder_path, f'{baslik}.png')}")
    
    if show:
        plt.show()
    
    plt.close()
    
def plot_bar(
    df: pd.DataFrame, 
    machine_code_column: str = "İş Merkezi Kodu ", 
    stoppage_column: str = "Duruş Adı", 
    duration_column: str = "Süre (Dakika)", 
    threshold: float = 3,
    save: bool = True,
    show: bool = True
) -> None:
    """
    Her bir tezgah için duruş sürelerini çubuk grafik olarak görselleştirir.
    
    Args:
        df: Görselleştirilecek DataFrame
        machine_code_column: Makine kodu sütunu adı
        stoppage_column: Duruş adı sütunu adı
        duration_column: Süre sütunu adı
        threshold: Eşik değeri, bu değerden düşük yüzdeli duruşlar "Diğer" olarak gruplandırılır
        save: Grafiği kaydetme bayrağı
        show: Grafiği gösterme bayrağı
    """
    logger.info("Tezgah duruş grafikleri oluşturuluyor...")
    
    # Unique makine kodlarını al
    machine_codes = df[machine_code_column].unique()

    # Klasör yolunu tanımla
    folder_path = 'Raporlar/Tezgahlar/Son Hafta'
    ensure_dir(folder_path)
    
    for code in machine_codes:
        logger.info(f"Tezgah grafik oluşturuluyor: {code}")
        
        # Makineye ait verileri filtrele
        machine_data = df[df[machine_code_column] == code].copy()
        
        # Toplam süreyi hesapla
        total_duration = machine_data[duration_column].sum()
        
        # Eğer toplam süre 0 ise, bu makine için grafik oluşturma
        if total_duration == 0:
            logger.warning(f"Tezgah {code} için veri yok veya toplam süre 0.")
            continue
            
        # Yüzdeleri hesapla
        machine_data["Yüzde"] = (machine_data[duration_column] / total_duration) * 100
        
        # Eşik değerinden küçük olanları "Diğer" olarak grupla
        other_duration = machine_data[machine_data["Yüzde"] < threshold][duration_column].sum()
        filtered_data = machine_data[machine_data["Yüzde"] >= threshold].copy()
        
        if other_duration > 0:
            filtered_data = pd.concat([
                filtered_data, 
                pd.DataFrame({
                    stoppage_column: ["Diğer"], 
                    duration_column: [other_duration], 
                    "Yüzde": [(other_duration / total_duration) * 100]
                })
            ])
        
        # Süreye göre büyükten küçüğe sırala
        filtered_data = filtered_data.sort_values(by=duration_column, ascending=False)
        
        # Grafik boyutunu artır - daha fazla yükseklik ve genişlik ekle
        plt.figure(figsize=(12, 8))  # Boyutu 10x6'dan 12x8'e çıkar
        
        # Renk paleti dinamik olarak oluştur
        pastel_colors = sns.color_palette("pastel", n_colors=len(filtered_data[stoppage_column].unique()))
        
        # Çubuk grafiğini çiz
        ax = sns.barplot(
            x=filtered_data[stoppage_column],
            y=filtered_data[duration_column],
            palette=pastel_colors,
            hue=filtered_data[stoppage_column],
            dodge=False,
            legend=False  # Uyarıyı engellemek için eklendi
        )

        # Etiketleri ekle
        for index, value in enumerate(filtered_data[duration_column]):
            percentage = filtered_data["Yüzde"].iloc[index]
            plt.text(
                index, 
                value + 10,  # Değerin biraz üzerine yerleştir
                f'{value:.0f} dk\n({percentage:.1f}%)', 
                ha='center',
                fontsize=9
            )
        
        # Başlık ve eksen etiketleri
        plt.title(f"{code} - Duruş Süreleri", fontsize=14, pad=15)
        plt.xlabel("Duruş Adı", fontsize=12)
        plt.ylabel("Süre (Dakika)", fontsize=12)
        
        # X ekseni etiketlerini düzelt - daha dik bir açı ve daha alt hizalama
        plt.xticks(rotation=75, ha='right')  # 45 yerine 75 derece döndür
        
        # Y ekseni üst sınırını ayarla
        max_value = filtered_data[duration_column].max()
        plt.ylim(0, max_value * 1.2)  # %20 margin ekle
        
        # Alt boşluğu artır etiketlerin taşmaması için
        plt.tight_layout(pad=3.0, rect=[0, 0.05, 1, 0.95])  # Alt kenar boşluğunu artır
        
        if save:
            plt.savefig(os.path.join(folder_path, f"{code}.png"), dpi=300, bbox_inches='tight')
            logger.info(f"Grafik kaydedildi: {os.path.join(folder_path, f'{code}.png')}")
        
        if show:
            plt.show()
        
        plt.close()
    
    logger.info("Tezgah duruş grafikleri oluşturuldu.")

def means2png(
    title: str, 
    oee: float = None, 
    performans: float = None, 
    kullanılabilirlik: float = None, 
    kalite: float = None, 
    path: str = None
) -> None:
    """
    OEE ve ilgili metrik değerlerini içeren bir görsel oluşturur.
    
    Args:
        title: Görsel başlığı
        oee: OEE değeri (0-1 aralığında)
        performans: Performans değeri (0-1 aralığında)
        kullanılabilirlik: Kullanılabilirlik değeri (0-1 aralığında)
        kalite: Kalite değeri (0-1 aralığında)
        path: Kaydedilecek dosya yolu
    """
    logger.info(f"OEE görselleştirmesi oluşturuluyor: {title}")
    
    # Sayısal değerleri yüzdelik formatta göstermek için yuvarlama
    try:
        oee = round(oee * 100)
        performans = round(performans * 100)
        kullanılabilirlik = round(kullanılabilirlik * 100)
        kalite = round(kalite * 100)
    except:
        oee, performans, kullanılabilirlik, kalite = "sayısal", "bir", "veri", "yoktur"
        logger.warning(f"{title} için sayısal veriler hesaplanamadı.")
    
    # Görsel boyutları
    width, height = 230, 240

    # Görsel oluştur
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    try:
        # Font yükleme (TTF formatında bir yazı tipi dosyası kullanmanız gerekir)
        font_large = ImageFont.truetype("arial.ttf", 30)
        font_medium = ImageFont.truetype("arial.ttf", 12)
    except:
        # Font yüklenemezse, varsayılan fontları kullan
        logger.warning("Arial fontu yüklenemedi, varsayılan font kullanılıyor.")
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()

    # Başlık ve metrikleri çiz
    draw.text((20, 15), title, fill="black", font=font_large)
    draw.text((20, 70), f"TOPLAM TEE\nORANI : %{oee}", fill="black", font=font_large, spacing=5)
    draw.text((20, 175), 
              f"PERFORMANS ORANI : %{performans}\nKULLANILABİLİRLİK ORANI : %{kullanılabilirlik}\nKALİTE ORANI : %{kalite}",
              fill="black", font=font_medium, spacing=5)

    # Dosya yolunu oluştur
    if path:
        full_path = os.path.join("Raporlar/Tee/", path)
        directory = os.path.dirname(full_path)
        
        # Dizin yoksa oluştur
        ensure_dir(directory)
        
        # Görseli kaydet
        image.save(full_path)
        logger.info(f"OEE görseli kaydedildi: {full_path}")

def combine_images_horizontal(
    image1_path: str, 
    image2_path: str, 
    output_path: str
) -> None:
    """
    İki resmi yatay olarak birleştirir.
    
    Args:
        image1_path: İlk resmin dosya yolu
        image2_path: İkinci resmin dosya yolu
        output_path: Çıktı dosyasının yolu
    """
    try:
        logger.info(f"Resimler birleştiriliyor: {image1_path} ve {image2_path}")
        
        # Resimleri yükle
        image1 = Image.open(image1_path)
        image2 = Image.open(image2_path)
        
        # Yeni resmin boyutları
        new_width = image1.width + image2.width
        new_height = max(image1.height, image2.height)
        
        # Yeni bir boş resim oluştur
        combined_image = Image.new("RGB", (new_width, new_height))
        
        # Resimleri birleştir
        combined_image.paste(image1, (0, 0))
        combined_image.paste(image2, (image1.width, 0))
        
        # Çıktı dizinini kontrol et
        output_dir = os.path.dirname(output_path)
        ensure_dir(output_dir)
        
        # Yeni resmi kaydet
        combined_image.save(output_path)
        logger.info(f"Birleştirilmiş resim kaydedildi: {output_path}")
    except Exception as e:
        logger.error(f"Resim birleştirme hatası: {str(e)}")

def visualize_top_bottom_machines(
    df: pd.DataFrame,
    top_count: int = 7,
    bottom_count: int = 7,
    save: bool = True,
    show: bool = True
) -> None:
    """
    En çok ve en az duruşa sahip tezgahları görselleştirir.
    
    Args:
        df: Görselleştirilecek DataFrame
        top_count: En çok duruşa sahip tezgah sayısı
        bottom_count: En az duruşa sahip tezgah sayısı
        save: Grafiği kaydetme bayrağı
        show: Grafiği gösterme bayrağı
    """
    logger.info(f"En çok ve en az duruşa sahip tezgahlar grafiği oluşturuluyor...")
    
    # Toplam süreyi hesapla
    total_time = df["Süre (Dakika)"].sum()

    # Eşik değeri belirleme
    threshold = 0  # Yüzde 0

    # Yüzde hesaplama ve eşiği kontrol etme
    df_copy = df.copy()  # Orijinal DataFrame'i değiştirmemek için
    df_copy["Yüzde"] = (df_copy["Süre (Dakika)"] / total_time) * 100
    filtered_data = df_copy[df_copy["Yüzde"] > threshold]

    # İlk ve son tezgahları seçme
    top = filtered_data.tail(top_count)  # En yüksek değerler (ascending=True olduğu için tail)
    bottom = filtered_data.head(bottom_count)  # En düşük değerler (ascending=True olduğu için head)

    # Seçilen satırları birleştirme
    selected_data = pd.concat([bottom, top])

    # Renkleri ayarlama: ilk bottom_count yeşil, son top_count kırmızı
    colors = ['#2ca02c'] * len(bottom) + ['#d62728'] * len(top)

    # Bar grafiği oluşturma
    plt.figure(figsize=(12, 8))

    # Bar grafiği çizdir
    bars = plt.bar(selected_data["İş Merkezi Kodu "], selected_data["Süre (Dakika)"], color=colors)

    # Yüzdeleri her bir barın üstüne ekleme
    for bar in bars:
        height = bar.get_height()
        percentage = (height / total_time) * 100  # Yüzde hesaplama
        plt.text(
            bar.get_x() + bar.get_width() / 2, height, 
            f"{height}\n({percentage:.1f}%)",  # Hem süre hem de yüzde gösterme
            ha='center', va='bottom', fontsize=10, color='black', weight='bold'
        )

    # Grafik başlık ve eksen etiketleri
    plt.title(f"İş Merkezi Koduna Göre Süre (Dakika) - İlk {bottom_count} Yeşil, Son {top_count} Kırmızı", fontsize=14, pad=15)
    plt.xlabel("İş Merkezi Kodu", fontsize=12)
    plt.ylabel("Süre (Dakika)", fontsize=12)

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    if save:
        plt.savefig("Raporlar/Genel/İlk ve Son Tezgah.png", dpi=300, bbox_inches='tight')
        logger.info("Grafik kaydedildi: Raporlar/Genel/İlk ve Son Tezgah.png")
    
    if show:
        plt.show()
    
    plt.close()
    
def generate_oee_visuals(
    df: pd.DataFrame, 
    weeks: List[int]
) -> None:
    """
    OEE, performans, kullanılabilirlik ve kalite değerlerini görselleştirir.
    
    Args:
        df: İşlenecek DataFrame
        weeks: Hafta numaraları listesi
    """
    logger.info("OEE görselleri oluşturuluyor...")
    
    # Her hafta için
    for week in weeks:
        week_df = df[df["Hafta"] == week]
        
        # Genel ortalama
        oee_general = week_df["Oee"].mean()
        performans_general = week_df["Performans"].mean()
        kullanılabilirlik_general = week_df["Kullanılabilirlik"].mean()
        kalite_general = week_df["Kalite"].mean()
        
        path = f"Genel/{week} Hafta.png"
        title = f"{week}. Hafta"
        means2png(
            title=title, 
            oee=oee_general, 
            performans=performans_general,
            kullanılabilirlik=kullanılabilirlik_general, 
            kalite=kalite_general, 
            path=path
        )

        # Kısımlara göre
        for kisim in week_df["KISIM"].unique():
            if kisim == "Diğer":
                continue
                
            kisim_df = week_df[week_df["KISIM"] == kisim]
            
            if len(kisim_df) == 0:
                continue
                
            oee_part = kisim_df["Oee"].mean()
            performans_part = kisim_df["Performans"].mean()
            kullanılabilirlik_part = kisim_df["Kullanılabilirlik"].mean()
            kalite_part = kisim_df["Kalite"].mean()
            
            path = f"Kısımlar/{week} Hafta/{kisim}.png"
            title = f"{kisim}"
            means2png(
                title=title, 
                oee=oee_part, 
                performans=performans_part, 
                kullanılabilirlik=kullanılabilirlik_part, 
                kalite=kalite_part, 
                path=path
            )

        # Tezgahlara göre
        for machine in week_df["İş Merkezi Kodu "].unique():
            machine_df = week_df[week_df["İş Merkezi Kodu "] == machine]
            
            if len(machine_df) == 0:
                continue
                
            oee_machine = machine_df["Oee"].mean()
            performans_machine = machine_df["Performans"].mean()
            kullanılabilirlik_machine = machine_df["Kullanılabilirlik"].mean()
            kalite_machine = machine_df["Kalite"].mean()
            
            path = f"Tezgahlar/{week} Hafta/{machine}.png"
            title = f"{machine}"
            means2png(
                title=title, 
                oee=oee_machine, 
                performans=performans_machine,
                kullanılabilirlik=kullanılabilirlik_machine, 
                kalite=kalite_machine, 
                path=path
            )
    
    # Ardışık iki haftanın karşılaştırmasını yap
    if len(weeks) >= 2:
        second_week = weeks[1]  # İkinci en son hafta
        last_week = weeks[0]  # En son hafta
        
        image1_path = f"Raporlar/Tee/Genel/{second_week} Hafta.png"
        image2_path = f"Raporlar/Tee/Genel/{last_week} Hafta.png"
        output_path = f"Raporlar/Tee/Genel/{second_week}-{last_week} Hafta.png"
        
        combine_images_horizontal(image1_path, image2_path, output_path)
    
    logger.info("OEE görselleri oluşturuldu.")