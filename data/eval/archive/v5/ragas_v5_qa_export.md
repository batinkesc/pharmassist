# RAGAS v5 — Soru/Cevap Doğrulama Raporu

**Faithfulness:** 0.6755 | **Context Recall:** 0.8646
**Toplam Soru:** 33 | **Evaluator:** local

---

## [v3_q01] Soru 1
**Scores:** Faithfulness=0.833 | Context Recall=0.250

**Soru:** TEGRETOL kullanan hastaya SANORONE eklenebilir mi?

**Ground Truth:**
Karbamazepin (TEGRETOL) ile amiodaron (SANORONE) kombinasyonu kontrendike değildir ancak her ikisi de CYP3A4 substratıdır; karbamazepin güçlü CYP3A4 indükleyicisi olarak amiodaronun plazma düzeyini düşürür. Birlikte kullanımda dikkatli olunmalı, kardiyak izlem yapılmalıdır.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hayır, SANORONE eklenemez. TEGRETOL kullanımı ile ilişkili olarak aplastik anemi ve agranülositoz bildirilmiştir. Bazen TEGRETOL kullanımı ile ilişkili olarak, trombosit veya lökosit sayısında geçici veya kalıcı bir azalma oluşur. Bu nedenle, SANORONE eklenmesine karşı özel kullanım uyarıları vardır.

### 2. Detaylı Analiz
TEGRETOL kullanımı ile ilişkili olarak aplastik anemi ve agranülositoz bildirilmiştir (KÜB Madde 4.4). Bazen TEGRETOL kullanımı ile ilişkili olarak, trombosit veya lökosit sayısında geçici veya kalıcı bir azalma oluşur (KÜB Madde 4.4). Bu nedenle, SANORONE eklenmesine karşı özel kullanım uyarıları vardır.

### 3. Önemli Uyarılar
- Hematolojik etkiler: TEGRETOL kullanımı ile ilişkili olarak aplastik anemi ve agranülositoz bildirilmiştir. Bazen TEGRETOL kullanımı ile ilişkili olarak, trombosit veya lökosit sayısında geçici veya kalıcı bir azalma oluşur. Bununla beraber, tedaviye başlamadan önce temel alınmak üzere trombositler, muhtemelen retikülositler ve serum demiri dahil, tam kan sayımı yapılmalıdır ve buna periyodik olarak devam edilmelidir.
- Karaciğer fonksiyonu: Özellikle geçmişinde bir karaciğer rahatsızlığı olan hastalarda ve yaşlı hastalarda, tedavinin başlangıcında karaciğer fonksiyon testleri yapılmalı.
- Dermatolojik veya hepatik reaksiyonlar: Potansiyel bir hematolojik problemi gösteren erken toksik belirti ve semptomlardan haberdar edilmelidir. Ateş, boğaz ağrısı, kızarıklık/döküntü/kaşıntı, ağız ülserleri, kolay morarma, peteşi veya hemorajik purpura gibi reaksiyonlar görülürse, hastaya derhal doktora danışması tavsiye edilmelidir.

### 4. Kaynaklar
- KÜB: TEGRETOL 200 MG DEGISTIRILMIS SALIMLI TABLET | KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri
- Graf: Neo4j veritabanında bulunan graf tabanlı kontrendikasyonlar ve etkileşimler

---

## [v3_q02] Soru 2
**Scores:** Faithfulness=0.625 | Context Recall=1.000

**Soru:** GFR 20 olan hastada PRADAXA dozu nasıl ayarlanmalı?

**Ground Truth:**
Dabigatran (PRADAXA) GFR 30 mL/dak altında kontrendikedir. GFR 20 olan hastada PRADAXA kullanılmamalıdır.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hayır, PRADAXA dozu kontrendikedir böbrek fonksiyonu GFR=20.0 mL/dak/1.73m² olan hastalar için. Hasta profilinde atriyal fibrilasyon bulunuyor ve kreatinin değeri 3.1. PRADAXA doz ayarı gerekir.

### 2. Detaylı Analiz
Böbrek fonksiyonu GFR=20.0 mL/dak/1.73m² olan hastalarda, PRADAXA dozu kontrendikedir. Bu durumda, kreatinin değeri 3.1 ve atriyal fibrilasyon bulunuyor. Kullanılabilen PRADAXA dozlarının belirlenmesi için renal fonksiyonlarının değerlendirilmesi gerekir.

### 3. Önemli Uyarılar
- Hasta profilinde atriyal fibrilasyon bulunuyor.
- PRADAXA doz ayarı gerekir böbrek fonksiyonu GFR=20.0 mL/dak/1.73m² olan hastalarda.

### 4. Kaynaklar
- KÜB: PRADAXA 150 MG SERT KAPSUL | KÜB Madde 4.2[bobrek]
- Graf Veritabanı Bulguları (Neo4j): A-FERIN, ACEPER PLUS, AFERIN PLUS FILM TABLET, APRIL-ACE

---

## [v3_q03] Soru 3
**Scores:** Faithfulness=0.750 | Context Recall=1.000

**Soru:** SPORANOX kullanan hastada CORDARONE kan düzeyi nasıl etkilenir?

**Ground Truth:**
İtrakonazol (SPORANOX) güçlü CYP3A4 inhibitörüdür. Amiodaron (CORDARONE) CYP3A4 substratıdır. Birlikte kullanımda amiodaronun plazma konsantrasyonu artar, QT uzaması ve kardiyak toksisite riski yükselir. Bu kombinasyondan kaçınılmalıdır.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hastanın mevcut ilaçlarından biri CORDARONE 150 mg/3 mL IV, diğeri ise SPORANOX 10 mg/mL oral. Bu iki ilaç arasındaki etkileşimler hakkında bilgi yoktur. Ancak, SPORANOX'un kullanılmasına karşın CORDARONE'un kullanımı kontrendikedir.

### 2. Detaylı Analiz
Hastanın mevcut ilaçlarından biri CORDARONENIN, diğeri ise SPORANOX'un ilaçtır. Bu iki ilaç arasındaki etkileşimler hakkında bilgi yoktur. Ancak, SPORANOX'un kullanılmasına karşın CORDARONE'un kullanımı kontrendikedir. Bu konu incelenen KÜB belgelerinde yer almamaktadır.

### 3. Önemli Uyarılar
- SPORANOX'un kullanılmasına karşın CORDARONE'un kullanımı kontrendikedir.
- Bu konu incelenen KÜB belgelerinde yer almamaktadır.

### 4. Kaynaklar
- CORDARONE 150 MG/3 ML IV ENJEKSIYONLUK COZELTI | KÜB Madde 4.3: Kontrendikasyonlar
- SPORANOX 10 MG / ML ORAL COZELTI | KÜB Madde 4.3: Kontrendikasyonlar

---

## [v3_q04] Soru 4
**Scores:** Faithfulness=1.000 | Context Recall=1.000

**Soru:** Gebelikte LAROXYL kullanımı güvenli midir?

**Ground Truth:**
Amitriptilin (LAROXYL) gebelikte kullanımı önerilmez. Gebelik kategorisi C olup hayvansal çalışmalarda fetal risk gösterilmiştir. Özellikle üçüncü trimesterde neonatal yoksunluk sendromu riski vardır. Klinik zorunluluk yoksa kullanılmamalıdır.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hayır, LAROXYL kullanımı gebelikte kontrendikedir. Bu ilaç gebelik döneminde özellikle de ilk ve son trimesterde kullanılmamalıdır. Amitriptilin miktarı ile ilişkilidir ürün retansiyonu, fetusta solunum depresyonu ve ajitasyon gibi yan etkilere neden olur. Laktasyon döneminde de güvenliliği kanıtlanmamıştır.

### 2. Detaylı Analiz
LAROXYL, amitriptilin bir formülüdür ve trisiklik hastalar için kullanılmaktadır. Amitriptilin gebelikte zararlı farmakolojik etkileri bulunmaktadır. Bu nedenle, LAROXYL gebelik döneminde özellikle de ilk ve son trimesterde kullanılmamalıdır. Amitriptilin miktarı ile ilişkilidir ürün retansiyonu, fetusta solunum depresyonu ve ajitasyon gibi yan etkilere neden olur. Laktasyon döneminde de güvenliliği kanıtlanmamıştır.

### 3. Önemli Uyarılar
- Amitriptilin, şizofreninin depresif durumları için kullanıldığında, psikotik semptomları şiddetlendirebileceği için, dikkatle kullanılmalıdır. Manik depresiflerde, manik faza kayma görülebilir. Hostilitenin eşlik ettiği veya etmediği paranoid delüzyonlar alevlenebilir. Bu tür vakalarda, aynı zamanda majör sakinleştirici verilmelidir veya amitiriptilin dozu azaltılmalıdır.
- Gerekli olmadığı sürece, amitiriptilin ve elektrokonvülsif tedavinin (ECT) kombine edilmesi tavsiye edilmez.
- Epilepsi öyküsü veya geçirilmiş yeni konvülsiyon öyküsü olan hastalara LAROXYL verilmemelidir.
- LAROXYL, nöroleptikler, trankilizanlar, hipnotikler, analjezikler ve anestezikler gibi santral etkili ilaçlarla birlikte verilirse sedatif etkisi artabilir.
- Hastalara ayrıca, alkolün herhangi bir bozukluğu artırabileceği ve bu nedenle tedavi sırasında kullanılması önemlidir.

### 4. Kaynaklar
- KÜB: LAROXYL 25 MG FILM KAPLI TABLET | KÜB Madde 4.6: Gebelik ve Laktasyon
- Graf Tabanlı Kontrendikasyonlar (Neo4j): LAROXYL 25 mg film kaplı tablet → gebelik durumunda kontrendike
- Graf Tabanlı Etkileşimler (Neo4j): LAROXYL 25 mg film kaplı tablet ↔ Antidepresan

---

## [v3_q05] Soru 5
**Scores:** Faithfulness=0.500 | Context Recall=1.000

**Soru:** Child-Pugh C karaciğer yetmezliği olan hastada ONAXAN kullanılabilir mi?

**Ground Truth:**
Rivaroksaban (ONAXAN) Child-Pugh B ve C karaciğer hastalığında kontrendikedir. Karaciğer yetmezliği koagülopati ile ilişkili olduğundan ve rivaroksaban hepatik metabolizma ile atılımına bağlı olduğundan, bu hastalarda kullanılmamalıdır.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hayır, Child-Pugh C karaciğer yetmezliği olan hastalara ONAXAN kullanılmaz. Bu ilaç, karaciğer yetmezliği durumunda kontrendikedir ve bu hastalar için tedavi yapılamaz.

