import re
import unicodedata

# PUA (Private Use Area) ve yaygın trademark sembolleri
_TRADEMARK_SYMBOLS = [
    '\u00ae', # ®
    '\u2122', # ™
    '\u00a9', # ©
    '\uf8e8', # PUA Trademark
    '\uf0d2', # PUA dot
    '\uf6da', # PUA
    '\uf8ec',
    '\uf8ef',
    '\uf8f0',
]

_TRADEMARK_RE = re.compile(f"[{''.join(_TRADEMARK_SYMBOLS)}]", re.UNICODE)

_TR_MAP = str.maketrans({
    'İ': 'I',
    'ı': 'i',
    'Ş': 'S',
    'ş': 's',
    'Ç': 'C',
    'ç': 'c',
    'Ğ': 'G',
    'ğ': 'g',
    'Ö': 'O',
    'ö': 'o',
    'Ü': 'U',
    'ü': 'u',
})

def normalize_drug_name(name: str) -> str:
    """
    İlaç adını normalize eder:
    1. Trademark sembollerini kaldırır.
    2. Unicode NFC normalizasyonu uygular.
    3. Türkçe karakterleri İngilizce karşılıklarına çevirir (arama tutarlılığı için).
    4. Birden fazla boşluğu teke indirir.
    5. Küçük harfe çevirir ve trimler.
    """
    if not name:
        return ""
    
    # Unicode NFC normalize
    s = unicodedata.normalize('NFC', name)
    
    # Trademark sembollerini kaldır
    s = _TRADEMARK_RE.sub('', s)
    
    # Türkçe karakter mapping
    s = s.translate(_TR_MAP)
    
    # Birden fazla boşluğu teke indir
    s = re.sub(r'\s+', ' ', s)
    
    return s.strip().upper()

def get_base_name(name: str) -> str:
    """
    İlacın temel adını döndürür (ilk 1-2 kelime).
    Ör: "AUGMENTIN 400 MG TABLET" -> "AUGMENTIN"
    """
    norm = normalize_drug_name(name)
    parts = norm.split()
    if not parts:
        return ""
    
    # Genelde ilk kelime markadır.
    # Eğer ilk kelime çok kısaysa veya özel bir durumsa 2. kelimeyi de alabiliriz.
    return parts[0]
