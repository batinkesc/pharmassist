"""
KÜB (Kısa Ürün Bilgisi) standart bölüm tanımları ve metadata şeması.
TİTCK format standardına göre hazırlanmıştır.
"""

# Kritik bölümler: CDSS için öncelikli analiz hedefleri
CRITICAL_SECTIONS = {"4.3", "4.4", "4.5"}
IMPORTANT_SECTIONS = {"4.1", "4.2", "4.6", "4.8", "4.9"}

# KÜB standart bölüm başlıkları (Türkçe)
KUB_SECTION_TITLES = {
    "1":   "Beşeri Tıbbi Ürünün Adı",
    "2":   "Kalitatif ve Kantitatif Bileşim",
    "3":   "Farmasötik Form",
    "4":   "Klinik Özellikler",
    "4.1": "Terapötik Endikasyonlar",
    "4.2": "Pozoloji ve Uygulama Şekli",
    "4.3": "Kontrendikasyonlar",
    "4.4": "Özel Kullanım Uyarıları ve Önlemleri",
    "4.5": "Diğer Tıbbi Ürünlerle Etkileşimler",
    "4.6": "Gebelik ve Laktasyon",
    "4.7": "Araç ve Makine Kullanımı Üzerindeki Etkiler",
    "4.8": "İstenmeyen Etkiler",
    "4.9": "Doz Aşımı",
    "5":   "Farmakolojik Özellikler",
    "5.1": "Farmakodinamik Özellikler",
    "5.2": "Farmakokinetik Özellikler",
    "5.3": "Klinik Öncesi Güvenlilik Verileri",
    "6":   "Farmasötik Özellikler",
    "7":   "Ruhsat Sahibi",
    "8":   "Ruhsat Numarası",
    "9":   "İlk Ruhsat Tarihi / Ruhsat Yenileme Tarihi",
    "10":  "KÜB'ün Yenilenme Tarihi",
}

# Regex deseni: KÜB bölüm başlıklarını tespit eder
# Örnek: "4.3 Kontrendikasyonlar" veya "4.3\nKontrendikasyonlar"
SECTION_HEADING_PATTERNS = [
    # "4.3 Kontrendikasyonlar" - tek satır
    r"^(4\.[1-9](?:\.[0-9])?)\s{1,5}([A-ZÇĞİÖŞÜ][^\n]{5,80})$",
    # Ana bölümler: "5. Farmakolojik özellikler"
    r"^([1-9]|10)\.\s{1,3}([A-ZÇĞİÖŞÜ][^\n]{5,80})$",
    # Nokta olmadan: "4.3  Kontrendikasyonlar"
    r"^(4\.[1-9])\s{2,}([A-ZÇĞİÖŞÜ][^\n]{5,80})$",
]

# Risk seviyeleri (bölüm bazlı)
SECTION_RISK_LEVEL = {
    "4.3": "critical",   # Kontrendikasyon
    "4.4": "warning",    # Uyarılar
    "4.5": "warning",    # Etkileşimler
    "4.8": "info",       # Yan etkiler
    "4.2": "info",       # Dozaj
    "4.6": "info",       # Gebelik
}