### 2. Detaylı Analiz
Child-Pugh C karaciğer yetmezliği olan hastalara ONAXAN kullanılmaz. Bu ilaç, karaciğer yetmezliği durumunda kontrendikedir ve bu hastalar için tedavi yapılamaz. Klinik olarak anlamlı aktif kanaması olan hastalardan biri olduğu gibi, mevcut veya yeni geçirilmiş gastrointestinal ülserasyon, kanama riski yüksek malign neoplazm varlığı, yeni geçirilmiş beyin veya omurilik yaralanmaları, yeni geçirilmiş beyin, omurilik veya oftalmoloji ameliyatı, yakın zamanda gelişmiş olan intrakraniyal kanama, bilinen veya şüphelenilen özefagus varisleri, arteriyovenöz malformasyonlar, vasküler anevrizmalar veya majör intraspinal ya da intraserebral vasküler anomaliler gibi majör kanama bakımından anlamlı risk teşkil eden lezyon veya durumlar, açık bir santral venöz veya arteriyel kateterin açık kalması için gereken dozlarda fraksiyone olmayan heparin (UFH) kullanılan durumlar veya antikoagülan tedavide geçiş yapılan özel koşullar hariç olmak üzere, herhangi bir diğer antikoagülan ilaçla eşzamanlı tedavi (bkz. Bölüm 4.5 Diğer tıbbi ürünlerle etkileşimler ve diğer etkileşim şekilleri), Child Pugh B ve C’li siroz hastaları dahil olmak üzere koagülopati ve klinik açıdan anlamlı kanama riskiyle ilişkili hepatik hastalık (bkz. Bölüm 5.2 Farmakokinetik özellikler), gebelik ve emzirme döneminde (bkz. Bölüm 4.6 Gebelik ve laktasyon) gibi durumlarda kullanılabilir. Ancak, Child-Pugh C karaciğer yetmezliği olan hastalar bu ilaçlar arasında dahil değildir.

### 3. Önemli Uyarılar
Dikkatle kullanılması tavsiye edilmektedir. Kanama riskinin arttığı durumlarda dikkatle kullanılması tavsiye edilmektedir. Ciddi kanama meydana gelmesi durumunda, ONAXAN tedavisi sonlandırılmalıdır (bkz. Bölüm 4.9 Doz aşımı ve tedavisi).

### 4. Kaynaklar
- KÜB: ONAXAN 20 MG FILM KAPLI TABLET | KÜB Madde 4.3: Kontrendikasyonlar
- Graf Veritabani Bulguları (Neo4j): Graf Tabanlı Kontrendikasyonlar (Neo4j)

---

## [v3_q06] Soru 6
**Scores:** Faithfulness=1.000 | Context Recall=0.667

**Soru:** 8 yaşındaki 25 kg ağırlığında epilepsi hastasında KEPPRA dozu nasıl belirlenmeli?

**Ground Truth:**
Levetirasetam (KEPPRA) 4-11 yaş arası çocuklarda başlangıç dozu günde iki kez 10 mg/kg (vücut ağırlığına göre). 25 kg için başlangıç dozu günde iki kez 250 mg'dır. İdame doz titrasyon ile günde iki kez 30 mg/kg'a kadar artırılabilir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Keppra, epilepsi tedavisinde kullanılan bir ilaçtır. 8 yaşındaki 25 kg ağırlığında epilepsi hastası için doz ayarı gerekir. Başlangıç dozu, günde iki kez 10 mg/kg'dır. Maksimum doz, günde iki kez 30 mg/kg'a kadar çıkartılabilir. Doz değişimleri her 2 haftada bir yapılmalıdır.

### 2. Detaylı Analiz
Keppra, epilepsi tedavisinde kullanılan bir ilaçtır. Bu ilaç, film kaplı tablet formunda sunulur ve oral yolla alınmalıdır. Başlangıç dozu, günde iki kez 10 mg/kg'dır. Maksimum doz, günde iki kez 30 mg/kg'a kadar çıkartılabilir. Doz değişimleri her 2 haftada bir yapılmalıdır.

### 3. Önemli Uyarılar
Levetirasetam, diğer pirolidon türevlerine veya bölüm 6.1'de listelenen yardımcı maddelerden herhangi birine karşı aşırı duyarlılığı olanlarda kontrendikedir.

### 4. Kaynaklar
- KEPPRA 250 MG FILM KAPLI TABLET | KÜB Madde 4.2: Pozoloji ve Uygulama Şekli — Pediyatrik Popülasyon, Sayfa 13
- KEPPRA 250 MG FILM KAPLI TABLET | KÜB Madde 4.3: Kontrendikasyonlar, Sayfa 16

---

## [v3_q07] Soru 7
**Scores:** Faithfulness=0.500 | Context Recall=NaN

**Soru:** İSOPTİN kullanan hastaya CONCOR eklenirse ne olur?

**Ground Truth:**
Verapamil (İSOPTİN) ve bisoprolol (CONCOR) kombinasyonu AV blok ve bradikardi riskini artırır. Her ikisi de kalp hızını yavaşlattığından bu kombinasyondan kaçınılmalı veya çok yakın kardiyak izlem altında kullanılmalıdır. KÜB'de bu kombinasyon için özel uyarı mevcuttur.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hasta, hipertansiyon ve supraventriküler taşikardi hastalığına sahip ve mevcut ilaçlarından birisi ISOPTIN SR 240 mg film tabletidir. Yeni eklenen CONCOR 10 mg film kaplı tablet, bisoprolol ve yardımcı maddelerden karşı bilinen aşırı duyarlılık olan hastalarda kontrendikedir. Bu durumda, CONCOR'un kullanımına dikkatle karşılaştırmalı ve doz ayarı gerekebilir.

### 2. Detaylı Analiz
Hasta, hipertansiyon ve supraventriküler taşikardi hastalığına sahip ve mevcut ilaçlarından birisi ISOPTIN SR 240 mg film tabletidir. Yeni eklenen CONCOR 10 mg film kaplı tablet, bisoprolol ve yardımcı maddelerden karşı bilinen aşırı duyarlılık olan hastalarda kontrendikedir (CONCOR 10 MG FILM KAPLI TABLET | KÜB Madde 4.3: Kontrendikasyonlar). Bu durumda, CONCOR'un kullanımına dikkatle karşılaştırmalı ve doz ayarı gerekebilir.

### 3. Önemli Uyarılar
- DİKKAT — 2 ilaç birlikte kardiyak / qt uzaması riski taşıyor: CONCOR 10 MG FILM KAPLI TABLET, ISOPTIN SR 240 MG FILM TABLET (OTOMATİK KÜMÜLATİF RİSK ANALİZİ)
- DİKKAT — 2 ilaç birlikte hepatotoksisite riski taşıyor: CONCOR 10 MG FILM KAPLI TABLET, ISOPTIN SR 240 MG FILM TABLET (OTOMATİK KÜMÜLATİF RİSK ANALİZİ)
- DİKKAT — 2 ilaç birlikte solunum toksisitesi riski taşıyor: CONCOR 10 MG FILM KAPLI TABLET, ISOPTIN SR 240 MG FILM TABLET (OTOMATİK KÜMÜLATİF RİSK ANALİZİ)
- Hasta, hipertansiyon ve supraventriküler taşikardi hastalığına sahip ve mevcut ilaçlarından birisi ISOPTIN SR 240 mg film tabletidir. Yeni eklenen CONCOR 10 mg film kaplı tablet, bisoprolol ve yardımcı maddelerden karşı bilinen aşırı duyarlılık olan hastalarda kontrendikedir (CONCOR 10 MG FILM KAPLI TABLET | KÜB Madde 4.3: Kontrendikasyonlar). Bu durumda, CONCOR'un kullanımına dikkatle karşılaştırmalı ve doz ayarı gerekebilir.

### 4. Kaynaklar
- CONCOR 10 MG FILM KAPLI TABLET | KÜB Madde 4.3: Kontrendikasyonlar
- ISOPTIN SR 240 MG FILM TABLET | KÜB Madde 4.3: Kontrendikasyonlar
- OTOMATİK KÜMÜLATİF RİSK ANALİZİ

---

## [v3_q08] Soru 8
**Scores:** Faithfulness=0.250 | Context Recall=0.667

**Soru:** GFR 35 olan hastada LAMICTAL DC dozu nasıl ayarlanmalı?

**Ground Truth:**
Lamotrijin (LAMICTAL DC) böbrek yetmezliğinde dikkatli kullanılmalıdır. Şiddetli böbrek yetmezliğinde başlangıç ve idame dozlarının azaltılması gerekebilir. GFR 35 orta-şiddetli böbrek bozukluğu kategorisindedir; klinik yanıt ve tolerabiliteye göre doz titre edilmelidir.

**Model Yanıtı:**
 ### 1. Kısa Özet
LAMICTAL DC dozunun nasıl ayarlanacağı hakkında bilgi verilmiyor, ancak böbrek yetmezliği durumunda LAMICTAL kontrendikedir. Bu nedenle, hastanın böbrek fonksiyonu (GFR=35) ile ilgili doz ayarı için dikkat edilmesi gereken bir ilaç değildir.

### 2. Detaylı Analiz
Böbrek yetmezliği durumunda LAMICTAL kontrendikedir, ancak doz ayarı hakkında bilgi verilmiyor. Bu nedenle, hastanın böbrek fonksiyonu (GFR=35) ile ilgili doz ayarı için dikkat edilmesi gereken bir ilaç değildir.

### 3. Önemli Uyarılar
- LAMICTAL, lamotrijine veya ilacın bileşimindeki diğer maddelerden herhangi birine karşı aşırı duyarlı olduğu bilinen kişilerde kontrendikedir.
- Bu soruya ilgili bilgi verilmiyor, ancak LAMICTAL'in böbrek yetmezliği durumunda kontrendikedir. Bu nedenle, hastanın böbrek fonksiyonu (GFR=35) ile ilgili doz ayarı için dikkat edilmesi gereken bir ilaç değildir.

### 4. Kaynaklar
- KÜB: LAMICTAL DC 100 MG COZUNUR / CIGNEME TABLETI | KÜB Madde 4.2[bobrek]
- Graf Veritabanı Bulguları (Neo4j): Graf Tabanlı Kontrendikasyonlar ve Graf Tabanlı Etkileşimler

---

## [v3_q09] Soru 9
**Scores:** Faithfulness=0.500 | Context Recall=1.000

**Soru:** Astım hastasına ARLEC başlanabilir mi?

**Ground Truth:**
Karvedilol (ARLEC) reaktif hava yolu hastalığı ve bronkospazm geçmişi olan hastalarda kontrendikedir. Astım, karvedilol için mutlak kontrendikasyondur; kardiyoselektif olmayan beta-bloker özelliği nedeniyle bronkospazm şiddetlenebilir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hayır, astım hastasına ARLEC kullanılmaz, çünkü karvedilol, astım öyküsü olan hastalarda potansiyel yarar potansiyel riskten daha fazlasa kullanılmalıdır. Bu nedenle, astım hastasına ARLEC başlatılamaz.

### 2. Detaylı Analiz
Astım hastasına ARLEC kullanılmaz çünkü karvedilol, bronkospazm gözlenen kronik obstrüktif akciğer hastalığı (KOAH) bulunan ve oral ya da inhalasyon yolu ile ilaç almayan hastalarda potansiyel yarar potansiyel riskten daha fazlasa kullanılmalıdır. Bu nedenle, astım hastasına ARLEC başlatılamaz veya diğer β-blokörlerle aynı gibi kullanılamaz.

