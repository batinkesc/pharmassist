"""
Query Augmentation modülü.

Görev:
  - Hasta profili + kullanıcı sorusu → ChromaDB için arama stratejisi üretir
  - Hangi madde numaralarına öncelik verileceğini belirler
  - Hasta flags'lerini filtre olarak aktarır
  - Birden fazla ilaç için ayrı arama planları oluşturur

Klinik mantık:
  - Etkileşim sorusu → 4.5 öncelikli
  - Kontrendikasyon sorusu → 4.3 öncelikli
  - Doz sorusu + böbrek yetmezliği → 4.2[bobrek] öncelikli
  - Gebelik/emzirme → 4.6 öncelikli
  - Yan etki → 4.8 öncelikli
  - Genel kullanım uyarısı → 4.4 öncelikli
"""

import re
from dataclasses import dataclass, field
from loguru import logger

from src.agents.patient_profile import PatientProfile


# ---------------------------------------------------------------------------
# Soru türü tespiti için anahtar kelimeler
# ---------------------------------------------------------------------------

INTERACTION_KEYWORDS = re.compile(
    r"etkile[sş]im|beraber|kombinas|birlikte|yan\s+yana|ilave|ek\s+olarak"
    r"|ile\s+kullan|birlikte\s+ver"
    # Farmakokinetik/farmakodinamik etki değişimi sinyalleri
    r"|etki\s+nas[ıi]l\s+de[gğ]i[sş]|kan\s+d[üu]zeyi|plazma\s+d[üu]zeyi"
    r"|eklenirse|eklenebilir|eklendi[gğ]inde|ba[sş]lan[ıi]rsa|ba[sş]land[ıi][gğ][ıi]nda"
    r"|verili[rn]se|verildi[gğ]inde|[üu]zerine\s+etki|etkiler\s+mi"
    r"|nas[ıi]l\s+etkiler|ne\s+olur|ne\s+de[gğ]i[sş]|de[gğ]i[sş]tirir",
    re.IGNORECASE,
)
CONTRAINDICATION_KEYWORDS = re.compile(
    r"kontrendike|kullan[ıi]labilir\s+mi|verilir\s+mi|uygun\s+mu|yasak|sak[ıi]ncal[ıi]"
    r"|yaz[ıi]labilir\s+mi|kullan[ıi]l[ıi]r\s+m[ıi]|verilebilir\s+mi|verilmeli\s+mi"
    r"|kullanmal[ıi]\s+m[ıi]|reçete\s+edilebilir|kontrendike\s+mi"
    r"|ba[sş]lan[ıi]labilir\s+mi|ba[sş]lanabilir\s+mi|ba[sş]lan[ıi]r\s+m[ıi]"
    r"|ba[sş]lamal[ıi]\s+m[ıi]|ba[sş]lamak\s+uygun|ba[sş]lamas[ıi]\s+uygun"
    r"|endike\s+mi|endike\s+de[gğ]il|kullan[ıi]m[ıi]\s+uygun|alerjisi.*verilebilir|alerji.*kullan",
    re.IGNORECASE,
)
DOSE_KEYWORDS = re.compile(
    r"doz|dozaj|pozoloji|kaç\s+(mg|tablet|kapsül|ml)|ne\s+kadar|miktar"
    r"|doz\s+ayar|azalt|artır|düşür",
    re.IGNORECASE,
)
PREGNANCY_KEYWORDS = re.compile(
    r"gebelik|hamile|laktasyon|emzir|anne\s+sütü|trimester|gebelikte",
    re.IGNORECASE,
)
SIDE_EFFECT_KEYWORDS = re.compile(
    r"yan\s+etki|advers|istenmeyen|reaksiyon|toksisite"
    r"|ba[sş]lad[ıi]|neden\s+olabilir|ilaca\s+ba[gğ]l[ıi]|ilactan\s+m[ıi]"
    r"|bu\s+ilaç.*m[ıi]|sebep\s+olur|yol\s+açar|ortaya\s+çıkt[ıi]"
    r"|şikayet|semptom.*ilaç|ilaç.*semptom"
    # Klinik risk/enfeksiyon sinyalleri — 4.8 bölümüne yönlendirir
    r"|enfeksiyon\s+riski|kanama\s+riski|ödem|hepatotoksisite|nefrotoksisite"
    r"|hipoglisemi|hiperglisemi|laktik\s+asidoz|nöropati|miyopati"
    r"|üriner|genitoüriner|mantar\s+enf|cilt\s+reaksiyon"
    r"|risk\s+hakkında|bu\s+ilaç.*risk|ilaç.*risk\s+ne|ne\s+(tür|gibi)\s+risk",
    re.IGNORECASE,
)
WARNING_KEYWORDS = re.compile(
    r"uyarı|önlem|dikkat|risk|tehlike|güvenlik",
    re.IGNORECASE,
)

