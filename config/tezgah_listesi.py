"""
Tezgah ve kısım bilgilerini içeren konfigürasyon dosyası.
"""

# Kısım ve tezgah bilgileri
KISIM_2_1 = [
    "CT.D01", "CT.D02", "CT.D03", "CT.D04", "CT.D05", "CT.D06", "CT.D07", "CT.D08", 
    "CT.D09", "CT.D10", "CT.D11", "CT.D12", "CT.G1", "CT.KO1", "CT.KO2"
]

KISIM_2_2 = [
    "İM.K01", "İM.K03", "İM.MK1", "İM.T01", "İM.T02", "İM.V01"
]

KISIM_3_1 = [
    "İM.MV1", "İM.MV2", "İM.MV3", "İM.MV4", "İM.MV5", "İM.MV6", "İM.S01", "İM.S02"
]

KISIM_3_2 = [
    "İM.OM01", "İM.OM02", "İM.OM03", "İM.OM04", "İM.OM05", "İM.OM06", 
    "İM.OM07", "İM.OM08", "İM.OM09", "İM.OM10"
]

KISIM_4_1 = [
    "İM.M1", "İM.M2", "İM.M3", "İM.M4", "İM.M5", "İM.M6", "İM.M7", "İM.M8", "İM.M9", "İM.O05"
]

KISIM_4_2 = [
    "İM.O01", "İM.O02", "İM.O03", "İM.O04", "İM.O06", "İM.O07", "İM.O08", "İM.O09", "İM.O10", "İM.O11"
]

KISIM_5_1 = [
    "T.B01", "T.J01", "T.J02", "T.K01", "T.S01", "T.S02", "T.S03", "T.S04", "T.S05", "T.S06", "T.S07", "T.S08"
]

# Tezgah listelerini bir dictionary ile birleştirelim
KISIMLAR_DICT = {
    "KISIM 2.1": KISIM_2_1,
    "KISIM 2.2": KISIM_2_2,
    "KISIM 3.1": KISIM_3_1,
    "KISIM 3.2": KISIM_3_2,
    "KISIM 4.1": KISIM_4_1,
    "KISIM 4.2": KISIM_4_2,
    "KISIM 5.1": KISIM_5_1
}

# Raporlar için çıktı dizinleri
OUTPUT_DIRS = {
    "main": "Raporlar",
    "tee": "Raporlar/Tee",
    "parts": "Raporlar/Kısımlar",
    "machines": "Raporlar/Tezgahlar",
    "general": "Raporlar/Genel"
}

# Görselleştirme için ayarlar
VISUALIZATION_SETTINGS = {
    "default_figsize": (12, 8),
    "default_dpi": 300,
    "color_palettes": {
        "parts": "Pastel2",
        "machines": "tab20",
        "top_machines": "Reds",
        "bottom_machines": "Greens"
    },
    "threshold": 3  # Diğer gruplama için eşik değer (%)
}