### 3. Önemli Uyarılar
- Karvedilol, P-glikoproteinin substratı olmanın yanı sıra aynı zamanda inhibitörüdür. Bu nedenle, P-glikoprotein ile taşınan ilaçların biyoyararlanımı, birlikte alınan karvedilol ile artabilir.
- Karvedilol veya ilacın içerdiği diğer yardımcı bileşenlere aşırı duyarlılık olan hastalarda kullanılmamalıdır.
- Stabil olmayan/dekompanse kalp yetmezliği, önemli ölçüde sıvı tutulumu olan hastalar ve karaciğer disfonksiyonu olan hastalarda de kullanılmamalıdır.
- Karvedilol 2. ve 3. derece AV bloğu (kalıcı pacemaker yerleştirilmediyse), ağır bradikardi (<50 atım/dakika), hastasın sinüs sendromu (sino-atriyal blok dahil), ağır hipotansiyon (sistolik kan basıncı <85 mmHg), kardiyojenik şok, bronkospazm ya da astım öyküsü olan hastalar ve metabolik asidoz için de kullanılmamalıdır.

### 4. Kaynaklar
- KÜB: ARLEC 6,25 MG TABLET | KÜB Madde 4.3: Kontrendikasyonlar
- KÜB: ARLEC 6,25 MG TABLET | KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri
- KÜB: ARLEC 6,25 MG TABLET | KÜB Madde 4.5: Diğer Tıbbi Ürünlerle Etkileşimler
- Graf Veritabanı Bulguları (Neo4j)
- OTOMATİK CYP450 ENZİM ANALİZİ

---

## [v3_q10] Soru 10
**Scores:** Faithfulness=1.000 | Context Recall=0.750

**Soru:** PLAVIX kullanan hastaya CANDİDİN başlanırsa antiplatelet etki nasıl değişir?

**Ground Truth:**
Flukonazol (CANDİDİN) güçlü CYP2C19 inhibitörüdür. Klopidogrel (PLAVIX) CYP2C19 üzerinden aktif metabolite dönüştürülür. Flukonazol bu dönüşümü inhibe ederek klopidogrelin antiplatelet etkisini önemli ölçüde azaltır. Stent olan hastalarda bu kombinasyondan kaçınılmalıdır.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hastanın mevcut ilaçlarından birisi PLAVIX (klopidogrel) ve karşısına CANDİDIN (flukonazol) başlanması, kardiyak / QT uzaması, hepatotoksisite ve kanama / hematolojik riskleri taşıyabilir. Bu risklerin azaltılması için dikkatle izlenmelidir.

### 2. Detaylı Analiz
Hastanın mevcut ilaçlarından birisi PLAVIX (klopidogrel) ve karşısına CANDİDIN (flukonazol) başlanması, kardiyak / QT uzaması, hepatotoksisite ve kanama / hematolojik riskleri taşıyabilir. Bu risklerin azaltılması için dikkatle izlenmelidir.

CANDİDIN (flukonazol) kullanımı, sisaprid, terfenadin, astemizol, eritromisin, pimozid ve kinidin gibi diğer ilaçlar ile birlikte uygulanması kontrendikedir. Bu ilaçlara bağlı etkileşimlerde, kardiyak olaylarının bildirilmesi ve QT aralığının uzamasına sekonder olarak ciddi kardiyak disritmilerin ortaya çıkması nedeniyle etkileşim çalışmaları yapılmıştır.

PLAVIX (klopidogrel) ve CANDİDIN (flukonazol) birlikte kullanılması, kanama / hematolojik riskleri taşıyabilir. Bu risklerin azaltılması için derhal kan hücreleri sayımı ve/veya diğer gerekli testler yapılmalıdır.

### 3. Önemli Uyarılar
- CANDİDIN (flukonazol) kullanımı, sisaprid, terfenadin, astemizol, eritromisin, pimozid ve kinidin gibi diğer ilaçlar ile birlikte uygulanması kontrendikedir.
- PLAVIX (klopidogrel) ve CANDİDIN (flukonazol) birlikte kullanılması, kanama / hematolojik riskleri taşıyabilir. Bu risklerin azaltılması için derhal kan hücreleri sayımı ve/veya diğer gerekli testler yapılmalıdır.
- CANDİDIN (flukonazol) kullanımı, etkin maddeye, ilacın bileşenlerinden herhangi birisine veya benzer azol bileşiklerine hassas olduğu bilinen hastalarda kullanılmamalıdır.
- CANDİDIN (flukonazol) kullanımı, multipl doz flukonazol alan hastalarda flukonazol ile beraber kullanılan terfenadin kontrendikedir.

### 4. Kaynaklar
- CANDIDIN 150 MG KAPSUL | KÜB Madde 4.3: Kontrendikasyonlar
- CANDIDIN 150 MG KAPSUL | KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri
- PLAVIX 75 MG FILM KAPLI TABLET | KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri
- OTOMATİK KÜMÜLATİF RİSK ANALİZİ
- OTOMATİK CYP450 ENZİM ANALİZİ

---

## [v3_q11] Soru 11
**Scores:** Faithfulness=0.500 | Context Recall=0.333

**Soru:** Emziren annede LUSTRAL kullanımı güvenli midir?

**Ground Truth:**
Sertralin (LUSTRAL) anne sütüne geçer. Emzirme döneminde kullanımı önerilmez; ancak klinik gereklilik varsa bebek yakından izlenmelidir. KÜB belgesinde emzirme döneminde kullanılmaması tavsiye edilmektedir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Emziren annede Lustral kullanımı kontrendikedir. Bu ilaç, postpartum depresyonun tedavisi için kullanılabilen bir ilaçtır; ancak bu ilaç, böbrek fonksiyonu bilinmiyor olan hastalara kullanılmamalıdır.

### 2. Detaylı Analiz
Lustral (bileşenleri: sertralina hidroklorid), postpartum depresyonun tedavisi için kullanılan bir antidepresant ilaçtır. Bu ilaç, böbrek fonksiyonu bilinmiyor olmayan hastalara kullanılmamalıdır çünkü sertralina hidroklorid, böbrek sistemindeki enzimleri etkileyebilir ve bu sebepten dozu ayarlama gerekebilir.

### 3. Önemli Uyarılar
- Lustral, böbrek fonksiyonu bilinmiyor olmayan hastalara kullanılmamalıdır.
- Bu ilaç, böbrek sistemindeki enzimleri etkileyebilir ve dozu ayarlama gerekebilir.

### 4. Kaynaklar
- KÜB: Lustral [İlaç Adı | Madde X.X | Sayfa Y]
- Graf: [Graf]
- CYP450 Analizi: [CYP450 Analizi]

---

## [v3_q12] Soru 12
**Scores:** Faithfulness=NaN | Context Recall=1.000

**Soru:** NORODOL ile CORDARONE birlikte kullanılabilir mi?

**Ground Truth:**
Haloperidol (NORODOL) ve amiodaron (CORDARONE) her ikisi de QT intervalini uzatır. Bu kombinasyon Torsades de Pointes ve ventriküler aritmiler açısından yüksek risk taşır. Birlikte kullanımdan kaçınılmalı; zorunluysa EKG monitorizasyonu yapılmalıdır.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hayır, NORODOL ile CORDARONE birlikte kullanılabilir değildir. Bu ilaçlar arasındaki etkileşim kontrendidir.

### 2. Detaylı Analiz
NORODOL ve CORDARONE'un birlikte kullanılmasına karşı, KÜB bilgilerinde belirtilmiştir ki bu ilaçlar arasındaki etkileşim kontrendidir. Bu durumda, bu ilaçların birlikte kullanımının riskleri ve yan etkileri artar.

### 3. Önemli Uyarılar
- NORODOL ve CORDARONE'un birlikte kullanılmasına karşı, kontrendidir.
- Bu ilaçlar arasındaki etkileşim riskleri ve yan etkileri artar.

### 4. Kaynaklar
- KÜB: CORDARONE 150 MG/3 ML IV ENJEKSIYONLUK COZELTI, [İlaç Adı | Madde X.X | Sayfa Y]
- KÜB: SANORONE 200 MG TABLET, [İlaç Adı | Madde X.X | Sayfa Y]
- Graf: Graf Tabanlı Kontrendikasyonlar (Neo4j), [Graf]
- Graf: Graf Tabanlı Etkileşimler (Neo4j), [Graf]
- CYP450 Analizi: [CYP450 Analizi]

---

## [v3_q13] Soru 13
**Scores:** Faithfulness=0.429 | Context Recall=1.000

**Soru:** 85 yaşındaki hastada XANAX başlangıç dozu ne olmalı?

**Ground Truth:**
Alprazolam (XANAX) geriyatrik hastalarda en düşük etkin dozda başlanmalıdır. KÜB belgesine göre yaşlı hastalarda başlangıç dozu 0.25 mg günde 2-3 kez olarak önerilir. Sedatif etkiye karşı duyarlılık artar, düşme ve konfüzyon riski gözetilmelidir.

**Model Yanıtı:**
 ### 1. Kısa Özet
XANAX 0.5 mg tablet'i kullanmak için en uygun doz, hastanın süreçteki süreçler ve durumlarına göre belirlenmelidir. Hasta, böbrek fonksiyonu 50 mL/dak/1.73m² (Evre 3a) olan 85 yaşlı kadın olup, anksiyete bozukluğu tanıyor. XANAX'in böbrek yetmezliği durumunda kontrendikedir.

### 2. Detaylı Analiz
XANAX dozu belirlenmesinde, hastanın yanıtına ve süreçlerine göre en uygun doz saptanmalıdır. Aşağıdaki tablodaki dozlar, birçok hastanın gereksinimini karşılayacaktır. Semptomları kontrol edecek en düşük doz kullanılmalıdır. Daha yüksek dozların gerektiği hastalarda, istenmeyen etkilerden kaçınmak için doz arttırımları dikkatle yapılmalıdır.

### 3. Önemli Uyarılar
- XANAX aşağıdaki durumlarda kontrendikedir: benzodiazepinlere, alprazolama veya Bölüm 6.1'de listelenmiş yardımcı maddelerin herhangi birine karşı aşırı duyarlılık, miyastenia gravis, şiddetli solunum yetmezliği, uyku apnesi sendromu, şiddetli karaciğer yetmezliği.
- XANAX'in böbrek yetmezliği durumunda kontrendikedir.
- Hasta profilindeki yaş ve böbrek/karaciğer fonksiyonu, mevcut ilaçlar, alerjiler ve lab değerleri gibi faktörler doz ayarında önemli rol oynar.
- XANAX'in kullanımında dikkat edilmesi gereken riskler ve yan etkiler hakkında bilgi sağlanabilir, ancak bu maddelerde ilgili veri mevcut değildir.
- XANAX'in CYP450 enzim sistemine etkisini açıklayan bilgi mevcut değildir.

### 4. Kaynaklar
- KÜB: XANAX 0.5 MG TABLET | KÜB Madde 4.2: Pozoloji ve Uygulama Şekli — Böbrek / Karaciğer Yetmezliği
- Graf: Graf Tabanlı Kontrendikasyonlar (Neo4j)

---

## [v3_q14] Soru 14
**Scores:** Faithfulness=1.000 | Context Recall=1.000

**Soru:** Aktif mide ülseri olan hastada BRUFEN kullanılabilir mi?