# Spesifik tıbbi durumlar — 4.4 özel uyarı bölümü ile eşleşen koşullar
# Bu koşullar soruda geçtiğinde query zenginleştirmede 4.4 içeriği güçlendirilir
SPECIAL_CONDITION_KEYWORDS = re.compile(
    r"feokromasitom|miyastenia\s*gravis|myasteni|parkinson|epilepsi|lupus|porfiri"
    r"|tirotoksikoz|hipertiroidi|hipotiroid|böbrek\s+ta[sş][ıi]|ürolitiyaz"
    r"|glokom|prostat|bph|üreme|çocuk\s+istememe|fertil"
    r"|alkol\s+ba[gğ][ıi]ml[ıi]|miyopati|rabdomiyoliz",
    re.IGNORECASE,
)
OVERDOSE_KEYWORDS = re.compile(
    r"doz\s+aşım|toksik\s+doz|zehirlenme|overdoz",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Klinik Sinonim Haritası — tıbbi kısaltma & eş anlamlı terim genişletme
# ---------------------------------------------------------------------------
# Sorudaki tıbbi kısaltmaları ChromaDB için tam Türkçe karşılıklarına ekler.
# Hem soru türü tespitini hem de semantik retrieval'ı iyileştirir.
# Format: {regex_pattern: "genişletilmiş terim(ler)"}

_SINONIM_HARITASI: list[tuple[re.Pattern, str]] = [
    # ── Böbrek / Renal ───────────────────────────────────────────────────────
    (re.compile(r"\bKBY\b",            re.IGNORECASE), "kronik böbrek yetmezliği renal yetmezlik"),
    (re.compile(r"\bABY\b",            re.IGNORECASE), "akut böbrek yetmezliği renal yetmezlik"),
    (re.compile(r"\bAKI\b",            re.IGNORECASE), "akut böbrek hasarı renal yetmezlik"),
    (re.compile(r"\beGFR\b",           re.IGNORECASE), "tahmini GFR glomerüler filtrasyon böbrek"),
    (re.compile(r"\bCrCl\b",           re.IGNORECASE), "kreatinin klerensi böbrek fonksiyonu"),
    # ── Karaciğer / Hepatik ─────────────────────────────────────────────────
    (re.compile(r"\bKHY\b|\bKCY\b",    re.IGNORECASE), "karaciğer yetmezliği hepatik yetmezlik"),
    (re.compile(r"kc\s*yet",           re.IGNORECASE), "karaciğer yetmezliği hepatik"),
    # ── Kardiyovasküler ──────────────────────────────────────────────────────
    (re.compile(r"\bKY\b",             re.IGNORECASE), "kalp yetmezliği kardiyak yetmezlik"),
    (re.compile(r"\bAF\b",             re.IGNORECASE), "atriyal fibrilasyon aritmisi"),
    (re.compile(r"\bKAH\b",            re.IGNORECASE), "koroner arter hastalığı iskemik kalp"),
    (re.compile(r"\bIHD\b",            re.IGNORECASE), "iskemik kalp hastalığı koroner"),
    (re.compile(r"\bMI\b"),                             "miyokard enfarktüsü kalp krizi"),   # IGNORECASE YOK: Türkçe soru eki "mi" ile çakışmasın
    (re.compile(r"\bHTA\b",            re.IGNORECASE), "hipertansiyon yüksek tansiyon"),
    (re.compile(r"\bDVT\b",            re.IGNORECASE), "derin ven trombozu venöz tromboembolizm"),
    (re.compile(r"\bPE\b",             re.IGNORECASE), "pulmoner emboli akciğer pıhtısı"),
    (re.compile(r"\bVTE\b",            re.IGNORECASE), "venöz tromboembolizm DVT pulmoner emboli"),
    # ── Akciğer / Solunumsal ─────────────────────────────────────────────────
    (re.compile(r"\bCOPD\b",           re.IGNORECASE), "kronik obstrüktif akciğer hastalığı KOAH"),
    (re.compile(r"\bKOAH\b",           re.IGNORECASE), "kronik obstrüktif akciğer hastalığı amfizem bronşit"),
    # ── Diyabet / Metabolik ──────────────────────────────────────────────────
    (re.compile(r"\bT2DM\b|\bT2D\b|\bDM2\b", re.IGNORECASE), "tip 2 diyabet glisemik kontrol insülin direnci"),
    (re.compile(r"\bT1DM\b|\bT1D\b|\bDM1\b", re.IGNORECASE), "tip 1 diyabet insüline bağımlı"),
    (re.compile(r"\bDKA\b",            re.IGNORECASE), "diyabetik ketoasidoz metabolik asidoz"),
    (re.compile(r"\bHHS\b",            re.IGNORECASE), "hiperosmolar hiperglisemik durum diyabet"),
    # ── Laboratuvar / Koagülasyon ────────────────────────────────────────────
    (re.compile(r"\bINR\b",            re.IGNORECASE), "INR protrombin zamanı antikoagülan koagülasyon"),
    (re.compile(r"\bHbA1c\b",          re.IGNORECASE), "hemoglobin A1c glisemik kontrol diyabet izlem"),
    (re.compile(r"\bLDL\b",            re.IGNORECASE), "LDL kolesterol düşük dansiteli lipoprotein"),
    (re.compile(r"\bHDL\b",            re.IGNORECASE), "HDL kolesterol yüksek dansiteli lipoprotein"),
    # ── İlaç Sınıfları / Kısaltmalar ────────────────────────────────────────
    (re.compile(r"\bNSAİİ\b|\bNSAID\b",     re.IGNORECASE), "steroid olmayan antiinflamatuar ibuprofen diklofenak"),
    (re.compile(r"\bACEi\b|ACE\s*inh",      re.IGNORECASE), "ACE inhibitörü anjiyotensin dönüştürücü enzim lisinopril"),
    (re.compile(r"\bARB\b",                  re.IGNORECASE), "anjiyotensin reseptör blokörü valsartan losartan"),
    (re.compile(r"\bBB\b",                   re.IGNORECASE), "beta bloker metoprolol bisoprolol atenolol"),
    (re.compile(r"\bCCB\b",                  re.IGNORECASE), "kalsiyum kanal blokörü amlodipin nifedipin"),
    (re.compile(r"\bSSRI\b",                 re.IGNORECASE), "selektif serotonin geri alım inhibitörü sertralin fluoksetin"),
    (re.compile(r"\bTCA\b",                  re.IGNORECASE), "trisiklik antidepresan amitriptilin imipramin"),
    (re.compile(r"\bDMAH\b|\bLMWH\b",        re.IGNORECASE), "düşük molekül ağırlıklı heparin enoksaparin nadroparin"),
    (re.compile(r"\bASA\b",                  re.IGNORECASE), "asetilsalisilik asit aspirin antiplatelet"),
    (re.compile(r"\bPPI\b",                  re.IGNORECASE), "proton pompa inhibitörü omeprazol pantoprazol"),
    (re.compile(r"\bSGLT2\b|\bSGLT-2\b",     re.IGNORECASE), "SGLT-2 inhibitörü empagliflozin dapagliflozin"),
    (re.compile(r"\bGLP.?1\b",               re.IGNORECASE), "GLP-1 agonist semaglutid liraglutid"),
    # ── Klinik Durumlar (Türkçe kısaltma) ───────────────────────────────────
    (re.compile(r"\bSVO\b|\bİVO\b",          re.IGNORECASE), "serebrovasküler olay inme iskemik felç"),
    (re.compile(r"\bTIA\b",                  re.IGNORECASE), "geçici iskemik atak mini inme"),
    (re.compile(r"\bRAS\b",                  re.IGNORECASE), "romatoid artrit eklem inflamasyonu"),
    (re.compile(r"\bSLE\b",                  re.IGNORECASE), "sistemik lupus eritematöz otoimmün"),
    (re.compile(r"\bMS\b",                   re.IGNORECASE), "multipl skleroz nörolojik demyelinizan"),
    # ── Klinik Eşanlamlılar / Varyantlar ────────────────────────────────────
    (re.compile(r"hiperpotasemi",            re.IGNORECASE), "hiperkalemi yüksek potasyum elektrolit"),
    (re.compile(r"hiperkalemi",              re.IGNORECASE), "hiperpotasemi yüksek potasyum elektrolit"),
    (re.compile(r"hipopotasemi|hipokalemi",  re.IGNORECASE), "düşük potasyum potasyum eksikliği elektrolit"),
    (re.compile(r"üriner\s*(enfeksiyon|infeksiyon)", re.IGNORECASE), "idrar yolu enfeksiyonu UTI sistit"),
    (re.compile(r"idrar\s*yolu\s*(enfeksiyon|infeksiyon)", re.IGNORECASE), "üriner enfeksiyon UTI sistit"),
    (re.compile(r"\bQTc?\s*(uzamas|prolongat)", re.IGNORECASE), "QT uzaması Torsades de Pointes ventriküler aritmi kardiyak"),
    (re.compile(r"torsade",                  re.IGNORECASE), "QT uzaması ventriküler aritmi kardiyak"),
    (re.compile(r"siroz",                    re.IGNORECASE), "karaciğer sirozu hepatik yetmezlik Child-Pugh"),
    (re.compile(r"feokromas[iy]toma",        re.IGNORECASE), "feokromasitoma feokromositoma adrenal tümör hipertansif kriz"),
    (re.compile(r"miyastenia\s*gravis",      re.IGNORECASE), "myasthenia gravis nöromüsküler kavşak kas"),
    (re.compile(r"gut\s*(hastalığı|artriti)?|gut\b", re.IGNORECASE), "gut ürik asit hiperurisemi artrit"),
    (re.compile(r"epilepsi",                 re.IGNORECASE), "epilepsi nöbet antiepileptik konvülsiyon"),
    (re.compile(r"konvülsiyon|nöbet",        re.IGNORECASE), "epilepsi konvülsiyon antiepileptik"),
    (re.compile(r"anksiyete|kaygı\s*bozukluğu", re.IGNORECASE), "anksiyete bozukluğu kaygı panik"),
    (re.compile(r"depresyon",                re.IGNORECASE), "major depresif bozukluk antidepresan duygudurum"),
    # ── INN ↔ Marka Köprüsü ─────────────────────────────────────────────────
    # Yönlü: hem marka→INN hem INN→marka semantik eşleşmeyi artırır
    (re.compile(r"\bPLAVIX\b",              re.IGNORECASE), "klopidogrel antiplatelet trombosit"),
    (re.compile(r"\bklopidogrel\b",         re.IGNORECASE), "PLAVIX antiplatelet trombosit"),
    (re.compile(r"\bJARDIANCE\b",           re.IGNORECASE), "empagliflozin SGLT-2 inhibitörü diyabet"),
    (re.compile(r"\bempagliflozin\b",       re.IGNORECASE), "JARDIANCE SGLT-2 inhibitörü diyabet"),
    (re.compile(r"\bCYMBALTA\b",            re.IGNORECASE), "duloksetin SNRI serotonin noradrenalin antidepresan"),
    (re.compile(r"\bduloksetin\b",          re.IGNORECASE), "CYMBALTA SNRI antidepresan"),
    (re.compile(r"\bCANDİDİN\b|CANDİDİN",  re.IGNORECASE), "flukonazol antifungal mantar"),
    (re.compile(r"\bflukonazol\b",          re.IGNORECASE), "CANDİDİN antifungal mantar azol"),
    (re.compile(r"\bNORODOL\b",             re.IGNORECASE), "haloperidol antipsikotik dopamin"),
    (re.compile(r"\bhaloperidol\b",         re.IGNORECASE), "NORODOL antipsikotik dopamin"),
    (re.compile(r"\bSANORONE\b|\bCORDARONE\b", re.IGNORECASE), "amiodaron antiaritmik potasyum kanal"),
    (re.compile(r"\bamiodaron\b",           re.IGNORECASE), "SANORONE CORDARONE antiaritmik"),
    (re.compile(r"\bALTİZEM\b",             re.IGNORECASE), "diltiazem kalsiyum kanal blokörü antiaritmik"),
    (re.compile(r"\bdiltiazem\b",           re.IGNORECASE), "ALTİZEM kalsiyum kanal blokörü"),
    (re.compile(r"\bSPORANOX\b",            re.IGNORECASE), "itrakonazol antifungal azol CYP3A4"),
    (re.compile(r"\bitrakonazol\b",         re.IGNORECASE), "SPORANOX antifungal azol CYP3A4"),
    (re.compile(r"\bCLEXANE\b",             re.IGNORECASE), "enoksaparin düşük moleküler ağırlıklı heparin DMAH"),
    (re.compile(r"\benoksaparin\b",         re.IGNORECASE), "CLEXANE DMAH antikoagülan heparin"),
    (re.compile(r"\bTEGRETOL\b",            re.IGNORECASE), "karbamazepin antiepileptik CYP3A4 indüktör"),
    (re.compile(r"\bkarbamazepin\b",        re.IGNORECASE), "TEGRETOL antiepileptik CYP indüktör"),
    (re.compile(r"\bLAMICTAL\b",            re.IGNORECASE), "lamotrijin antiepileptik"),
    (re.compile(r"\blamotrijin\b",          re.IGNORECASE), "LAMICTAL antiepileptik"),
    (re.compile(r"\bRENITEC\b",             re.IGNORECASE), "enalapril ACE inhibitörü anjiyotensin hipertansiyon"),
    (re.compile(r"\benalapril\b",           re.IGNORECASE), "RENITEC ACE inhibitörü hipertansiyon"),
    (re.compile(r"\bCOLCHICUM\b",           re.IGNORECASE), "kolşisin gut antiinflamatuar"),
    (re.compile(r"\bkolşisin\b",            re.IGNORECASE), "COLCHICUM gut ürik asit antiinflamatuar"),
    (re.compile(r"\bONAXAN\b",              re.IGNORECASE), "oksazepam benzodiyazepin anksiyolitik"),
    (re.compile(r"\bokzazepam\b|\boksazepam\b", re.IGNORECASE), "ONAXAN benzodiyazepin anksiyolitik"),
    (re.compile(r"\bISOPTIN\b|\bİSOPTİN\b", re.IGNORECASE), "verapamil kalsiyum kanal blokörü antiaritmik"),
    (re.compile(r"\bverapamil\b",           re.IGNORECASE), "ISOPTIN İSOPTİN kalsiyum kanal blokörü"),
    # ── Antikoagülanlar / Antitrombotikler ──────────────────────────────────
    (re.compile(r"\bELIQUIS\b",             re.IGNORECASE), "apiksaban direkt oral antikoagülan faktör Xa"),
    (re.compile(r"\bapiksaban\b",           re.IGNORECASE), "ELIQUIS DOAC oral antikoagülan"),
    (re.compile(r"\bPRADAXA\b",             re.IGNORECASE), "dabigatran direkt trombin inhibitörü oral antikoagülan"),
    (re.compile(r"\bdabigatran\b",          re.IGNORECASE), "PRADAXA DOAC oral antikoagülan"),
    (re.compile(r"\bDOAC\b|\bNOAK\b",       re.IGNORECASE), "direkt oral antikoagülan yeni oral antikoagülan apiksaban dabigatran rivaroksaban"),
    # ── Kardiyovasküler / Beta Bloker ────────────────────────────────────────
    (re.compile(r"\bNORVASC\b",             re.IGNORECASE), "amlodipin kalsiyum kanal blokörü dihidropiridin hipertansiyon"),
    (re.compile(r"\bamlodipin\b",           re.IGNORECASE), "NORVASC kalsiyum kanal blokörü CCB"),
    (re.compile(r"\bBELOC\b",              re.IGNORECASE), "metoprolol beta bloker kardiyoselektif"),
    (re.compile(r"\bmetoprolol\b",          re.IGNORECASE), "BELOC beta bloker BB"),
    (re.compile(r"\bCONCOR\b|\bBIVOLEN\b", re.IGNORECASE), "bisoprolol beta bloker kardiyoselektif"),
    (re.compile(r"\bbisoprolol\b",          re.IGNORECASE), "CONCOR BIVOLEN beta bloker BB"),
    (re.compile(r"\bARLEC\b|\bCALBICOR\b|\bCARVEXAL\b", re.IGNORECASE), "karvedilol alfa-beta bloker kalp yetmezliği"),
    (re.compile(r"\bkarvedilol\b",          re.IGNORECASE), "ARLEC CALBICOR alfa-beta bloker"),
    # ── ARB / Diüretik ───────────────────────────────────────────────────────
    (re.compile(r"\bCOZAAR\b",              re.IGNORECASE), "losartan anjiyotensin reseptör blokörü ARB"),
    (re.compile(r"\blosartan\b",            re.IGNORECASE), "COZAAR ARB anjiyotensin reseptör"),
    (re.compile(r"\bDIOVAN\b|\bCO.DIOVAN\b", re.IGNORECASE), "valsartan anjiyotensin reseptör blokörü ARB"),
    (re.compile(r"\bvalsartan\b",           re.IGNORECASE), "DIOVAN CO-DIOVAN ARB hipertansiyon"),
    (re.compile(r"\bALDACTONE\b",          re.IGNORECASE), "spironolakton potasyum tutucu diüretik aldosteron antagonisti"),
    (re.compile(r"\bspironolakton\b",       re.IGNORECASE), "ALDACTONE potasyum tutucu diüretik"),
    (re.compile(r"\bLASIX\b",              re.IGNORECASE), "furosemid loop diüretik"),
    (re.compile(r"\bfurosemid\b",          re.IGNORECASE), "LASIX loop diüretik"),
    (re.compile(r"\bDIGOXIN.ASSOS\b",      re.IGNORECASE), "digoksin kardiyak glikozit kalp yetmezliği atriyal fibrilasyon"),
    (re.compile(r"\bdigoksin\b",            re.IGNORECASE), "DIGOXIN kardiyak glikozit"),
    # ── ACE İnhibitörleri ────────────────────────────────────────────────────
    (re.compile(r"\bAPRIL.ACE\b|\bRILACE\b", re.IGNORECASE), "ramipril ACE inhibitörü anjiyotensin hipertansiyon"),
    (re.compile(r"\bramipril\b",            re.IGNORECASE), "APRIL-ACE RILACE ACE inhibitörü"),
    (re.compile(r"\bACEPER\b",             re.IGNORECASE), "perindopril ACE inhibitörü anjiyotensin"),
    (re.compile(r"\bperindopril\b",         re.IGNORECASE), "ACEPER ACE inhibitörü"),
    # ── Statinler ────────────────────────────────────────────────────────────
    (re.compile(r"\bLIPITOR\b|\bTORVENTA\b", re.IGNORECASE), "atorvastatin statin HMG-CoA redüktaz kolesterol"),
    (re.compile(r"\batorvastatin\b",        re.IGNORECASE), "LIPITOR TORVENTA statin kolesterol"),
    (re.compile(r"\bCRESTOR\b|\bPLASOBIN\b|\bPLASOBER\b", re.IGNORECASE), "rosuvastatin statin HMG-CoA kolesterol"),
    (re.compile(r"\brosuvastatin\b",        re.IGNORECASE), "CRESTOR statin kolesterol"),
    # ── Diyabet ─────────────────────────────────────────────────────────────
    (re.compile(r"\bAMARYL\b|\bDIAMEPRID\b", re.IGNORECASE), "glimepirid sülfonilüre insülin sekresyon diyabet"),
    (re.compile(r"\bglimepirid\b",          re.IGNORECASE), "AMARYL DIAMEPRID sülfonilüre diyabet"),
    (re.compile(r"\bDIAMICRON\b",          re.IGNORECASE), "gliklazid sülfonilüre diyabet"),
    (re.compile(r"\bgliklazid\b",           re.IGNORECASE), "DIAMICRON sülfonilüre diyabet"),
    (re.compile(r"\bJANUVIA\b",             re.IGNORECASE), "sitagliptin DPP-4 inhibitörü diyabet glukoz"),
    (re.compile(r"\bsitagliptin\b",         re.IGNORECASE), "JANUVIA DPP-4 diyabet"),
    (re.compile(r"\bDPP.?4\b",             re.IGNORECASE), "dipeptidil peptidaz-4 inhibitörü sitagliptin gliptin diyabet"),
    (re.compile(r"\bVICTOZA\b",            re.IGNORECASE), "liraglutid GLP-1 agonist diyabet"),
    (re.compile(r"\bliraglutid\b",          re.IGNORECASE), "VICTOZA GLP-1 agonist diyabet"),
    (re.compile(r"\bGLUCOBAY\b",           re.IGNORECASE), "akarboz alfa glukozidaz inhibitörü diyabet karbonhidrat"),
    (re.compile(r"\bakarboz\b",             re.IGNORECASE), "GLUCOBAY alfa glukozidaz diyabet"),
    (re.compile(r"\bMETAFORMAL\b",         re.IGNORECASE), "metformin biguanid diyabet insülin direnci"),
    (re.compile(r"\bmetformin\b",           re.IGNORECASE), "METAFORMAL biguanid diyabet"),
    # ── Antidepresanlar / Psikiyatri ─────────────────────────────────────────
    (re.compile(r"\bCIPRALEX\b",           re.IGNORECASE), "essitalopram SSRI antidepresan serotonin"),
    (re.compile(r"\bessitalopram\b",        re.IGNORECASE), "CIPRALEX SSRI antidepresan"),
    (re.compile(r"\bLUSTRAL\b",            re.IGNORECASE), "sertralin SSRI antidepresan serotonin"),
    (re.compile(r"\bsertralin\b",           re.IGNORECASE), "LUSTRAL SSRI antidepresan"),
    (re.compile(r"\bLAROXYL\b",            re.IGNORECASE), "amitriptilin trisiklik antidepresan TCA"),
    (re.compile(r"\bamitriptilin\b",        re.IGNORECASE), "LAROXYL TCA trisiklik antidepresan"),
    (re.compile(r"\bEFEXOR\b|\bFAXIVEN\b", re.IGNORECASE), "venlafaksin SNRI serotonin noradrenalin antidepresan"),
    (re.compile(r"\bvenlafaksin\b",         re.IGNORECASE), "EFEXOR FAXIVEN SNRI antidepresan"),
    (re.compile(r"\bDEPREXINAT\b",         re.IGNORECASE), "mirtazapin noradrenerjik antidepresan"),
    (re.compile(r"\bmirtazapin\b",          re.IGNORECASE), "DEPREXINAT antidepresan"),
    (re.compile(r"\bANKEP\b",              re.IGNORECASE), "ketiapin antipsikotik atipik"),
    (re.compile(r"\bketiapin\b",            re.IGNORECASE), "ANKEP antipsikotik atipik"),
    (re.compile(r"\bXANAX\b",              re.IGNORECASE), "alprazolam benzodiyazepin anksiyolitik"),
    (re.compile(r"\balprazolam\b",          re.IGNORECASE), "XANAX benzodiyazepin anksiyolitik"),
    (re.compile(r"\bMAOI\b|\bMAOİ\b",      re.IGNORECASE), "monoamin oksidaz inhibitörü serotonin sendromu"),
    # ── Antibiyotikler ───────────────────────────────────────────────────────
    (re.compile(r"\bAUGMENTIN\b",          re.IGNORECASE), "amoksisilin klavülanat beta laktam antibiyotik penisilin"),
    (re.compile(r"\bamoksisilin\b",         re.IGNORECASE), "AUGMENTIN penisilin beta laktam antibiyotik"),
    (re.compile(r"\bKLACID\b",             re.IGNORECASE), "klaritromisin makrolid antibiyotik CYP3A4 inhibitörü"),
    (re.compile(r"\bklaritromisin\b",       re.IGNORECASE), "KLACID makrolid antibiyotik CYP3A4"),
    (re.compile(r"\bCIPRO\b",              re.IGNORECASE), "siprofloksasin florokinolon antibiyotik"),
    (re.compile(r"\bsiprofloksasin\b",      re.IGNORECASE), "CIPRO florokinolon antibiyotik"),
    (re.compile(r"\bZITOREL\b",            re.IGNORECASE), "azitromisin makrolid antibiyotik"),
    (re.compile(r"\bazitromisin\b",         re.IGNORECASE), "ZITOREL makrolid antibiyotik"),
    (re.compile(r"\bFLAGYL\b",             re.IGNORECASE), "metronidazol antibiyotik antiparaziter anaerobik"),
    (re.compile(r"\bmetronidazol\b",        re.IGNORECASE), "FLAGYL antibiyotik anaerobik"),
    (re.compile(r"\bAVELOX\b",             re.IGNORECASE), "moksifloksasin florokinolon antibiyotik"),
    (re.compile(r"\bmoksifloksasin\b",      re.IGNORECASE), "AVELOX florokinolon antibiyotik"),
    # ── Antiepileptikler ─────────────────────────────────────────────────────
    (re.compile(r"\bDEPALEX\b|\bPROKSIVAL\b|\bVALEPTIK\b", re.IGNORECASE), "valproat valproik asit antiepileptik duygudurum dengeleyici"),
    (re.compile(r"\bvalproat\b|\bvalproik\s*asit\b",         re.IGNORECASE), "DEPALEX PROKSIVAL VALEPTIK antiepileptik"),
    (re.compile(r"\bNEURONTIN\b",          re.IGNORECASE), "gabapentin antiepileptik nöropatik ağrı"),
    (re.compile(r"\bgabapentin\b",          re.IGNORECASE), "NEURONTIN antiepileptik nöropatik ağrı"),
    (re.compile(r"\bKEPPRA\b",             re.IGNORECASE), "levetirasetam antiepileptik nöbet"),
    (re.compile(r"\blevetirasetam\b",       re.IGNORECASE), "KEPPRA antiepileptik"),
    (re.compile(r"\bEPANUTIN\b|\bEPDANTOIN\b|\bFENITOSEL\b", re.IGNORECASE), "fenitoin antiepileptik nöbet CYP indüktörü"),
    (re.compile(r"\bfenitoin\b",            re.IGNORECASE), "EPANUTIN EPDANTOIN antiepileptik CYP indüktörü"),
    # ── Tiroid ───────────────────────────────────────────────────────────────
    (re.compile(r"\bEUTHYROX\b",           re.IGNORECASE), "levotiroksin tiroid hormonu hipotiroidizm"),
    (re.compile(r"\blevotiroksin\b",        re.IGNORECASE), "EUTHYROX tiroid hormonu"),
    (re.compile(r"\bPROPYCIL\b",           re.IGNORECASE), "propiltiourasil antitiroid tirotoksikoz"),
    (re.compile(r"\bpropiltiourasil\b",     re.IGNORECASE), "PROPYCIL antitiroid"),
    # ── PPI / Gastrik ────────────────────────────────────────────────────────
    (re.compile(r"\bLOSEC\b|\bGERDOPAN\b", re.IGNORECASE), "omeprazol proton pompa inhibitörü PPI mide"),
    (re.compile(r"\bomeprazol\b",           re.IGNORECASE), "LOSEC proton pompa inhibitörü PPI"),
    (re.compile(r"\bPANTPAS\b",            re.IGNORECASE), "pantoprazol proton pompa inhibitörü PPI mide"),
    (re.compile(r"\bpantoprazol\b",         re.IGNORECASE), "PANTPAS PPI proton pompa inhibitörü"),
    (re.compile(r"\bLANSOR\b",             re.IGNORECASE), "lansoprazol proton pompa inhibitörü PPI"),
    (re.compile(r"\blansoprazol\b",         re.IGNORECASE), "LANSOR PPI proton pompa inhibitörü"),
    (re.compile(r"\bESNEKS\b|\bESMARA\b|\bESOM\b", re.IGNORECASE), "esomeprazol proton pompa inhibitörü PPI"),
    (re.compile(r"\besomeprazol\b",         re.IGNORECASE), "ESNEKS ESMARA ESOM PPI"),
    (re.compile(r"\bPARIET\b|\bPATRIL\b",  re.IGNORECASE), "rabeprazol proton pompa inhibitörü PPI"),
    (re.compile(r"\brabeprazol\b",          re.IGNORECASE), "PARIET PATRIL PPI proton pompa inhibitörü"),
    # ── NSAID / Ağrı Kesici ──────────────────────────────────────────────────
    (re.compile(r"\bVOLTAREN\b",           re.IGNORECASE), "diklofenak NSAID antiinflamatuar analjezik"),
    (re.compile(r"\bdiklofenak\b",          re.IGNORECASE), "VOLTAREN NSAID antiinflamatuar"),
    (re.compile(r"\bBRUFEN\b",             re.IGNORECASE), "ibuprofen NSAID antiinflamatuar analjezik ateş"),
    (re.compile(r"\bibuprofen\b",           re.IGNORECASE), "BRUFEN NSAID antiinflamatuar"),
    (re.compile(r"\bCELEBREX\b|\bCELGYN\b|\bELOXIB\b|\bSELKAP\b", re.IGNORECASE), "selekoksib COX-2 inhibitörü NSAID"),
    (re.compile(r"\bselekoksib\b",          re.IGNORECASE), "CELEBREX CELGYN COX-2 NSAID"),
    (re.compile(r"\bNAPROSYN\b",           re.IGNORECASE), "naproksen NSAID antiinflamatuar"),
    (re.compile(r"\bnaproksen\b",           re.IGNORECASE), "NAPROSYN NSAID antiinflamatuar"),
    (re.compile(r"\bENFLAR\b|\bEXEN\b|\bLOXIDOL\b", re.IGNORECASE), "meloksikam NSAID COX-2 selektif antiinflamatuar"),
    (re.compile(r"\bmeloksikam\b",          re.IGNORECASE), "ENFLAR EXEN LOXIDOL NSAID"),
    (re.compile(r"\bCONTRAMAL\b",          re.IGNORECASE), "tramadol opioid analjezik ağrı kesici"),
    (re.compile(r"\btramadol\b",            re.IGNORECASE), "CONTRAMAL opioid analjezik"),
    # ── Antiemetik / Diğer ───────────────────────────────────────────────────
    (re.compile(r"\bZOFRAN\b",             re.IGNORECASE), "ondansetron antiemetik seratonin 5-HT3 bulantı kusma"),
    (re.compile(r"\bondansetron\b",         re.IGNORECASE), "ZOFRAN antiemetik bulantı"),
    (re.compile(r"\bFOSAMAX\b",            re.IGNORECASE), "alendronat bifosfonat osteoporoz kemik"),
    (re.compile(r"\balendronat\b",          re.IGNORECASE), "FOSAMAX bifosfonat osteoporoz"),
    (re.compile(r"\bIMMURAN\b|\bIMURAN\b", re.IGNORECASE), "azatiyoprin immunsüpresif pürin antimetabolit"),
    (re.compile(r"\bazatiyoprin\b",         re.IGNORECASE), "IMURAN immunsüpresif"),
    (re.compile(r"\bURIKOLIZ\b|\bUZORİK\b", re.IGNORECASE), "allopurinol ksantin oksidaz inhibitörü ürik asit gut"),
    (re.compile(r"\ballopurinol\b",         re.IGNORECASE), "URIKOLIZ gut ürik asit"),
    (re.compile(r"\bDELTACORTRIL\b|\bPRECORT\b", re.IGNORECASE), "prednizolon prednizon kortikosteroid steroid"),
    (re.compile(r"\bprednizolon\b|\bprednizon\b", re.IGNORECASE), "DELTACORTRIL PRECORT kortikosteroid steroid"),
    (re.compile(r"\bDROSPORIN\b|\bCYLORIN\b", re.IGNORECASE), "siklosporin kalsinörin inhibitörü immunsüpresif"),
    (re.compile(r"\bsiklosporin\b",         re.IGNORECASE), "DROSPORIN CYLORIN immunsüpresif"),
    (re.compile(r"\bCORDALIN\b",           re.IGNORECASE), "amiodaron antiaritmik potasyum kanal"),
    # ── Ek Klinik Durumlar ───────────────────────────────────────────────────
    (re.compile(r"hipotiroidizm|hipotiroidi\b", re.IGNORECASE), "tiroid yetersizliği levotiroksin TSH yüksek"),
    (re.compile(r"hipertiroidizm|hipertiroidi\b", re.IGNORECASE), "tirotoksikoz Graves hastalığı tiroid aşırı"),
    (re.compile(r"osteoporoz",              re.IGNORECASE), "kemik erimesi kemik mineral yoğunluğu bifosfonat"),
    (re.compile(r"kemik\s*(erime|kayb)",   re.IGNORECASE), "osteoporoz osteopeni kemik mineral yoğunluğu"),
    (re.compile(r"anemi|kansızlık",        re.IGNORECASE), "hemoglobin düşüklüğü demir eksikliği eritrosit"),
    (re.compile(r"trombositopeni",         re.IGNORECASE), "düşük trombosit kanama riski platelet"),
    (re.compile(r"nötropeni",              re.IGNORECASE), "düşük nötrofil enfeksiyon riski lökopeni immunsüpresyon"),
    (re.compile(r"sepsis|septik\s*şok",    re.IGNORECASE), "sistemik enfeksiyon bakteriyemi organ yetmezliği"),
    (re.compile(r"pnömoni|zatürre",        re.IGNORECASE), "akciğer enfeksiyonu solunum yolu enfeksiyonu"),
    (re.compile(r"migren",                 re.IGNORECASE), "migren baş ağrısı vasküler nörolojik"),
    (re.compile(r"parkinson\s*(hastalığı)?", re.IGNORECASE), "Parkinson dopamin eksikliği nörodejeneratif hareket"),
    (re.compile(r"alzheimer|demans",       re.IGNORECASE), "Alzheimer demans kognitif bozukluk nörodejeneratif"),
    (re.compile(r"osteoartrit|kireçlenme", re.IGNORECASE), "osteoartrit dejeneratif artrit eklem aşınması"),
    (re.compile(r"reflü|GERD",             re.IGNORECASE), "gastroözofageal reflü asit PPI mide yanması"),
    (re.compile(r"psöriyazis|sedef\s*hastalığı", re.IGNORECASE), "psöriyazis sedef deri otoimmün"),
    (re.compile(r"kanser|malignite|tümör|neoplazi", re.IGNORECASE), "kanser malignite tümör neoplazi onkoloji"),
    (re.compile(r"hiperurisemi",           re.IGNORECASE), "yüksek ürik asit gut hiperurisemi allopurinol"),
    # ── Ek Laboratuvar Değerleri ─────────────────────────────────────────────
    (re.compile(r"\bTSH\b",               re.IGNORECASE), "tiroid stimülan hormon tiroid fonksiyon hipotiroidizm"),
    (re.compile(r"\bFT4\b|\bT4\b",        re.IGNORECASE), "tiroksin serbest tiroksin tiroid hormonu"),
    (re.compile(r"\bCRP\b",               re.IGNORECASE), "C-reaktif protein inflamasyon belirteci"),
    (re.compile(r"\bD.dimer\b",           re.IGNORECASE), "D-dimer venöz tromboembolizm DVT pıhtı koagülasyon"),
    (re.compile(r"\bferritin\b",          re.IGNORECASE), "ferritin demir deposu anemi demir eksikliği"),
    (re.compile(r"\bB12\b",              re.IGNORECASE), "vitamin B12 kobalamin anemi nöropati eksikliği"),
    (re.compile(r"\bPSA\b",              re.IGNORECASE), "prostat spesifik antijen prostat"),
    (re.compile(r"\bBNP\b|\bNT.proBNP\b", re.IGNORECASE), "beyin natriüretik peptit kalp yetmezliği kardiyak"),
    (re.compile(r"\bHBA\b|\beGFR\b",     re.IGNORECASE), "glomerüler filtrasyon böbrek fonksiyon"),
    # ── Formülasyon / Uygulama Yolu ─────────────────────────────────────────
    (re.compile(r"\bSR\b|\bXR\b|\bMR\b|\bER\b", re.IGNORECASE), "yavaş salınımlı uzatılmış salınım modifiye salım"),
    (re.compile(r"\bIV\b|\bI\.V\.",       re.IGNORECASE), "intravenöz damar içi infüzyon enjeksiyon"),
    (re.compile(r"\bIM\b|\bI\.M\.",       re.IGNORECASE), "intramüsküler kas içi enjeksiyon"),
    (re.compile(r"\bSC\b|\bSQ\b|\bS\.C\.", re.IGNORECASE), "subkutan deri altı enjeksiyon"),
    # ── Ek İlaç Sınıfı Kısaltmaları ─────────────────────────────────────────
    (re.compile(r"\bJAKi\b|\bJAK\s*inh", re.IGNORECASE), "JAK inhibitörü barisitenib tofasitenib"),
    (re.compile(r"\bmTOR\b",              re.IGNORECASE), "mTOR inhibitörü sirolimus everolimus immunsüpresif"),
    (re.compile(r"\bSNRI\b",              re.IGNORECASE), "serotonin noradrenalin geri alım inhibitörü duloksetin venlafaksin"),
    (re.compile(r"\bNRI\b",               re.IGNORECASE), "noradrenalin geri alım inhibitörü"),
]


def _apply_synonym_expansion(soru: str) -> str:
    """
    Türkçe tıbbi kısaltma ve eş anlamlıları zenginleştirilmiş forma dönüştürür.

    Orijinal sorguya ekleme yapar — YERİNE GEÇMEz.
    Dönen metin yalnızca ChromaDB semantik araması için kullanılır,
    LLM prompt'una veya kullanıcıya gösterilmez.
    """
    extras: list[str] = []
    for pattern, expansion in _SINONIM_HARITASI:
        if pattern.search(soru):
            extras.append(expansion)

    if extras:
        logger.debug(f"Sinonim genişletme: {len(extras)} eşleşme")
        return soru + " " + " ".join(extras)
    return soru


# ---------------------------------------------------------------------------
# Arama planı veri yapısı
# ---------------------------------------------------------------------------

@dataclass
class SearchPlan:
    """
    Tek bir ilaç için retrieval planı.

    Attributes:
        ilac_adi:       Aranacak ilaç adı (None ise tüm ilaçlar)
        madde_onceligi: Önce bu maddelerde ara (sıralı)
        patient_flags:  Hasta bazlı flag filtreleri
        n_results:      Her aramada kaç sonuç isteniyor
        sorgu:          Zenginleştirilmiş arama sorgusu
    """
    ilac_adi: str | None
    madde_onceligi: list[str]
    patient_flags: list[str]
    n_results: int
    sorgu: str


@dataclass
class AugmentedQuery:
    """
    Tam augmented query çıktısı.

    Attributes:
        ozgun_soru:     Kullanıcının ham sorusu
        soru_turleri:   Tespit edilen soru türleri
        arama_planlari: Her ilaç için SearchPlan listesi
        hasta_ozeti:    Promptta kullanılacak hasta profil özeti
    """
    ozgun_soru: str
    soru_turleri: list[str]
    arama_planlari: list[SearchPlan]
    hasta_ozeti: str


# ---------------------------------------------------------------------------
# Ana augmentation fonksiyonu
# ---------------------------------------------------------------------------

def augment_query(
    soru: str,
    profil: PatientProfile,
    hedef_ilaclar: list[str] | None = None,
    n_results: int = 5,
) -> AugmentedQuery:
    """
    Kullanıcı sorusu + hasta profilini zenginleştirilmiş arama planına çevirir.

    Args:
        soru:          Kullanıcı sorusu (Türkçe)
        profil:        Hasta profili
        hedef_ilaclar: Sorgunun ilgili olduğu ilaçlar (None ise tüm koleksiyon aranır)
        n_results:     Her plan için kaç chunk alınacak

    Returns:
        AugmentedQuery — arama planları ve hasta özeti
    """
    # Klinik kısaltma & sinonim genişletme — yalnızca retrieval için
    soru_expanded = _apply_synonym_expansion(soru)

    soru_turleri = _detect_question_types(soru_expanded, profil)
    madde_onceligi = _prioritize_sections(soru_turleri, profil)
    flags = profil.aktif_flags
    zengin_sorgu = _enrich_query(soru_expanded, profil, soru_turleri)

    # Spesifik tıbbi durum varsa 4.4'ü önce al (kontrendikasyon/uyarı sorgularında)
    if SPECIAL_CONDITION_KEYWORDS.search(soru):
        if "4.4" in madde_onceligi:
            madde_onceligi.remove("4.4")
        madde_onceligi.insert(0, "4.4")
        logger.debug(f"Spesifik tıbbi durum tespit edildi — 4.4 önceliğe alındı")

    logger.debug(f"Soru türleri: {soru_turleri}")
    logger.debug(f"Madde önceliği: {madde_onceligi}")
    logger.debug(f"Aktif flags: {flags}")

    # Her ilaç için ayrı plan (ya da ilaç belirtilmemişse tek genel plan)
    arama_planlari: list[SearchPlan] = []

    if hedef_ilaclar:
        for ilac in hedef_ilaclar:
            plan = SearchPlan(
                ilac_adi=ilac,
                madde_onceligi=madde_onceligi,
                patient_flags=flags,
                n_results=n_results,
                sorgu=zengin_sorgu,
            )
            arama_planlari.append(plan)
    else:
        # Genel arama — ilaç filtresi yok
        arama_planlari.append(SearchPlan(
            ilac_adi=None,
            madde_onceligi=madde_onceligi,
            patient_flags=flags,
            n_results=n_results,
            sorgu=zengin_sorgu,
        ))

    return AugmentedQuery(
        ozgun_soru=soru,
        soru_turleri=soru_turleri,
        arama_planlari=arama_planlari,
        hasta_ozeti=profil.ozet_metin(),
    )


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def _detect_question_types(soru: str, profil: PatientProfile) -> list[str]:
    """Sorunun hangi klinik kategorilere girdiğini tespit eder."""
    turleri = []

    if INTERACTION_KEYWORDS.search(soru):
        turleri.append("etkilesim")
    if CONTRAINDICATION_KEYWORDS.search(soru):
        turleri.append("kontrendikasyon")
    if DOSE_KEYWORDS.search(soru):
        turleri.append("doz")
    if PREGNANCY_KEYWORDS.search(soru) or profil.gebelik or profil.emzirme:
        turleri.append("gebelik_laktasyon")
    if SIDE_EFFECT_KEYWORDS.search(soru):
        turleri.append("yan_etki")
    if WARNING_KEYWORDS.search(soru):
        turleri.append("uyari")
    if OVERDOSE_KEYWORDS.search(soru):
        turleri.append("doz_asimi")

    # Hiçbiri eşleşmediyse genel sorgu
    if not turleri:
        turleri.append("genel")

    return turleri


def _prioritize_sections(soru_turleri: list[str], profil: PatientProfile) -> list[str]:
    """
    Soru türüne göre KÜB madde öncelik sırasını belirler.

    Mantık:
      - Her soru türü bir madde grubuna eşlenir
      - Hasta profili bazlı ekstralar eklenir (böbrek → 4.2, 4.4)
      - Kritik maddeler (4.3, 4.4, 4.5) her zaman dahil edilir
    """
    oncelikli: list[str] = []
    ek: list[str] = []

    for tur in soru_turleri:
        if tur == "etkilesim":
            oncelikli += ["4.5", "4.4"]
        elif tur == "kontrendikasyon":
            oncelikli += ["4.3", "4.4"]
        elif tur == "doz":
            oncelikli += ["4.2"]
        elif tur == "gebelik_laktasyon":
            oncelikli += ["4.6", "4.3"]
        elif tur == "yan_etki":
            oncelikli += ["4.8", "4.4"]
        elif tur == "uyari":
            oncelikli += ["4.4", "4.3"]
        elif tur == "doz_asimi":
            oncelikli += ["4.9"]
        else:  # genel
            oncelikli += ["4.3", "4.4", "4.5"]

    # Temel maddeler her zaman sonuçta olsun
    ek += ["4.3", "4.4", "4.5"]

    # Hasta profili ekstraları
    if profil.bobrek_yetmezligi:
        ek += ["4.2", "4.4"]
    if profil.karaciger_yetmezligi:
        ek += ["4.2", "4.4"]
    if profil.gebelik or profil.emzirme:
        ek += ["4.6"]
    if profil.geriyatrik:
        ek += ["4.2"]

    # Sırayı koru, tekrarları temizle
    seen = set()
    result = []
    for m in oncelikli + ek:
        if m not in seen:
            seen.add(m)
            result.append(m)

    return result


def _enrich_query(soru: str, profil: PatientProfile, soru_turleri: list[str]) -> str:
    """
    Hasta profilini sorguya ekleyerek daha spesifik bir retrieval sorgusu üretir.

    ChromaDB semantik arama için: kısa, yoğun bilgi içerikli metin daha iyi.
    """
    from src.agents.patient_profile import _lab_durumu

    parcalar = [soru]

    if profil.bobrek_yetmezligi:
        parcalar.append(f"böbrek yetmezliği GFR {profil.gfr}")
    if profil.karaciger_yetmezligi:
        parcalar.append(f"karaciğer yetmezliği Child-Pugh {profil.karaciger_skoru}")
    if profil.geriyatrik:
        parcalar.append(f"geriyatrik yaşlı hasta {profil.yas} yaş")
    if profil.pediyatrik:
        parcalar.append(f"pediyatrik çocuk hasta {profil.yas} yaş")
    if profil.gebelik:
        parcalar.append("gebelik hamile")
    if profil.emzirme:
        parcalar.append("laktasyon emzirme")

    if profil.mevcut_ilaclar and "etkilesim" in soru_turleri:
        ilac_metni = " ".join(profil.mevcut_ilaclar[:3])
        parcalar.append(f"ilaç etkileşimi {ilac_metni}")

    # Yan etki soruları için 4.8 semantik bağlamını güçlendir — semptom odaklı
    if "yan_etki" in soru_turleri:
        parcalar.append("yan etki istenmeyen etki advers reaksiyon güvenlilik profili")
        # Spesifik semptom/risk terimleri varsa doğrudan ekle → ilgili 4.8 chunk'ı çeker
        _YAN_ETKI_SPESIFIK = [
            (re.compile(r"üriner|idrar\s+yolu|mesane|genitoüriner", re.IGNORECASE),
             "üriner enfeksiyon genitoüriner idrar yolu"),
            (re.compile(r"kanama|hemoraji|purpura|peteş", re.IGNORECASE),
             "kanama riski hemoraji"),
            (re.compile(r"ödem|şişlik|periferik\s+ödem", re.IGNORECASE),
             "ödem periferik ödem sıvı tutulumu"),
            (re.compile(r"karaciğer|hepatik|sarılık|transaminaz", re.IGNORECASE),
             "hepatotoksisite karaciğer enzim yüksekliği"),
            (re.compile(r"kas\s+ağrı|miyalji|rabdomiyoliz", re.IGNORECASE),
             "miyopati rabdomiyoliz kas toksisitesi"),
            (re.compile(r"mantar|kandida|fungal", re.IGNORECASE),
             "mantar enfeksiyonu kandida fungal"),
        ]
        for pattern, terim in _YAN_ETKI_SPESIFIK:
            if pattern.search(soru):
                parcalar.append(terim)
                break  # Birden fazla eşleşme karmaşıklığı artırır

    # Spesifik tıbbi durum sorularında 4.4 özel uyarı içeriğini güçlendir
    # (feokromasitoma, miyastenia gravis gibi durumlar 4.4'te uyarı olarak geçer)
    special_match = SPECIAL_CONDITION_KEYWORDS.search(soru)
    if special_match:
        condition_term = special_match.group(0)
        parcalar.append(f"özel kullanım uyarısı {condition_term} dikkatli kullanım")

    # Fix #5: Anormal lab değerlerini sorguya ekle — YALNIZCA doz/kontrendikasyon
    # soru türlerinde ve en fazla 1 klinik terim. Diğer soru türlerinde lab
    # değerleri prompt context'ine (hasta profili özetine) bırakılır, sorguya eklenmez.
    # Aksi hâlde alakasız chunk'lar retrieve edilerek LLM bağlamı kirlenir.
    if any(t in soru_turleri for t in ("doz", "kontrendikasyon")):
        # Öncelik sırası: böbrek → karaciğer → elektrolit → INR → HbA1c
        _ONCELIK = [
            (("Kreatinin",), "yüksek",       "böbrek fonksiyon bozukluğu kreatinin yüksek"),
            (("ALT", "AST"), "yüksek",       "karaciğer enzim yüksekliği hepatotoksisite"),
            (("Bilirubin",), "yüksek",       "karaciğer enzim yüksekliği bilirubin"),
            (("K",),         "yüksek",       "hiperkalemi potasyum yüksek"),
            (("K",),         "kritik_düşük", "hipokalemi potasyum düşük"),
            (("INR",),       "yüksek",       "antikoagülan INR yüksek kanama riski"),
            (("HbA1c",),     "yüksek",       "diyabet glisemik kontrol bozuk"),
        ]
        for params, durum_prefix, terim in _ONCELIK:
            for anormal in profil.anormal_lab_degerleri:
                if anormal["param"] in params and durum_prefix in anormal["durum"]:
                    parcalar.append(terim)
                    break  # Sadece en öncelikli lab bulgusunu ekle
            else:
                continue
            break  # İlk eşleşme bulundu — daha fazla ekleme

    return " ".join(parcalar)