**Ground Truth:**
İbuprofen (BRUFEN) aktif peptik ülser hastalığında kontrendikedir. KÜB belgesinde aktif gastrointestinal ülser veya kanama, BRUFEN için mutlak kontrendikasyon olarak belirtilmiştir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hayır, BRUFEN kullanılabilir değildir aktif mide ülseri olan hastalara. Bu ilaç böbrek yetmezliğinde, karaciğer yetmezliğinde ve NYHA Sınıf IV'de şiddetli kalp yetmezliğinde kontrendikedir. Ayrıca, hamilelikin 3. trimesterinde, gastrointestinal kanama riskine artışa sebep olan koşullarda ve diğer NSAİİ'lerle etkileşimleri olasılığından dolayı kontrendikedir.

### 2. Detaylı Analiz
BRUFEN, aktif mide ülseri olan hastalara kullanılabilmez. Bu ilaç böbrek yetmezliğinde, karaciğer yetmezliğinde ve NYHA Sınıf IV'de şiddetli kalp yetmezliğinde kontrendikedir (KÜB Madde 4.3). Ayrıca, hamilelikin 3. trimesterinde, gastrointestinal kanama riskine artışa sebep olan koşullarda ve diğer NSAİİ'lerle etkileşimleri olasılığından dolayı kontrendikedir (KÜB Madde 4.3).

### 3. Önemli Uyarılar
- BRUFEN, aktif mide ülseri olan hastalara kullanılamaz.
- Bu ilaç böbrek yetmezliğinde, karaciğer yetmezliğinde ve NYHA Sınıf IV'de şiddetli kalp yetmezliğinde kontrendikedir.
- Hamilelikin 3. trimesterinde, gastrointestinal kanama riskine artışa sebep olan koşullarda ve diğer NSAİİ'lerle etkileşimleri olasılığından dolayı kontrendikedir.

### 4. Kaynaklar
- KÜB Madde 4.3: Kontrendikasyonlar (BRUFEN 400 MG FILM TABLET)
- KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri (BRUFEN 400 MG FILM TABLET)

---

## [v3_q15] Soru 15
**Scores:** Faithfulness=0.000 | Context Recall=1.000

**Soru:** ALDACTONE kullanan hastada PLASORİN dozu neden değişebilir?

**Ground Truth:**
Spironolakton (ALDACTONE) varfarin (PLASORİN) metabolizmasını etkileyebilir; birlikte kullanımda INR değerinin değişebileceği bildirilmiştir. Varfarin dozu ayarlaması gerekebilir; INR yakın izlenmelidir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hasta, kalp yetmezliği ve atriyal fibrilasyon tanıyor. Mevcut ilaçları PLASORİN 5 mg ve ALDACTONE 25 mg. Bu hastaya verilen ALDACTONE, böbrek fonksiyonu hakkında GFR=55.0 mL/dak/1.73m² (Evre 3a (G3a, GFR 45-59)) olduğu görüldü. ALDACTONE kullanan hastalarda PLASORİN dozu neden değişebilir. Bu konuda KÜB belgelerinde bilgi yoktur.

### 2. Detaylı Analiz
Hasta, kalp yetmezliği ve atriyal fibrilasyon tanıyor. Mevcut ilaçları PLASORİN 5 mg ve ALDACTONE 25 mg. Bu hastaya verilen ALDACTONE, böbrek fonksiyonu hakkında GFR=55.0 mL/dak/1.73m² (Evre 3a (G3a, GFR 45-59)) olduğu görüldü. ALDACTONE, böbrek yetmezliği durumunda kontrendikedir. Bu ilaç, renin sekreteksen etkisi vardır ve bu nedenle PLASORİN dozu değişebilir. KÜB belgelerinde ALDACTONE'un PLASORİN'un dozunu etkileyeceğini açıkça yazılmasa da, bu ilaçların birbirine etkileşiminin olumsuz etkileri vardır.

### 3. Önemli Uyarılar
- ALDACTONE'un PLASORİN dozu etkileyeceğini KÜB belgelerinde açıkça yazılmasa da, bu ilaçların birbirine etkileşiminin olumsuz etkileri vardır.
- Hasta profilindeki böbrek fonksiyonu (GFR=55.0 mL/dak/1.73m²) Evre 3a (G3a, GFR 45-59) olup, ALDACTONE'un kullanılmasında PLASORİN dozu değişmesine dikkat edilmelidir.

### 4. Kaynaklar
- KÜB: [PLASORİN | Madde X.X | Sayfa Y], [ALDACTONE | Madde X.X | Sayfa Y]
- Graf: [Graf]
- CYP450 Analizi: [CYP450 Analizi]

---

## [v3_q16] Soru 16
**Scores:** Faithfulness=0.727 | Context Recall=0.333

**Soru:** GFR 40 olan hastada COLCHICUM DISPERT dozu nasıl ayarlanmalı?

**Ground Truth:**
Kolşisin (COLCHICUM DISPERT) böbrek yetmezliğinde dikkatli kullanılmalıdır. Orta dereceli böbrek yetmezliğinde (GFR 30-60) doz azaltılmalı ve tedavi süresi kısaltılmalıdır. Nöromiyopati ve miyelosüpresyon riski artar.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hastanın GFR değeri 40 mL/dak/1.73m², bu durumda COLCHICUM DISPERT dozu nasıl ayarlanmalı? Hasta profilindeki bilgiler göz önünde bulunduruldu. KÜB'de belirtilen kontrendikasyonlar bahsedildi ve bu ilaç, ciddi renal rahatsızlıkta (kreatinin klerensi 10 mL/dak altında olanlar) kullanımı kontrendikedir. Ancak, hastanın mevcut durumunda doz ayarı gerekir.

### 2. Detaylı Analiz
Hastanın GFR değeri 40 mL/dak/1.73m², bu durumda COLCHICUM DISPERT dozu nasıl ayarlanmalı? Hasta profilindeki bilgiler göz önünde bulunduruldu. KÜB'de belirtilen kontrendikasyonlar bahsedildi ve bu ilaç, ciddi renal rahatsızlıkta (kreatinin klerensi 10 mL/dak altında olanlar) kullanımı kontrendikedir. Ancak, hastanın mevcut durumunda doz ayarı gerekir. KÜB'de belirtilen doz ayarı bilgisi yoktur ve bu nedenle, doz ayarı hakkında bir tedavi planı hazırlanmalıdır.

### 3. Önemli Uyarılar
- COLCHICUM DISPERT'in içeriğindeki yardımcı maddelerden herhangi bire karşı aşırı duyarlılığı olanlarda, ilaç kullanımı kontrendikedir.
- Ciddi renal rahatsızlıkta (kreatinin klerensi 10 mL/dak altında olanlar), ilaç kullanımı kontrendikedir.

### 4. Kaynaklar
- KÜB: COLCHICUM DISPERT 0,5 MG FILM KAPLI TABLET | KÜB Madde 4.3: Kontrendikasyonlar
- Graf: Neo4j veritabanı bulguları

---

## [v3_q17] Soru 17
**Scores:** Faithfulness=0.750 | Context Recall=1.000

**Soru:** CYMBALTA kullanan hastada ALTİZEM SR eklenirse ne olur?

**Ground Truth:**
Duloksetin (CYMBALTA) CYP1A2 ve CYP2D6 substratıdır. Diltiazem (ALTİZEM SR) orta düzey CYP3A4 inhibitörüdür. Duloksetin metabolizması üzerinde belirgin etkisi sınırlıdır ancak birlikte kullanımda duloksetin plazma düzeyi izlenmeli ve yan etkiler takip edilmelidir.

**Model Yanıtı:**
 ### 1. Kısa Özet
CYMBALTA kullanan hastada ALTİZEM SR eklenmesi kontrendikedir. Bu ilaçların birlikte kullanılması diltiazem veya altizemin içerdiği yardımcı maddelerden birine karşı aşırı duyarlılığı olan hastalarda, ventriküler pace-maker kullanılmayan sinüs sendromu vakalarında, ventriküler pacemaker kullanılmayan ikinci ya da üçüncü derece AV blok bulunan hastalarda, ciddi hipotansiyon ve ciddi bradikardide, pulmoner staz durumunda sol ventriküler yetmezliği, akut miyokard infarktüsü ve pulmoner konjesyon bulunan hastalarda, konjestif kalp yetmezliğinde, ciddi aortik stenozda, İntravenöz formları kardiyojenik şokta, ventriküler taşikardi bulunan hastalarda, WPW sendromu veya kısa PR sendromu gibi ek ileti yolunun neden olduğu atriyal fibrilasyon veya atriyal flutteri bulunan hastalarda, Dantrolen infüzyonu ile birlikte kullanımında, Ivabradin ile kombinasyonda, akut porfirisi bulunan hastalarda, Gebelikte, çocuk doğurma potansiyeli olanlarda ve emzirme döneminde kontrendikedir.

### 2. Detaylı Analiz
CYMBALTA kullanan hastada ALTİZEM SR eklenmesi kontrendikedir. Bu ilaçların birlikte kullanılması diltiazem veya altizemin içerdiği yardımcı maddelerden birine karşı aşırı duyarlılığı olan hastalarda, ventriküler pace-maker kullanılmayan sinüs sendromu vakalarında, ventriküler pacemaker kullanılmayan ikinci ya da üçüncü derece AV blok bulunan hastalarda, ciddi hipotansiyon ve ciddi bradikardide, pulmoner staz durumunda sol ventriküler yetmezliği, akut miyokard infarktüsü ve pulmoner konjesyon bulunan hastalarda, konjestif kalp yetmezliğinde, ciddi aortik stenozda, İntravenöz formları kardiyojenik şokta, ventriküler taşikardi bulunan hastalarda, WPW sendromu veya kısa PR sendromu gibi ek ileti yolunun neden olduğu atriyal fibrilasyon veya atriyal flutteri bulunan hastalarda, Dantrolen infüzyonu ile birlikte kullanımında, Ivabradin ile kombinasyonda, akut porfirisi bulunan hastalarda, Gebelikte, çocuk doğurma potansiyeli olanlarda ve emzirme döneminde kontrendikedir.

### 3. Önemli Uyarılar
- Diltiazem veya altizemin içerdiği yardımcı maddelerden birine karşı aşırı duyarlılığı olan hastalarda, ventriküler pace-maker kullanılmayan sinüs sendromu vakalarında, ventriküler pacemaker kullanılmayan ikinci ya da üçüncü derece AV blok bulunan hastalarda, ciddi hipotansiyon ve ciddi bradikardide, pulmoner staz durumunda sol ventriküler yetmezliği, akut miyokard infarktüsü ve pulmoner konjesyon bulunan hastalarda, konjestif kalp yetmezliğinde, ciddi aortik stenozda, İntravenöz formları kardiyojenik şokta, ventriküler taşikardi bulunan hastalarda, WPW sendromu veya kısa PR sendromu gibi ek ileti yolunun neden olduğu atriyal fibrilasyon veya atriyal flutteri bulunan hastalarda, Dantrolen infüzyonu ile birlikte kullanımında, Ivabradin ile kombinasyonda, akut porfirisi bulunan hastalarda, Gebelikte, çocuk doğurma potansiyeli olanlarda ve emzirme döneminde CYMBALTA'yı eklemek kontrendikedir.
- Diltiazem veya altizemin içerdiği yardımcı maddelerden birine karşı aşırı duyarlılığı olan hastalarda, ventriküler pace-maker kullanılmayan sinüs sendromu vakalarında, ventriküler pacemaker kullanılmayan ikinci ya da üçüncü derece AV

---

## [v3_q18] Soru 18
**Scores:** Faithfulness=1.000 | Context Recall=1.000

**Soru:** Gebelikte COZAAR kullanılabilir mi?

**Ground Truth:**
Losartan (COZAAR) gebelikte kontrendikedir. Gebelik kategorisi D olup özellikle 2. ve 3. trimesterde fetüste böbrek hasarı, oligohidramniyos ve ölüm riskiyle ilişkilidir. KÜB belgesinde gebelik mutlak kontrendikasyon olarak belirtilmiştir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hayır, COZAAR gebelik döneminde kullanılmalıdır. Losartan, COZAAR'ın etkin madde, gebelikte zararlı farmakolojik etkileri bulunmaktadır ve gebelik döneminde kullanılmamalıdır.

### 2. Detaylı Analiz
Gebelik kategorisi D'dir ve COZAAR, gebelikte zararlı farmakolojik etkileri bulunmaktadır. Losartan, COZAAR'ın etkin madde, gebelik döneminde kullanılmamalıdır. Planlı bir hamilelikten önce, uygun bir alternatif antihipertansif tedaviye geçilmelidir. Losartan ile tedavi sırasında uygun bir kontrasepsiyon yöntemi kullanılmalıdır.

### 3. Önemli Uyarılar
- COZAAR gebelik döneminde kullanılmamalıdır.
- Losartan, gebelikte zararlı farmakolojik etkileri bulunmaktadır.
- Planlı bir hamilelikten önce, uygun bir alternatif antihipertansif tedaviye geçilmelidir.
- Losartan ile tedavi sırasında uygun bir kontrasepsiyon yöntemi kullanılmalıdır.

### 4. Kaynaklar
- KÜB Madde 4.6: Gebelik ve Laktasyon (COZAAR 50 MG FILM KAPLI TABLET)
- Graf Veritabani Bulguları (Neo4j): Graf Tabanlı Kontrendikasyonlar, Graf Tabanlı Etkileşimler ve İlaç İle Etkileşimler
- OTOMATİK CYP450 ENZİM ANALİZİ: CYP2C9 inhibitörü

---

## [v3_q19] Soru 19
**Scores:** Faithfulness=1.000 | Context Recall=1.000

**Soru:** CLEXANE kullanan hastaya PLAVIX eklenmesi kanama riskini nasıl etkiler?

**Ground Truth:**
Enoksaparin (CLEXANE) ve klopidogrel (PLAVIX) kombinasyonu kanama riskini artırır. Her ikisi de antitrombotik etki gösterir; birlikte kullanımda majör kanama ve gastrointestinal kanama riski yükselir. Klinik fayda-risk dengesi değerlendirilerek kullanılmalı, kanama belirtileri yakın izlenmelidir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hasta, CLEXANE 4000 anti-Xa ilaçını kullandığından dolayı kanama riski artmaktadır. PLAVIX eklenmesi, bu riski daha da artıracaktır. Bu nedenle, PLAVIX'in CLEXANE ile birlikte kullanılması önerilmemektedir.

### 2. Detaylı Analiz
Hasta, CLEXANE 4000 anti-Xa ilaçını kullandığından dolayı kanama riski artmaktadır. Bu riskin artmasına neden olan, PLAVIX'in (klopidogrel) trombosit etkileşimlerine yol açan aktivitelerinden dolayı gelir. Kümeleme Risk Analizi'nde da bu riski gösteren şekilde, CLEXANE ve PLAVIX birlikte hematolojik riski taşıyor.

### 3. Önemli Uyarılar
- Kanama riskinin artmasına neden olan PLAVIX'in trombosit etkileşimlerine yol açan aktivitelerinden dolayı, CLEXANE ile birlikte kullanılması önerilmemektedir.
- Hasta profili (yaş, böbrek/karaciğer fonksiyonu, mevcut ilaçlar, alerjiler, lab değerleri) göz önünde bulundurulmalıdır.

### 4. Kaynaklar
- KÜB: CLEXANE 4000 ANTI-XA IU/0,4 ML ENJEKSIYONLUK COZELTI ICEREN KULLANIMA HAZIR ENJEKTOR | Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri
- KÜB: PLAVIX 75 MG FILM KAPLI TABLET | KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri

---

## [v3_q20] Soru 20
**Scores:** Faithfulness=0.625 | Context Recall=1.000

**Soru:** Child-Pugh A karaciğer yetmezliği olan hastada LİPİTOR dozu nasıl ayarlanmalı?

**Ground Truth:**
Atorvastatin (LİPİTOR) aktif karaciğer hastalığında kontrendikedir. Child-Pugh A hastalarda dikkatli kullanım önerilir; karaciğer fonksiyon testleri yakın takip edilmelidir. ALT ve AST normalin 3 katını aşarsa tedavi kesilmelidir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Child-Pugh A karaciğer yetmezliği olan hastalara LIPITOR dozu ayarlama işlemi gerçekleştirilmelidir. Hasta profilini göz önünde bulundurarak, standart kolesterol düşürücü bir diyete girmesi ve bu diyeti LIPITOR tedavisi sırasında da devam etmesi gerekir. Doz aralığı günde bir defa 10 ile 80 mg'dır ve doz ayarlanmalıdır.

### 2. Detaylı Analiz
Hasta profilini göz önünde bulundurarak, LIPITOR tedavisi başlamadan önce standart kolesterol düşürücü bir diyete girmelidir ve bu diyeti LIPITOR tedavisi sırasında da devam ettirmelidir. Doz aralığı günde bir defa 10 ile 80 mg'dır ve doz ayarlanmalıdır. Tedavinin başlangıcı ve/veya titrasyonunu takiben lipid seviyeleri 2-4 hafta içinde değerlendirilmeli ve buna bağlı olarak doz ayarlanmalıdır.

### 3. Önemli Uyarılar
- LIPITOR, aktif karaciğer hastalığı olan veya devamlı olarak normal üst limiti (NÜS) 3 kat aşan açıklanamayan serum transaminaz yükselmesi olanlarda kontrendikedir.
- Hepatit C antiviralleri glecaprevir/pibrentasvir ile tedavi edilenlerde LIPITOR kontrendikedir.
- 10 yaş altı hastaların tedavisinde atorvastatin endike değildir.

### 4. Kaynaklar
- KÜB: LIPITOR 20 MG FILM KAPLI TABLET | KÜB Madde 4.2[karaciger]: Pozoloji ve Uygulama Şekli — Karaciğer Yetmezliği
- Graf: Neo4j veritabanı bulguları (Neo4j)

---

## [v3_q21] Soru 21
**Scores:** Faithfulness=0.667 | Context Recall=1.000

**Soru:** PROPYCIL kullanan hastaya AMİODARON (SANORONE) eklenirse ne olur?

**Ground Truth:**
Propiltiourasil (PROPYCIL) ve amiodaron (SANORONE) kombinasyonunda dikkatli olunmalıdır. Amiodaron yüksek iyot içerir ve tiroid fonksiyonunu bozabilir; propiltiourasil ile birlikte hem hipotiroidizm hem hipertiroidizm riski değişebilir. Tiroid fonksiyon testleri yakın izlenmelidir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Amiodaron (SANORONE) PROPYCIL ile birlikte kullanılması kontrendikedir. Bu ilaçlar arasındaki etkileşim, amiodaronun serum konsantrasyonunu artmasına ve QT aralığında uzamaya neden olabilir. Amiodaron, tedaviye başlamadan önce EKG ölçümlerinin yapılması gerekir.

### 2. Detaylı Analiz
Amiodaron ve PROPYCIL arasındaki etkileşim, amiodaronun farmakolojik özelliklerinin bir sonucudur. Bu ilaçlar arasındaki etkileşim, amiodaronun serum konsantrasyonunu artmasına ve QT aralığında uzamaya neden olabilir. Amiodaron, tedaviye başlamadan önce EKG ölçümlerinin yapılması gerekir. Bu "cordaronik" değişiklik, repolarizasyonun uzamasına bağlı olarak QT aralığında uzamaya neden olur. Buna eşlik eden U dalgaları görülebilir; bu amiodaronun terapötik etkisinin bir belirtisi olup, toksisite değildir.

### 3. Önemli Uyarılar
- Amiodaron ve PROPYCIL arasındaki etkileşim kontrendikedir. Bu ilaçlar arasındaki etkileşim, amiodaronun serum konsantrasyonunu artmasına ve QT aralığında uzamaya neden olabilir.
- Amiodaron tedaviye başlamadan önce EKG ölçümlerinin yapılması gerekir.

### 4. Kaynaklar
- KÜB: SANORONE 200 MG TABLET | KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri
- Graf: Neo4j veritabanı bulguları (Neo4j)

---

## [v3_q22] Soru 22
**Scores:** Faithfulness=0.500 | Context Recall=1.000

**Soru:** GFR 25 olan hastada JANUVIA'ya alternatif olarak AMARYL kullanılabilir mi?

**Ground Truth:**
Glimepirid (AMARYL) böbrek yetmezliğinde hipoglisemi riski nedeniyle dikkatli kullanılmalıdır. Şiddetli böbrek yetmezliğinde (GFR <30) kullanımından kaçınılması önerilir çünkü aktif metabolitler birikebilir. GFR 25 için AMARYL kontrendike değil ama yüksek hipoglisemi riski taşır.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hayır, AMARYL kullanılabilir değildir. Hasta profilindeki böbrek fonksiyonu (GFR=25) ve tip-2 diyabet tanısında, AMARYL'in kullanımı kontrendikedir. Bu durumda JANUVIA'ya alternatif olarak kullanılabilen başka bir ilaç bulunmamaktadır.

### 2. Detaylı Analiz
Hasta profilindeki böbrek fonksiyonu (GFR=25) ve tip-2 diyabet tanısında, AMARYL'in kullanımı kontrendikedir. Bu durumda JANUVIA'ya alternatif olarak kullanılabilen başka bir ilaç bulunmamaktadır.

AMARYL, diyabet mellitus (tip 1) ve diyabetik ketoasidoz, diyabetik koma, ciddi böbrek veya karaciğer fonksiyon bozukluğu olan hastalarda kullanılmamalıdır. Bu nedenle, AMARYL'in GFR 25 olan hastada JANUVIA'ya alternatif olarak kullanılabilir olması durumunda bu ilaç da kontrendikedir.

### 3. Önemli Uyarılar
- AMARYL, yemeklerden kısa bir zaman önce veya yemeklerle birlikte alınmalıdır.
- Hipogliseminin olası semptomları mevcut olabilir. Bununla birlikte, terleme, nemli cilt, anksiyete, taşikardi, hipertansiyon, çarpıntı, anjina pektoris ve kardiyak aritmiler gibi adrenerjik karşı regülasyon belirtileri mevcut olabilir.
- Hipoglisemiyi destekleyen faktörler şunları içerir: hastanın iletişim isteksizliği ya da (yaşlı hastalarda daha sık olarak) yetersizliği, beslenme yetersizliği, düzensiz öğün aralıkları veya öğün atlama veya açlık süreleri, diyette değişiklikler, fiziksel egzersiz ile karbonhidrat alımı arasında dengesizlik, alkol tüketimi vb.

### 4. Kaynaklar
- AMARYL 2 MG TABLET | KÜB Madde 4.3: Kontrendikasyonlar
- AMARYL 2 MG TABLET | KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri
- Hasta profil bilgileri (yaş, böbrek/karaciğer fonksiyonu, mevcut ilaçlar, alerjiler, lab değerleri)

---

## [v3_q23] Soru 23
**Scores:** Faithfulness=1.000 | Context Recall=0.667

**Soru:** Miyastenia gravis hastasına AVELOX başlanabilir mi?

**Ground Truth:**
Moksifloksasin (AVELOX) miyastenia gravis hastalarında kontrendikedir veya dikkatle kullanılmalıdır. Florokinolonların nöromüsküler blokajı artırabileceği ve miyasteniya semptomlarını şiddetlendirebileceği bilinmektedir. KÜB belgesinde bu uyarı mevcuttur.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hayır, AVELOX kullanımı miyastenia gravis hastasına kontrendikedir. Miyastenia gravis hastalarının moksifloksasin tedavisinde ciddi advers reaksiyonlar gözlemlenebilir, bu nedenle dikkatli kullanımı önerilir veya alternatif tedavi seçenekler bulunmadığında yalnızca dikkatli yarar/risk değerlendirmesinden sonra başlatılmalıdır.

### 2. Detaylı Analiz
Miyastenia gravis hastasına AVELOX kullanımında ciddi advers reaksiyonlar gözlemlenebilir, bu nedenle dikkatli kullanımı önerilir. Moksifloksasin tedavisinde yaygın olarak görülen advers reaksiyonlar kas-iskelet ve periferal sinir sistemi (tendinit, tendon rüptürü, tendonlarda şişme veya  enflamasyon, karıncalanma veya uyuşma, kol ve bacaklarda uyuşukluk, kas ağrısı, kas güçsüzlüğü, eklem ağrısı, eklemlerde şişme gibi) artralji, miyalji, periferal nöropati ve merkezi sinir sistemi etkileridir (halüsinasyon, anksiyete, depresyon, intihar eğilimi, insomnia, şiddetli baş ağrısı ve konfüzyon) (Bkz. Bölüm 4.8). Bu reaksiyonlar, AVELOX başladıktan sonra saatler ya da haftalar içinde görülebilir. Her yaş grubundan veya önceden mevcut risk faktörleri olmayan hastalar, bu advers reaksiyonları yaşamıştır.

### 3. Önemli Uyarılar
- Moksifloksasin tedavisinde ciddi advers reaksiyonlar gözlemlenebilir, bu nedenle dikkatli kullanımı önerilir.
- Dikkatli yarar/risk değerlendirmesinden sonra AVELOX'un miyastenia gravis hastasına başlatılması yalnızca alternatif tedavi seçenekler bulunmadığında önerilir.
- Moksifloksasinle tedavisi yalnızca akut bakteriyel sinüzit ve kronik bronşitin akut bakteriyel alevlenmesinde ancak daha önceki tedavilerin başarısız olması veya alternatif oral tedavilerin bulunmaması durumunda kullanılmalıdır.
- AVELOX, potasyum seviyelerini düşürmek için ilaç kullanan hastalarda veya klinik olarak anlamlı bradikardi ile ilişkili ilaç kullanan hastalarda dikkatli kullanılmalıdır.
- Moksifloksasin QT aralığını uzatan diğer ilaçlarla eşzamanlı olarak kullanılmamalıdır.

### 4. Kaynaklar
- KÜB: AVELOX 400 MG FILM KAPLI TABLET | KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri
- KÜB: AVELOX 400 MG FILM KAPLI TABLET | KÜB Madde 4.8: İstenmeyen Etkiler
- Graf: Neo4j veritabanı bulguları

---

## [v3_q24] Soru 24
**Scores:** Faithfulness=0.833 | Context Recall=1.000

**Soru:** TEGRETOL kullanan hastada LAMICTAL DC dozu neden artırılmalıdır?

**Ground Truth:**
Karbamazepin (TEGRETOL) güçlü CYP3A4 indükleyicisidir ve aynı zamanda lamotrijin glukuronidasyonunu hızlandırır. Lamotrijin (LAMICTAL DC) karbamazepin ile birlikte kullanıldığında plazma yarılanma ömrü yaklaşık yarıya iner. Bu nedenle lamotrijin dozu karbamazepin alan hastalarda belirgin şekilde artırılmalıdır.

**Model Yanıtı:**
 ### 1. Kısa Özet
Lamotrigin (LAMICTAL DC 100 MG COZUNUR / CIGNEME TABLETI) kullanılan epilepsi hastaları için, TEGRETOL (TEGRETOL 200 MG DEGISTIRILMIS SALIMLI TABLET) dozu artırılması önerilmemektedir. Bu tedaviye başlamadan önce, hastanın böbrek fonksiyonunu kontrol ederek karaciğer yetmezliği durumunda kontrendikedir.

### 2. Detaylı Analiz
Lamotrigin (LAMICTAL DC 100 MG COZUNUR / CIGNEME TABLETI) kullanılan epilepsi hastaları için, TEGRETOL (TEGRETOL 200 MG DEGISTIRILMIS SALIMLI TABLET) dozu artırılması önerilmemektedir. Bu tedaviye başlamadan önce, hastanın böbrek fonksiyonunu kontrol ederek karaciğer yetmezliği durumunda kontrendikedir.

### 3. Önemli Uyarılar
- Dikkat: 2 ilaç birlikte kardiyak / qt uzaması riski taşıyor: LAMICTAL DC 100 MG COZUNUR / CIGNEME TABLETI, TEGRETOL 200 MG DEGISTIRILMIS SALIMLI TABLET
- Dikkat: 2 ilaç birlikte hepatotoksisite riski taşıyor: LAMICTAL DC 100 MG COZUNUR / CIGNEME TABLETI, TEGRETOL 200 MG DEGISTIRILMIS SALIMLI TABLET
- Dikkat: 2 ilaç birlikte kanama / hematolojik risk riski taşıyor: LAMICTAL DC 100 MG COZUNUR / CIGNEME TABLETI, TEGRETOL 200 MG DEGISTIRILMIS SALIMLI TABLET
- Dikkat: 2 ilaç birlikte nörotoksisite / sss riski taşıyor: LAMICTAL DC 100 MG COZUNUR / CIGNEME TABLETI, TEGRETOL 200 MG DEGISTIRILMIS SALIMLI TABLET
- Dikkat: 2 ilaç birlikte alerji / anafilaksi riski taşıyor: LAMICTAL DC 100 MG COZUNUR / CIGNEME TABLETI, TEGRETOL 200 MG DEGISTIRILMIS SALIMLI TABLET

### 4. Kaynaklar
- KÜB: LAMICTAL DC 100 MG COZUNUR / CIGNEME TABLETI | KÜB Madde 4.2[geriyatrik]: Pozoloji ve Uygulama Şekli — Geriyatrik Popülasyon
- KÜB: TEGRETOL 200 MG DEGISTIRILMIS SALIMLI TABLET | KÜB Madde 4.2[bobrek_karaciger]: Pozoloji ve Uygulama Şekli — Böbrek / Karaciğer Yetmezliği
- Graf: GRAF VERİTABANI BULGULARI (Neo4j)

---

## [v3_q25] Soru 25
**Scores:** Faithfulness=0.857 | Context Recall=1.000

**Soru:** JARDIANCE başlanan hastada üriner enfeksiyon riski hakkında neler söylenebilir?

**Ground Truth:**
Empagliflozin (JARDIANCE) üriner glukoz atılımını artırdığından genitoüriner enfeksiyon riskini yükseltir. KÜB belgesinde tekrarlayan üriner enfeksiyon öyküsü olan hastalarda dikkatli kullanım önerilmektedir. Üriner enfeksiyon belirtileri yakın izlenmelidir.

**Model Yanıtı:**
 ### 1. Kısa Özet
JARDIANCE (empagliflozin) kullanımında, üriner enfeksiyon riski hakkında bilgi verilmemektedir. Ancak, diğer tıbbi ürünlerle etkileşimlerin ve diğer etkileşim şekillerinin açıklanmasına rağmen, empagliflozinin primer metabolizma yolunun glukuronidasyon olduğuna düşündürülmektedir. Bu nedenle, OAT3, OATP1B1 ve OATP1B3 substratıdır ancak OAT1 ve OCT2'nin substratı değildir. Empagliflozin, P-glikoprotein (P-gp) ve meme kanseri direnç proteininin (BCRP) bir substratıdır.

### 2. Detaylı Analiz
JARDIANCE (empagliflozin) kullanımında, üriner enfeksiyon riski hakkında bilgi verilmemektedir. Ancak, diğer tıbbi ürünlerle etkileşimlerin ve diğer etkileşim şekillerinin açıklanmasına rağmen, empagliflozinin primer metabolizma yolunun glukuronidasyon olduğuna düşündürülmektedir. Bu nedenle, OAT3, OATP1B1 ve OATP1B3 substratıdır ancak OAT1 ve OCT2'nin substratı değildir. Empagliflozin, P-glikoprotein (P-gp) ve meme kanseri direnç proteininin (BCRP) bir substratıdır.

### 3. Önemli Uyarılar
Bilgi verilmemektedir.

### 4. Kaynaklar
- JARDIANCE 10 MG FILM KAPLI TABLET | KÜB Madde 4.5: Diğer Tıbbi Ürünlerle Etkileşimler
- JARDIANCE 10 MG FILM KAPLI TABLET | KÜB Madde 4.3: Kontrendikasyonlar

---

## [v3_q26] Soru 26
**Scores:** Faithfulness=1.000 | Context Recall=1.000

**Soru:** Hiperpotasemi olan hastada CO-DIOVAN kullanılabilir mi?

**Ground Truth:**
Valsartan/hidroklorotiyazid (CO-DIOVAN) kombinasyonunda valsartan bileşeni potasyum düzeyini artırabilir. Hiperpotasemisi olan hastalarda ARB içeren ilaçlar dikkatle kullanılmalıdır. Serum potasyum izlemi zorunludur; ciddi hiperpotasemi durumunda kontrendikedir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hiperpotasemi olan hastalara CO-DIOVAN kullanılabilir değildir. Bu ilaç, serum potasyumu takibi önerilir ve potasyum takviyesi, potasyum tutucu diüretikler, potasyum içeren yapay tuzlar veya potasyum düzeylerini artıran heparin vs. gibi diğer ilaçlar ile birlikte tavsiye edilmemektedir.

### 2. Detaylı Analiz
CO-DIOVAN, valsartan ve hidroklorotiyazid içeren bir ilaçtır. Bu ilaç, serum potasyumu takibi önerilir ve potasyum takviyesi, potasyum tutucu diüretikler, potasyum içeren yapay tuzlar veya potasyum düzeylerini artıran heparin vs. gibi diğer ilaçlar ile birlikte tavsiye edilmemektedir. Bu nedenle, hiperpotasemi olan hastalara CO-DIOVAN kullanılabilir değildir.

### 3. Önemli Uyarılar
* Serum potasyumu takibi önerilir.
* Potasyum takviyesi, potasyum tutucu diüretikler, potasyum içeren yapay tuzlar veya potasyum düzeylerini artıran heparin vs. gibi diğer ilaçlar ile birlikte CO-DIOVAN kullanılmasına karşı sürdürülmüş olmalıdır.

### 4. Kaynaklar
* KÜB: CO-DIOVAN 160 MG/12,5 MG FILM KAPLI TABLET | KÜB Madde 4.3: Kontrendikasyonlar
* KÜB: CO-DIOVAN 160 MG/12,5 MG FILM KAPLI TABLET | KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri
* Graf Veritabani Bulguları (Neo4j): Graf Tabanlı Kontrendikasyonlar (Neo4j)

---

## [v3_q27] Soru 27
**Scores:** Faithfulness=0.375 | Context Recall=0.500

**Soru:** 80 yaşındaki hastada RENITEC başlangıç dozu ne olmalı?

**Ground Truth:**
Enalapril (RENITEC) yaşlı hastalarda böbrek fonksiyonu azalmış olabileceğinden düşük başlangıç dozuyla başlanmalıdır. Geriyatrik hastalarda 2.5 mg başlangıç dozu önerilir, böbrek fonksiyonu ve kan basıncı yanıtına göre titre edilir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Renitec, 80 yaşındaki kadın hastaları için bir ilaçtır. Ayrıca, böbrek yetmezliği durumunda kontrendikedir. Ancak, bu ilaç enalaprile, yardımcı maddelerden herhangi birine veya başka bir ADE inhibitörüne karşı aşırı duyarlılığı olduğu bilinen hastalarda, daha önce bir ADE inhibitörü tedavisi ile ilişkili anjioödem öyküsü bulunan hastalarda, kalıtsal veya idyopatik anjiyoödem, ve gebelikte kontrendikedir. Bu nedenle, 80 yaşındaki bu hastaya başlangıç dozunu belirlemek için bir cüzdanlık yapmanız gerekebilir.

### 2. Detaylı Analiz
Renitec, aşağıdaki durumlarda kontrendikedir:
- Enalaprile, yardımcı maddelerden herhangi birine veya başka bir ADE inhibitörüne karşı aşırı duyarlılığı olduğu bilinen hastalarda,
- Daha önce bir ADE inhibitörü tedavisi ile ilişkili anjioödem öyküsü bulunan hastalarda,
- Kalıtsal veya idyopatik anjiyoödem,
- Gebelikte kontrendikedir.

Bu nedenle, 80 yaşındaki bu hastaya başlangıç dozunu belirlemek için bir cüzdanlık yapmanız gerekebilir. Ancak, bu ilaç kullanmadan önce, hastanın enalaprile veya başka bir ADE inhibitörü kullandığını veya kullanmaktadırığını kontrol ederek, ilaçtan yararlanabilmesi için doz ayarı gerekebilir.

### 3. Önemli Uyarılar
- Renitec, enalaprile veya başka bir ADE inhibitörü kullandığınızda, aşırı duyarlılık olabilir. Bu durumda, ilaçtan kaçınmanız gerekebilir.
- Renitec, gebelikte kontrendikedir. Bu nedenle, gebelikte hastalar için bu ilaç kullanılması önerilmez.

### 4. Kaynaklar
- KÜB: RENITEC 5 MG TABLET | KÜB Madde 4.3: Kontrendikasyonlar
- Graf Tabanlı Kontrendikasyonlar (Neo4j):
  - RENITEC 5 mg tablet → gebelik durumunda kontrendike
  - A-FERIN 300 MG/2 MG/10 MG KAPSUL → böbrek yetmezliği durumunda kontrendike
  - A-FERIN SINUS 500 MG/30 MG/1,25 MG FILM KAPLI TABLET → böbrek yetmezliği durumunda kontrendike
  - A-FERIN ZERO 120 MG/5 ML PEDIATRIK SURUP → böbrek yetmezliği durumunda kontrendike
  - A-FERIN ZERO 6 PLUS 250 MG/5 ML ORAL SUSPANSIYON → böbrek yetmezliği durumunda kontrendike
  - A-FERIN HOT TEK KULLANIMLIK TOZ ICEREN POSET → böbrek yetmezliği durumunda kontrendike
- Graf Tabanlı Etkileşimler (Neo4j):
  - RENITEC 5 mg tablet ↔ Enalaprilin lityum

---

## [v3_q28] Soru 28
**Scores:** Faithfulness=1.000 | Context Recall=1.000

**Soru:** İMURAN kullanan hastada ÜRİKOLİZ başlanırsa ne olur?

**Ground Truth:**
Allopurinol (ÜRİKOLİZ) azatioprinin (İMURAN) metabolizmasını inhibe eder; ksantin oksidaz inhibisyonu nedeniyle azatioprin toksisite riski dramatik biçimde artar. Birlikte kullanımda azatioprin dozu dörtte birine indirilmelidir veya bu kombinasyondan kaçınılmalıdır. KÜB belgesinde bu etkileşim kontraendikasyon olarak belirtilmiştir.

**Model Yanıtı:**
 ### 1. Kısa Özet
İMURAN kullanan bir hastaya ÜRİKOLİZ başlanmasına karşın, kontrendikedir. Bu iki ilaç birlikte hematolojik ve alerji/anafilaksi riskleri taşıyor. Hasta profilini göz önünde bulundurarak, yukarıdaki bilgilerle ilgili kaynaklarının desteklediği uyarıları değerlendirilmelidir.

### 2. Detaylı Analiz
İMURAN (50 mg film kaplı tablet) ve ÜRİKOLİZ® (300 mg tablet) birlikte kullanıldığında, hematolojik ve alerji/anafilaksi riskleri taşıyabilir. Bu iki ilaç, canlı organizma aşılarına karşı neden olabilecek potansiyel tehlikeler vardır (KÜB Madde 4.4). ÜRİKOLİZ, ksantin oksidaz inhibitürü ile eşzamanlı olarak verildiğinde, ksantin oksidaz inhibisyonu bunların aktivitelerini uzatacaktır ve bu da serum konsantrasyonları toksik seviyelere ulaşabilir (KÜB Madde 4.5). Bu nedenle, ÜRİKOLİZ'in 6-merkaptopurin veya azatioprin ile eş zamanlı kullanımından kaçınılmalıdır.

### 3. Önemli Uyarılar
- Hasta profilini göz önünde bulundurarak, yukarıdaki bilgilerle ilgili kaynaklarının desteklediği uyarıları değerlendirilmelidir.
- ÜRİKOLİZ'in 6-merkaptopurin veya azatioprin ile eş zamanlı kullanımından kaçınılmalıdır.

### 4. Kaynaklar
- IMURAN 50 MG FILM KAPLI TABLET | KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri
- ÜRİKOLİZ® 300 mg tablet | KÜB Madde 4.5: Diğer Tıbbi Ürünlerle Etkileşimler
- Graf veritabanında ilgili kontrendikasyon veya etkileşim kaydı bulunamadı.
- OTOMATİK KÜMÜLATİF RİSK ANALİZİ
- [CYP450 Analizi] (Bilgi yok: Bu konu incelenen KÜB belgelerinde yer almamaktadır.)

---

## [v3_q29] Soru 29
**Scores:** Faithfulness=0.000 | Context Recall=1.000

**Soru:** Feokromasitoma hastasına NORODOL başlanabilir mi?

**Ground Truth:**
Haloperidol (NORODOL) feokromasitomada kontrendikedir. Dopamin reseptör blokajı nedeniyle hipertansif kriz tetiklenebilir. KÜB belgesinde feokromasitoma kontrendikasyon olarak yer almaktadır.

**Model Yanıtı:**
 ### 1. Kısa Özet
Feokromasitoma hastasına NORODOL başlanabilir mi? Hayır, kontrendikedir. Bu ilaç bazal gangliyon lezyonlarmda kontrendikasyon olarak kullanılmaktadır ve Parkinson hastalarında da hipersensitivitesi olduğu bilinen kişilerde kullanılabilir. Ayrıca, QT arahgı uzamasma neden olabilecek potansiyeli vardır ve 2. veya 3. derece kalp boğu ve diyetilmemiş hipokalemi hastalarında, T orsades de Pointes, klinik yönden anlarnh bradikardi ya da ventrikiiler aritmi olan, QTc ara11gı uzaması, S1mf IA ve III antiaritmik ilaçlar ile tedavi edilen aritmisi, kompanse olmamış kalp yetmezliği ve yeni ge7irilmiş akut miyokardiyal infarktUsil gibi klinik avdan onemli kardiyak bozukluk:lan olan hastalarda haloperidol ilaçının kullanımı kontrendikedir.

### 2. Detaylı Analiz
Feokromasitoma hastasına NORODOL başlanabilir mi? Hayır, kontrendikedir. Bu ilaç bazal gangliyon lezyonlarmda kontrendikasyon olarak kullanılmaktadır ve Parkinson hastalarında da hipersensitivitesi olduğu bilinen kişilerde kullanılabilir. Ayrıca, QT arahgı uzamasma neden olabilecek potansiyeli vardır ve 2. veya 3. derece kalp boğu ve diyetilmemiş hipokalemi hastalarında, T orsades de Pointes, klinik yönden anlarnh bradikardi ya da ventrikiiler aritmi olan, QTc ara11gı uzaması, S1mf IA ve III antiaritmik ilaçlar ile tedavi edilen aritmisi, kompanse olmamış kalp yetmezliği ve yeni ge7irilmiş akut miyokardiyal infarktUsil gibi klinik avdan onemli kardiyak bozukluk:lan olan hastalarda haloperidol ilaçının kullanımı kontrendikedir.

### 3. Önemli Uyarılar
- Bu ilaç bazal gangliyon lezyonlarmda kontrendikasyon olarak kullanılmaktadır ve Parkinson hastalarında da hipersensitivitesi olduğu bilinen kişilerde kullanılabilir.
- Ayrıca, QT arahgı uzamasma neden olabilecek potansiyeli vardır ve 2. veya 3. derece kalp boğu ve diyetilmemiş hipokalemi hastalarında, T orsades de Pointes, klinik yönden anlarnh bradikardi ya da ventrikiiler aritmi olan, QTc ara11gı uzaması, S1mf IA ve III antiaritmik ilaçlar ile tedavi edilen aritmisi, kompanse olmamış kalp yetmezliği ve yeni ge7irilmiş akut miyokardiyal infarktUsil gibi klinik avdan onemli kardiyak bozukluk:lan olan hastalarda haloperidol ilaçının kullanımı kontrendikedir.

### 4. Kaynaklar
- KÜB: NORODOL 5 MG TABLET | KÜB Madde 4.3: Kontrendikasyonlar
- Graf: [Graf]
- CYP450 Analizi: [CYP450 Analizi]

---

## [v3_q30] Soru 30
**Scores:** Faithfulness=0.800 | Context Recall=1.000

**Soru:** GFR 15 olan hastada METAFORMAL kullanılabilir mi?

**Ground Truth:**
Metformin (METAFORMAL) GFR 30 mL/dak altında kontrendikedir. GFR 15 şiddetli böbrek yetmezliği olup laktik asidoz riski nedeniyle METAFORMAL bu hastada kesinlikle kullanılmamalıdır.

**Model Yanıtı:**
 ### 1. Kısa Özet
Hayır, METAFORMAL kullanılabilir değil böbrek fonksiyonu (GFR) 15 olan hastalarda. Bu ilacın kullanımına karşı uyarılar vardır ve bu hastaların tedaviye devam edip etmeme ihtiyacını değerlendirmek için glisemik durumu ve aynı zamanda risk faktörleri düzenli aralıklarla takip edilmelidir.

### 2. Detaylı Analiz
Böbrek fonksiyonunun normal olmayan hastalar için METAFORMAL kullanımına karşı uyarılar vardır. Bu ilacın kullanımına karşı uyarılar şunlardır:
- Akut metabolik asidozun herhangi bir tipi (örn; laktik asidoz, diyabetik ketoasidoz)
- Diyabetik prekoma
- Şiddetli böbrek yetmezliği (GFR <30mL/dak),
- Dehidrasyon, şiddetli enfeksiyon, şok gibi böbrek fonksiyonlarını değiştirme potansiyeli olan akut durumlar (bkz. Bölüm 4.4),
- Doku hipoksisine yol açabilecek akut veya kötüleşen kronik hastalıklar örn; dekompanse kalp yetmezliği, respiratuvar yetmezlik, yakın geçmişte miyokard infarktüsü, şok, septisemi,
- Hepatik yetmezlik, akut alkol intoksikasyonu, alkolizm,
- Laktasyon durumlarında kontrendikedir.

Böbrek fonksiyonunun normal olmayan hastalar için METAFORMAL kullanımına karşı uyarılar vardır ve bu hastaların tedaviye devam edip etmeme ihtiyacını değerlendirmek için glisemik durumu ve aynı zamanda risk faktörleri düzenli aralıklarla takip edilmelidir.

### 3. Önemli Uyarılar
- Böbrek fonksiyonunun normal olmayan hastalar için METAFORMAL kullanımına karşı uyarılar vardır.
- Bu hastaların tedaviye devam edip etmeme ihtiyacını değerlendirmek için glisemik durumu ve aynı zamanda risk faktörleri düzenli aralıklarla takip edilmelidir.

### 4. Kaynaklar
- KÜB: METAFORMAL 1000 MG FILM KAPLI TABLET | KÜB Madde 4.2[bobrek_karaciger]: Pozoloji ve Uygulama Şekli — Böbrek / Karaciğer Yetmezliği
- Graf: Graf Tabanlı Kontrendikasyonlar (Neo4j) ve Graf Tabanlı Etkileşimler (Neo4j)

---

## [v3_q31] Soru 31
**Scores:** Faithfulness=0.500 | Context Recall=0.500

**Soru:** Tip-2 diyabetli hastada JARDIANCE kullanımına bağlı gelişebilecek istenmeyen etkiler (madde 4.8) nelerdir?

**Ground Truth:**
Empagliflozin (JARDIANCE) KÜB madde 4.8 uyarınca yaygın görülen istenmeyen etkiler arasında vajinal moniliyazis, vulvovajinit, balanit ve diğer genital enfeksiyonlar, üriner sistem enfeksiyonu, pruritus (genel) ve poliüri yer almaktadır. Ayrıca nadir fakat ciddi olarak nekrotizan fasiit (Fournier gangreni) bildirilmiştir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Empagliflozin (JARDIANCE) kullanımında istenmeyen etkiler hakkında, ketoasidoz riski artabilir. Bu durumda hastanın derhal ketoasidoz açısından değerlendirilmelidir ve tedaviye ara verilmelidir. Diüretiklerle ve insülin ile birlikte kullanıldığında, dehidratasyon ve hipotansiyon riski artabilir.

### 2. Detaylı Analiz
Empagliflozin (JARDIANCE) kullanımında istenmeyen etkiler hakkında ayrıntılar:

- Ketoasidoz riski artabilir. Bu durumda hastanın derhal ketoasidoz açısından değerlendirilmelidir ve tedaviye ara verilmelidir.
- Diüretiklerle (örneğin, tiayazid ve loop diüretikler) birlikte kullanıldığında, dehidratasyon ve hipotansiyon riski artabilir.
- Insülin ile birlikte kullanıldığında, hipoglisemi riskini arttırabilir. Bu nedenle, insülin veya insülin salgılatıcıların daha düşük dozda kullanılması gerekebilir.
- Grafik veriler, empagliflozinin primer metabolizma yolunun UGT1A3, UGT1A8, UGT1A9 ve UGT2B7 aracılığı ile glukuronidasyon olduğunu düşündürür. Empagliflozin, OAT3, OATP1B1 ve OATP1B3 substratıdır ancak OAT1 ve OCT2'nin substratı değildir.
- P-glikoprotein (P-gp) ve meme kanseri direnç proteininin (BCRP) bir substratıdır. Probenesid ile eş zamanlı uygulanması, empagliflozinin pik plazma konsantrasyonlarında ve konsantrasyon zaman eğrisi altında kalan alanda yükselmeye neden olabilir.
- UGT indükleyicilerin (örneğin, rifampisin veya fenitoin) etkisi çalışılmamıştır. Etkilikte muhtemel bir azalma riski nedeniyle, UGT enzimlerinin bilinen indükleyicileriyle eş zamanlı uygulanması önerilmez.

### 3. Önemli Uyarılar
- Empagliflozin, tip 1 diyabet mellitusu olan hastalarda kullanılmamalıdır (Bkz. Bölüm 4.4 "Ketoasidoz").
- Ketoasidoz vakalarının ortaya çıkma olasılığının, daha yüksek empagliflozinin dozlarıyla artıp artmadığı bilinmemektedir.
- Ketoasidozun diyabetes mellitusu olmayan hastalarda da vakalar bildirilmiştir.
- Bulantı, kusma, anoreksi, abdominal ağrı, aşırı susama, nefes almakta güçlük, konfüzyon, olağandışı yorgunluk veya uyku hali gibi spesifik olmayan semptomların görülmesi halinde, ketoasidoz riski düşünülmelidir.
- Majör cerrahi işlemler veya akut ciddi hastalıklar nedeniyle hastaneye yatırılmış hastalarda tedaviye ara verilmelidir. Bu hastalarda ketonların izlenmesi önerilmektedir. Kan keton düzeylerinin ölçülmesi idrar ölçümlerine tercih edilmelidir.
- Empagliflozin tedavisine başlamadan önce, hastanın geçmişindeki ketoasidoza yatkınlık yaratan faktörler dikkate alınmalıdır.

### 4. Kaynaklar
- JARDIANCE 10 MG FILM KAPLI TABLET | KÜB Madde 4.8: İstenmeyen Etkiler
- JARDIANCE 10 MG FILM KAPLI TABLET | KÜB Madde 4.4: Özel Kullanım Uyarıları ve Önlemleri
- Grafik Veritabanı Bulguları (Neo4j)

---

## [v3_q32] Soru 32
**Scores:** Faithfulness=0.429 | Context Recall=1.000

**Soru:** PLAVIX kullanan hastada mantar enfeksiyonu için CANDİDİN başlanırsa ne tür bir etkileşim beklenir?

**Ground Truth:**
Flukonazol (CANDİDİN) orta-güçlü bir CYP2C19 inhibitörüdür. Klopidogrel (PLAVIX) bir ön ilaçtır ve aktif metabolite dönüşümü için CYP2C19 enzimine ihtiyaç duyar. Flukonazol ile birlikte kullanımda klopidogrelin aktif metabolite dönüşümü azalır, bu da antiplatelet etkinin azalmasına ve stent trombozu/kardiyovasküler olay riskinin artmasına neden olabilir.

**Model Yanıtı:**
 ### 1. Kısa Özet
PLAVIX kullanan hastada mantar enfeksiyonu için CANDİDİN başlanırsa, ilaçlar arasında bir etkileşim beklenebilir. CANDİDİN, etkin maddeye ve benzer azol bileşiklerine hassas olduğu bilinen hastalarda kullanılmamalıdır (KÜB Madde 4.3: Kontrendikasyonlar). Bu nedenle, PLAVIX'in CANDİDİN ile birlikte kullanılması kontrendikedir.

### 2. Detaylı Analiz
PLAVIX (klopidogrel) ve CANDIDIN arasında bir etkileşim beklenebilir. CANDİDİN, etkin maddeye, ilacın bileşenlerinden herhangi birisine veya benzer azol bileşiklerine hassas olduğu bilinen hastalarda kullanılmamalıdır (KÜB Madde 4.3: Kontrendikasyonlar). Bu nedenle, PLAVIX'in CANDİDİN ile birlikte kullanılması kontrendikedir.

### 3. Önemli Uyarılar
- CANDİDİN, etkin maddeye ve benzer azol bileşiklerine hassas olduğu bilinen hastalarda kullanılmamalıdır (KÜB Madde 4.3: Kontrendikasyonlar).
- PLAVIX'in CANDİDİN ile birlikte kullanılması kontrendikedir.

### 4. Kaynaklar
- KÜB: CANDIDIN 150 MG KAPSUL | KÜB Madde 4.3: Kontrendikasyonlar
- KÜB: CANDIDIN 150 MG KAPSUL | KÜB Madde 4.5: Diğer Tıbbi Ürünlerle Etkileşimler

---

## [v3_q33] Soru 33
**Scores:** Faithfulness=0.667 | Context Recall=1.000

**Soru:** Emziren bir anne LUSTRAL 50 mg kullanabilir mi? Süte geçişi konusunda KÜB ne diyor?

**Ground Truth:**
Sertralin (LUSTRAL) anne sütüne geçer. KÜB madde 4.6'ya göre, emziren annelerde sertralin kullanımı, ancak anne için beklenen yararın bebek üzerindeki riskten daha üstün olduğu hekim kararıyla mümkündür. Klinik veriler sütteki sertralin miktarının az olduğunu gösterse de bebekler istenmeyen etkiler açısından yakından izlenmelidir.

**Model Yanıtı:**
 ### 1. Kısa Özet
Emziren anne LUSTRAL 50 mg kullanabilir mi? Süte geçişi konusunda KÜB bilgisi yoktur. Ayrıca, LUSTRAL'ın süte geçişindeki etkisini belirleyen CYP450 enzim analizi de bulunamadı.

### 2. Detaylı Analiz
Postpartum depresyon hakkında bilgi yoktur. Ancak, LUSTRAL (brompiradol hydroklorid), süte geçişindeki etkisini belirleyen CYP450 enzim analizi de bulunamadı. Bu nedenle, emziren anne LUSTRAL 50 mg kullanabilip kullanamazığı hakkında bilgi yoktur.

### 3. Önemli Uyarılar
- LUSTRAL'ın süte geçişindeki etkisini belirleyen CYP450 enzim analizi bulunamadı.
- Bu konu incelenen KÜB belgelerinde yer almamaktadır.

### 4. Kaynaklar
- [LUSTRAL (brompiradol hydroklorid) KÜB](Kümesel Doktor Hizmetleri - Lustral (brompiradol hydroklorid))
- [CYP450 Analizi](https://www.cyp450.org/)

---
