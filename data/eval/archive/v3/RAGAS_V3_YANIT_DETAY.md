# RAGAS v3 — Soru Bazlı Yanıt ve Değerlendirme Belgesi

**Tarih:** 2026-04-14
**RAG Modeli:** Claude Haiku (claude-haiku-4-5-20251001)
**RAGAS Değerlendirici:** Mistral 7B v0.3 (local, LM Studio)
**Toplam Soru:** 30 | **Genel Ortalama:** F=0.7565 / CR=0.7377

---

## Hızlı Tablo

| # | ID | Kategori | F | CR | Durum |
|---|-----|----------|---|----|-------|
| 1 | v3_q01 | kontrendikasyon | 0.80 | 1.00 | ✅ |
| 2 | v3_q02 | doz_bobrek | NaN | 1.00 | ⚠️ GT uyuşmazlığı |
| 3 | v3_q03 | cyp450_etkilesim | NaN | 1.00 | ✅ |
| 4 | v3_q04 | gebelik | NaN | 1.00 | ✅ |
| 5 | v3_q05 | kontrendikasyon_karaciger | 1.00 | 0.50 | ✅ |
| 6 | v3_q06 | doz_pediyatrik | 0.67 | NaN | ⚠️ Doz hesabı yetersiz |
| 7 | v3_q07 | etkilesim_farmakodinamik | NaN | 1.00 | ✅ |
| 8 | v3_q08 | doz_bobrek | 0.57 | 0.33 | 🔴 Düşük |
| 9 | v3_q09 | kontrendikasyon | 0.83 | NaN | ✅ |
| 10 | v3_q10 | cyp450_etkilesim | NaN | 0.75 | 🔴 Yanlış klinik sonuç |
| 11 | v3_q11 | laktasyon | NaN | 0.33 | 🔴 Corpus boşluğu |
| 12 | v3_q12 | etkilesim_ciddi | NaN | 1.00 | ✅ |
| 13 | v3_q13 | doz_geriyatrik | 1.00 | 0.67 | ✅ |
| 14 | v3_q14 | kontrendikasyon | 1.00 | 0.50 | ✅ |
| 15 | v3_q15 | etkilesim_doz | 1.00 | 1.00 | ✅ Mükemmel |
| 16 | v3_q16 | doz_bobrek | NaN | 0.33 | ⚠️ Düşük context |
| 17 | v3_q17 | cyp450_etkilesim | NaN | 0.67 | ✅ |
| 18 | v3_q18 | kontrendikasyon | NaN | 1.00 | ✅ |
| 19 | v3_q19 | etkilesim_farmakodinamik | NaN | 1.00 | ✅ |
| 20 | v3_q20 | doz_karaciger | NaN | NaN | ⚠️ İkisi de NaN |
| 21 | v3_q21 | etkilesim_ciddi | NaN | 1.00 | ⚠️ Aşırı kontrendikasyon |
| 22 | v3_q22 | doz_bobrek | NaN | 0.00 | 🔴 Corpus boşluğu |
| 23 | v3_q23 | kontrendikasyon | 0.00 | 0.00 | 🔴 Bilgi yok |
| 24 | v3_q24 | etkilesim_doz | NaN | 1.00 | ✅ |
| 25 | v3_q25 | yan_etki | 0.75 | 1.00 | ⚠️ BİLGİ YOK ama CR=1 |
| 26 | v3_q26 | kontrendikasyon | 0.60 | 1.00 | ✅ |
| 27 | v3_q27 | doz_geriyatrik | NaN | 1.00 | ✅ |
| 28 | v3_q28 | etkilesim_ciddi | NaN | 0.67 | ✅ |
| 29 | v3_q29 | kontrendikasyon | 0.86 | 0.67 | ✅ |
| 30 | v3_q30 | doz_bobrek | NaN | 0.50 | ⚠️ |

---

## Soru 1 — v3_q01 [kontrendikasyon]

**Soru:** TEGRETOL kullanan hastaya SANORONE eklenebilir mi?
**F:** 0.8000 | **CR:** 1.0000 | **Contexts:** 9 | **Yanıt:** 2449 karakter

**Ground Truth:**
> Karbamazepin (TEGRETOL) ile amiodaron (SANORONE) kombinasyonu kontrendike değildir ancak her ikisi de CYP3A4 substratıdır; karbamazepin güçlü CYP3A4 indükleyicisi olarak amiodaronun plazma düzeyini düşürür. Birlikte kullanımda dikkatli olunmalı, kardiyak izlem yapılmalıdır.

**Sistem Yanıtı:**
```
Hayır, TEGRETOL kullanan hastaya SANORONE eklenmesi kontrendikedir ve bu kombinasyon kullanılmamalıdır.

**Temel neden — Atriyoventriküler blok riski:**

TEGRETOL'ün kontrendikasyonları arasında "atriyoventriküler bloğu olan hastalar" yer almaktadır [TEGRETOL® 200 mg | Madde 4.3 | Kontrendikasyonlar]. Bu hasta zaten atriyal fibrilasyon tanısı almıştır. SANORONE'un (amiodaron) ise kalp ileti sistemini deprese etme riski vardır ve özellikle "2. veya 3. derece A-V blok, sinoatrial blok veya bifasiküler blok gelişmesi durumunda tedavi kesilmelidir" [SANORONE 200 mg | Madde 4.4 | Özel Kullanım Uyarıları ve Önlemleri]. Her iki ilaç da ileti bozukluğu riskini arttırdığı için kombinasyon güvenli değildir.

**İkinci neden — Antiaritmik kombinasyon kontrendikasyonu:**

SANORONE'un KÜB belgesinde açı...
```

**Analiz:** GT 'kontrendike değil, dikkatli kullan' derken sistem 'kontrendike' diyor. Aşırı muhafazakâr.

---

## Soru 2 — v3_q02 [doz_bobrek]

**Soru:** GFR 20 olan hastada PRADAXA dozu nasıl ayarlanmalı?
**F:** NaN | **CR:** 1.0000 | **Contexts:** 5 | **Yanıt:** 1210 karakter

**Ground Truth:**
> Dabigatran (PRADAXA) GFR 30 mL/dak altında kontrendikedir. GFR 20 olan hastada PRADAXA kullanılmamalıdır.

**Sistem Yanıtı:**
```
**KESİN KARAR:** Hayır, bu hastaya standart doz PRADAXA uygulanmaz; doz azaltılması gerekir.

Bu 72 yaşındaki hastanın GFR değeri 20 mL/dak/1.73m² olup, Evre 4 (G4, GFR 15-29) kronik böbrek hastalığı tanısındadır. KÜB belgelerine göre şiddetli böbrek yetmezliğinin sınırı CrCL <30 ml/dk'dır ve bu sınırın altında PRADAXA mutlak kontrendikedir [PRADAXA® 150 mg sert kapsül | KÜB Madde 4.3 | Kontrendikasyonlar].

Hastanın kreatinin klirensinin tahmini için Cockgroft-Gault yöntemi kullanılması önerilmektedir [PRADAXA® 150 mg sert kapsül | KÜB Madde 4.2[geriyatrik] | Pozoloji ve Uygulama Şekli]. Sunulan GFR değeri 20 olup, bu hastanın şiddetli böbrek yetmezliği aralığında (CrCL <30 ml/dk) yer aldığını göstermektedir.

**KRİTİK UYARI:** KÜB belgesinde açıkça belirtilmektedir: "Şiddetli renal bozuk...
```

**Analiz:** GT 'kontrendike' derken sistem 'doz azalt' diyor. Yanlış yön.

---

## Soru 3 — v3_q03 [cyp450_etkilesim]

**Soru:** SPORANOX kullanan hastada CORDARONE kan düzeyi nasıl etkilenir?
**F:** NaN | **CR:** 1.0000 | **Contexts:** 9 | **Yanıt:** 1683 karakter

**Ground Truth:**
> İtrakonazol (SPORANOX) güçlü CYP3A4 inhibitörüdür. Amiodaron (CORDARONE) CYP3A4 substratıdır. Birlikte kullanımda amiodaronun plazma konsantrasyonu artar, QT uzaması ve kardiyak toksisite riski yükselir. Bu kombinasyondan kaçınılmalıdır.

**Sistem Yanıtı:**
```
SPORANOX kullanan bu hastada CORDARONE kan düzeyinin artma riski vardır ve dikkatli izlem gerektirilir.

İtrakonazol güçlü bir CYP3A4 inhibitörüdür. [SPORANOX | Madde 4.5] Amiodaron CYP3A4 ile metabolize edildiğinden, SPORANOX tarafından bu enzimin inhibisyonu amiodaronun plazma konsantrasyonunu artırabilir. Bu mekanizm aracılığıyla, SPORANOX'ın CORDARONE kan düzeyini yükseltme potansiyeli mevcuttur.

Bu kombinasyon özellikle bu hastada endişe vericidir çünkü her iki ilaç da kardiyak riske katkıda bulunur. SPORANOX negatif inotrop etkiye sahiptir ve konjestif kalp yetmezliği bildirilmiştir; [SPORANOX | Madde 4.4] ayrıca CORDARONE QT aralığını uzatır ve Torsades de Pointes riski taşır. [CORDARONE | Madde 4.5] Otomatik kümülatif risk analizi da her iki ilacın birlikte kardiyak etkileri ve QT...
```

**Analiz:** GT ile uyumlu. CYP3A4 mekanizması doğru.

---

## Soru 4 — v3_q04 [gebelik]

**Soru:** Gebelikte LAROXYL kullanımı güvenli midir?
**F:** NaN | **CR:** 1.0000 | **Contexts:** 5 | **Yanıt:** 986 karakter

**Ground Truth:**
> Amitriptilin (LAROXYL) gebelikte kullanımı önerilmez. Gebelik kategorisi C olup hayvansal çalışmalarda fetal risk gösterilmiştir. Özellikle üçüncü trimesterde neonatal yoksunluk sendromu riski vardır. Klinik zorunluluk yoksa kullanılmamalıdır.

**Sistem Yanıtı:**
```
Hayır, LAROXYL gebelikte kontrendikedir.

KÜB belgesine göre LAROXYL'in gebelik kategorisi D'dir ve "gebelik döneminde özellikle de ilk ve son trimesterde kullanılmamalıdır" [LAROXYL 25 mg | Madde 4.6 | Gebelik ve laktasyon]. Ayrıca KÜB'de açıkça "Gebelik ve emzirmede kontrendikedir" belirtilmektedir [LAROXYL 25 mg | Madde 4.3 | Kontrendikasyonlar].

Gebeliğin son trimesterinde verilen trisiklik antidepresanlar (amitriptilin LAROXYL'in etkin maddesidir) fetusta solunum depresyonu, yoksunluk semptomları ve ajitasyon gibi ciddi yan etkilere neden olabilir [LAROXYL 25 mg | Madde 4.6 | Gebelik ve laktasyon]. İdrar retansiyonu da annedeki amitriptilin miktarıyla ilişkilidir. Gebelik döneminde güvenliliği kanıtlanmamıştır.

Bu hasta 28 yaşında, gebelik durumundadır ve depresyon tanısı bulunmakta...
```

**Analiz:** Klinik karar doğru. Gebelik kategorisi C/D farkı var.

---

## Soru 5 — v3_q05 [kontrendikasyon_karaciger]

**Soru:** Child-Pugh C karaciğer yetmezliği olan hastada ONAXAN kullanılabilir mi?
**F:** 1.0000 | **CR:** 0.5000 | **Contexts:** 5 | **Yanıt:** 1121 karakter

**Ground Truth:**
> Rivaroksaban (ONAXAN) Child-Pugh B ve C karaciğer hastalığında kontrendikedir. Karaciğer yetmezliği koagülopati ile ilişkili olduğundan ve rivaroksaban hepatik metabolizma ile atılımına bağlı olduğundan, bu hastalarda kullanılmamalıdır.

**Sistem Yanıtı:**
```
Hayır, kontrendikedir.

ONAXAN® Child-Pugh C karaciğer yetmezliği olan bu hastada kullanılamaz. KÜB belgesinin 4.3 Kontrendikasyonlar bölümünde açıkça belirtildiği üzere, "Child Pugh B ve C'li siroz hastaları dahil olmak üzere koagülopati ve klinik açıdan anlamlı kanama riskiyle ilişkili hepatik hastalık" durumunda ONAXAN® kontrendikedir. [ONAXAN® 20 mg film kaplı tablet | Madde 4.3 | Kontrendikasyonlar]

Bu hastanın mevcut karaciğer fonksiyonu durumu (Child-Pugh C) doğrudan kontrendikasyon kriteridir. Ayrıca, hastanın yüksek bilirubin değeri (3.2 mg/dL) ve düşük albümin seviyesi (180) da ağır hepatik disfonksiyonun göstergeleridir ve ONAXAN® kullanımını güvensiz kılmaktadır. KÜB'de belirtildiği gibi, bu hasta popülasyonunda "koagülopati ve klinik açıdan anlamlı kanama riski" mevcuttur ve ...
```

**Analiz:** F=1.00. CR=0.50 — koagülopati mekanizması kısmi.

---

## Soru 6 — v3_q06 [doz_pediyatrik]

**Soru:** 8 yaşındaki 25 kg ağırlığında epilepsi hastasında KEPPRA dozu nasıl belirlenmeli?
**F:** 0.6667 | **CR:** NaN | **Contexts:** 5 | **Yanıt:** 1877 karakter

**Ground Truth:**
> Levetirasetam (KEPPRA) 4-11 yaş arası çocuklarda başlangıç dozu günde iki kez 10 mg/kg (vücut ağırlığına göre). 25 kg için başlangıç dozu günde iki kez 250 mg'dır. İdame doz titrasyon ile günde iki kez 30 mg/kg'a kadar artırılabilir.

**Sistem Yanıtı:**
```
Epilepsi tedavisiyle 8 yaşındaki 25 kg ağırlığındaki bu hasta için KEPPRA dozu klinik yanıt ve toleransa göre belirlenmelidir. Böbrek fonksiyonu bilinmediği için öncelikle normal böbrek fonksiyonu varsayımı altında dozlama yapılabilir; ancak böbrek fonksiyonu değerlendirmesi kritik öneme sahiptir.

Pediyatrik dozlama rehberine göre, 4-11 yaş arası ve 50 kg altındaki çocuklarda başlangıç dozu günde iki kez 10 mg/kg'dır. Bu hasta için (25 kg) başlangıç dozu günde iki kez 250 mg olmalıdır [KEPPRA 250 mg film kaplı tablet | Madde 4.2 | Pediyatrik Popülasyon — Doz Tablosu]. Klinik yanıt ve toleransa göre, doz günde iki kez 30 mg/kg'a (bu hasta için günde iki kez 750 mg'a) çıkartılabilir. Doz değişimleri her 2 haftada bir, günde iki kez 10 mg/kg'ı geçmemek şartıyla gerçekleştirilmelidir [KEPPRA ...
```

**Analiz:** Spesifik doz hesabı (250 mg, 10 mg/kg) eksik.

---

## Soru 7 — v3_q07 [etkilesim_farmakodinamik]

**Soru:** İSOPTİN kullanan hastaya CONCOR eklenirse ne olur?
**F:** NaN | **CR:** 1.0000 | **Contexts:** 7 | **Yanıt:** 1338 karakter

**Ground Truth:**
> Verapamil (İSOPTİN) ve bisoprolol (CONCOR) kombinasyonu AV blok ve bradikardi riskini artırır. Her ikisi de kalp hızını yavaşlattığından bu kombinasyondan kaçınılmalı veya çok yakın kardiyak izlem altında kullanılmalıdır. KÜB'de bu kombinasyon için özel uyarı mevcuttur.

**Sistem Yanıtı:**
```
**Hayır, kontrendikedir.**

İSOPTİN® SR 240 mg kullanan hastaya CONCOR® (bisoprolol) eklenmesi mutlak kontrendikedir. Bu kombinasyon, İSOPTİN® SR 240 mg KÜB belgesi Madde 4.3'te açıkça yasaklanmıştır.

İSOPTİN® SR 240 mg Film Tablet kullanımı "Eş zamanlı beta-blokör kullanan hastalar" durumunda kontrendikedir [İSOPTİN® SR 240 mg | Madde 4.3 | Kontrendikasyonlar]. CONCOR® (bisoprolol) selektif beta-1 adrenerjik bloköre ait bir beta-blokördür ve bu kontrendikasyonun kapsamına tam olarak girmektedir.

Ek olarak, İSOPTİN® SR 240 mg KÜB belgesi Madde 4.4'te belirtildiği üzere, verapamil ile beta-adrenerjik blokör alanı hastalarda "her hangi bir derecede ventrikül disfonksiyonu" olan olgularda bu kombinasyondan kaçınılmalıdır [İSOPTİN® SR 240 mg | Madde 4.4 | Kalp Yetmezliği].

Bu hasta 66 yaşın...
```

**Analiz:** Klinik karar doğru ama 'mutlak kontrendike' GT'den daha katı.

---

## Soru 8 — v3_q08 [doz_bobrek]

**Soru:** GFR 35 olan hastada LAMICTAL DC dozu nasıl ayarlanmalı?
**F:** 0.5714 | **CR:** 0.3333 | **Contexts:** 5 | **Yanıt:** 1271 karakter

**Ground Truth:**
> Lamotrijin (LAMICTAL DC) böbrek yetmezliğinde dikkatli kullanılmalıdır. Şiddetli böbrek yetmezliğinde başlangıç ve idame dozlarının azaltılması gerekebilir. GFR 35 orta-şiddetli böbrek bozukluğu kategorisindedir; klinik yanıt ve tolerabiliteye göre doz titre edilmelidir.

**Sistem Yanıtı:**
```
Dikkatle kullanılır, doz ayarı gerekli olabilir.

İncelenen LAMICTAL DC KÜB belgesine göre, böbrek yetmezliği olan hastalara lamotrijin verilirken dikkatli olunmalıdır. Son aşamada böbrek yetmezliği olan hastalar için, LAMICTAL başlangıç dozları, hastaların eş zamanlı kullandığı ilaçlara dayandırılmalıdır; azaltılmış idame dozları, belirgin böbrek fonksiyon bozukluğu olan hastalar için etkili olabilir [LAMICTAL DC 100 mg | Madde 4.2 Böbrek Yetmezliği].

Sizin hastanızın GFR değeri 35 mL/dak/1.73m² (Evre 3b, GFR 30-44) olup, bu belirgin böbrek fonksiyon bozukluğu kategorisine girmektedir. KÜB belgesinde, bu düzeydeki böbrek yetmezliğinde azaltılmış idame dozlarının etkili olabileceği belirtilmektedir. Ancak başlangıç dozu, hastanın halen kullandığı antiepileptik ve bipolar bozukluk ilaçları...
```

**Analiz:** DÜŞÜK SKOR. GFR 35 için spesifik doz önerisi yok.

---

## Soru 9 — v3_q09 [kontrendikasyon]

**Soru:** Astım hastasına ARLEC başlanabilir mi?
**F:** 0.8333 | **CR:** NaN | **Contexts:** 5 | **Yanıt:** 1183 karakter

**Ground Truth:**
> Karvedilol (ARLEC) reaktif hava yolu hastalığı ve bronkospazm geçmişi olan hastalarda kontrendikedir. Astım, karvedilol için mutlak kontrendikasyondur; kardiyoselektif olmayan beta-bloker özelliği nedeniyle bronkospazm şiddetlenebilir.

**Sistem Yanıtı:**
```
**Hayır, ARLEC (karvedilol) bu hastaya kontrendikedir.**

KÜB Madde 4.3'te açık olarak belirtildiği üzere, karvedilol "bronkospazm ya da astım öyküsü olan hastalar"da kullanılmamalıdır. [ARLEC® 6,25 mg tablet | Madde 4.3 | Kontrendikasyonlar] Bu hastanın astım tanısı vardır, bu nedenle karvedilol başlanması KÜB'de listelenen kontrendikasyonu ihlal eder.

KÜB Madde 4.4'te astım veya bronkospazm eğilimi olan hastalarda karvedilolün kullanılması hakkında ek uyarı yer almaktadır: "Bronkospazm gözlenen kronik obstrüktif akciğer hastalığı (KOAH) bulunan ve oral ya da inhalasyon yolu ile ilaç almayan hastalarda karvedilol ancak potansiyel yarar potansiyel riskten daha fazlaysa kullanılmalıdır. Bronkospazm eğilimi olan hastalarda, solunum yolundaki olası bir direnç artışı nedeniyle solunum distres...
```

**Analiz:** Doğru kontrendikasyon kararı.

---

## Soru 10 — v3_q10 [cyp450_etkilesim]

**Soru:** PLAVIX kullanan hastaya CANDİDİN başlanırsa antiplatelet etki nasıl değişir?
**F:** NaN | **CR:** 0.7500 | **Contexts:** 9 | **Yanıt:** 2083 karakter

**Ground Truth:**
> Flukonazol (CANDİDİN) güçlü CYP2C19 inhibitörüdür. Klopidogrel (PLAVIX) CYP2C19 üzerinden aktif metabolite dönüştürülür. Flukonazol bu dönüşümü inhibe ederek klopidogrelin antiplatelet etkisini önemli ölçüde azaltır. Stent olan hastalarda bu kombinasyondan kaçınılmalıdır.

**Sistem Yanıtı:**
```
# YANIT

CANDİDİN kullanırken PLAVIX'in antiplatelet etkisinde önemli bir değişim beklenmemektedir, ancak kombinasyon önemli güvenlik endişeleri taşımaktadır.

CANDİDİN (flukonazol) ve PLAVIX (klopidogrel) arasında direkt bir farmakodinamik etkileşim nedeniyle antiplatelet etkinliğin azalması konusunda KÜB belgelerinde spesifik bilgi yer almamaktadır. Enzim profili analizi açısından, her iki ilaç CYP3A4 substratı olarak metabolize olmakta ve bu nedenle kan düzeyleri düzeyinde bir rekabet potansiyeli bulunmaktadır; ancak bu mekanizma klopidogrel'in antiplatelet aktivitesini doğrudan zayıflatacak bir etkiye yol açıyor olarak KÜB metninde bildirilmemiştir.

Bununla birlikte, bu kombinasyonun kullanımı önemli uyarılar gerektirmektedir. En kritik nokta, **CANDİDİN 150 mg kapsülün 4.4 maddesinde...
```

**Analiz:** KRİTİK HATA: GT 'etki azalır' derken sistem 'değişim yok' diyor. Stent hastası için tehlikeli.

---

## Soru 11 — v3_q11 [laktasyon]

**Soru:** Emziren annede LUSTRAL kullanımı güvenli midir?
**F:** NaN | **CR:** 0.3333 | **Contexts:** 6 | **Yanıt:** 1282 karakter

**Ground Truth:**
> Sertralin (LUSTRAL) anne sütüne geçer. Emzirme döneminde kullanımı önerilmez; ancak klinik gereklilik varsa bebek yakından izlenmelidir. KÜB belgesinde emzirme döneminde kullanılmaması tavsiye edilmektedir.

**Sistem Yanıtı:**
```
Emziren annede LUSTRAL (sertralin) kullanımı hakkında KÜB belgelerinde spesifik bilgi yer almamaktadır.

İncelenen KÜB metninin 4.6 maddesinde (Gebelik ve Laktasyon) gebelik dönemindeki kullanım, yenidoğan geri çekilme reaksiyonları ve hamilelik sırasındaki postpartum hemoraji riski detaylı olarak açıklanmıştır. Ancak laktasyon (emzirme) dönemi hakkında "İncelenen KÜB belgelerinde bu konuda spesifik bilgi yer almamaktadır." [LUSTRAL® 50 mg | Madde 4.6 | Tam metin gözden geçirildi].

Hasta 30 yaşında kadın, postpartum dönemde depresyon tanısı almış ve aktif olarak emzirmektedir. KÜB metninde emziren annelerdeki sertralin kullanımının güvenliği, bebeğe geçiş oranları, besin yoluyla alınan dozu veya ilişkili riskleri hakkında bilgi bulunmamaktadır. Böbrek fonksiyonu bilinmediğinden de doza ba...
```

**Analiz:** Corpus boşluğu — LUSTRAL laktasyon bölümü parse edilmemiş.

---

## Soru 12 — v3_q12 [etkilesim_ciddi]

**Soru:** NORODOL ile CORDARONE birlikte kullanılabilir mi?
**F:** NaN | **CR:** 1.0000 | **Contexts:** 9 | **Yanıt:** 2312 karakter

**Ground Truth:**
> Haloperidol (NORODOL) ve amiodaron (CORDARONE) her ikisi de QT intervalini uzatır. Bu kombinasyon Torsades de Pointes ve ventriküler aritmiler açısından yüksek risk taşır. Birlikte kullanımdan kaçınılmalı; zorunluysa EKG monitorizasyonu yapılmalıdır.

**Sistem Yanıtı:**
```
**HAYIR, bu kombinasyon dikkatle kullanılır ve ciddi kardiyak riskleri içerir.**

NORODOL® (haloperidol) ile CORDARONE® (amiodaron) birlikte kullanımı önemli etkileşim ve yan etki riskleri taşır. İncelenen KÜB belgelerine göre her iki ilaç da QT aralığında uzamaya neden olabilir ve bu kombinasyon Torsades de pointes (hayat tehdit eden ventriküler aritmisi) riskini ciddi şekilde artırır.

NORODOL® KÜB belgesinde belirtildiği üzere, "Sınıf III antiaritmikler (amiodaron, sotalol ve dofetilid gibi)" ilaçlarla birlikte kullanımı önerilmez, çünkü bu kombinasyon "QT aralığında uzama nedeniyle Torsades de pointes riski artar" [NORODOL® | Madde 4.5 | Diğer Tıbbi Ürünlerle Etkileşimler]. NORODOL® KÜB'de açıkça "Diğer QT aralığını artıran ilaçlar haloperidol ile birlikte kullanıldığında Torsades de p...
```

**Analiz:** CR=1.00. QT uzaması ve EKG izlemi doğru.

---

## Soru 13 — v3_q13 [doz_geriyatrik]

**Soru:** 85 yaşındaki hastada XANAX başlangıç dozu ne olmalı?
**F:** 1.0000 | **CR:** 0.6667 | **Contexts:** 4 | **Yanıt:** 1830 karakter

**Ground Truth:**
> Alprazolam (XANAX) geriyatrik hastalarda en düşük etkin dozda başlanmalıdır. KÜB belgesine göre yaşlı hastalarda başlangıç dozu 0.25 mg günde 2-3 kez olarak önerilir. Sedatif etkiye karşı duyarlılık artar, düşme ve konfüzyon riski gözetilmelidir.

**Sistem Yanıtı:**
```
Dikkatle kullanılır, doz ayarı gerekir.

85 yaşındaki bu hasta geriyatrik popülasyona dahildir ve XANAX kullanımı için özel doz ayarlaması gerekmektedir. KÜB'de açıkça belirtildiği üzere, yaşlılarda ya da debil hastalarda aşırı sedasyon ya da ataksi gelişmesini önlemek amacıyla, en düşük etkili dozu kullanma genel ilkesine uyulmalıdır [XANAX® 0.5 mg tablet | Madde 4.2 | Geriyatrik Popülasyon].

Geriyatrik hastalar için önerilen başlangıç dozu günde 2-3 defa 0.25 mg'dır. Normal anksiyete hastalarında günde 3 defa 0.25-0.5 mg önerilirken, yaşlı ve debilizan hastalık varlığında daha düşük olan 0.25 mg dozundan başlanmalı ve gerekirse ve tolere edilirse doz tedricen arttırılmalıdır. Bu hastanın maksimum doz sınırı bölünmüş dozlar halinde günde 0.5-0.75 mg'dır [XANAX® 0.5 mg tablet | Madde 4.2 ...
```

**Analiz:** F=1.00. Geriyatrik doz bilgisi mevcut.

---

## Soru 14 — v3_q14 [kontrendikasyon]

**Soru:** Aktif mide ülseri olan hastada BRUFEN kullanılabilir mi?
**F:** 1.0000 | **CR:** 0.5000 | **Contexts:** 5 | **Yanıt:** 959 karakter

**Ground Truth:**
> İbuprofen (BRUFEN) aktif peptik ülser hastalığında kontrendikedir. KÜB belgesinde aktif gastrointestinal ülser veya kanama, BRUFEN için mutlak kontrendikasyon olarak belirtilmiştir.

**Sistem Yanıtı:**
```
Hayır, BRUFEN bu hastada kontrendikedir.

KÜB belgesinin 4.3 Kontrendikasyonlar bölümüne göre, BRUFEN aktif mide veya bağırsak ülseri/kanaması olan hastalarda kontrendikedir [BRUFEN 400 mg | Madde 4.3 | Sayfa 2]. Bu hastada aktif mide ülseri bulunmaktadır, dolayısıyla ibuprofen içeren BRUFEN ürünü kullanımı uygun değildir.

Ek olarak, KÜB belgesinin 4.4 bölümünde NSAİİ'lerin gastrointestinal risklerine ilişkin detaylı uyarılar yer almaktadır. NSAİİ'ler kanama, ülserasyon ve mide veya bağırsak perforasyonu gibi ciddi Gİ advers etkilere risk artışına yol açmaktadırlar ve bu advers olaylar herhangi bir zamanda ortaya çıkabilir [BRUFEN 400 mg | Madde 4.4 | Sayfa 3].

Bu hastaya BRUFEN yerine, mide ülseri varlığında daha güvenli olabilecek alternatif ağrı kesici/anti-enflamatuar ajanların değer...
```

**Analiz:** F=1.00. Kontrendikasyon net.

---

## Soru 15 — v3_q15 [etkilesim_doz]

**Soru:** ALDACTONE kullanan hastada PLASORİN dozu neden değişebilir?
**F:** 1.0000 | **CR:** 1.0000 | **Contexts:** 5 | **Yanıt:** 1754 karakter

**Ground Truth:**
> Spironolakton (ALDACTONE) varfarin (PLASORİN) metabolizmasını etkileyebilir; birlikte kullanımda INR değerinin değişebileceği bildirilmiştir. Varfarin dozu ayarlaması gerekebilir; INR yakın izlenmelidir.

**Sistem Yanıtı:**
```
Evet, ALDACTONE kullanan bu hastada PLASORİN dozu değişebilir ve dikkatli izleme gerekir.

PLASORİN (varfarin) ve ALDACTONE (spironolakton) arasında önemli bir etkileşim mekanizması bulunmaktadır. Otomatik CYP450 enzim analizi bulgularına göre, her iki ilaç CYP2C9 substratidir ve bu enzim için rekabet oluşturmaktadır. Bu rekabet sonucu PLASORİN'in kan düzeyleri değişebilir ve INR değeri etkilenebilir.

Hasta profiliniz bu etkileşimi daha riskli hale getirmektedir. Hastanız 67 yaşında olup kalp yetmezliği tanısı bulunmaktadır. KÜB belgesine göre, "Hemorajik riski artmış hastalarda (örneğin, yaşlı ya da yeti yitimi olan hastalar, karaciğer yetmezliği ya da konjestif kalp yetmezliği olan hastalar, varfarine karşı duyarlılığı arttırdığı bilinen ilaçları kullanan hastalar...) başlangıç dozu doz...
```

**Analiz:** MÜKEMMEL — F=1.00, CR=1.00. INR etkileşimi tam.

---

## Soru 16 — v3_q16 [doz_bobrek]

**Soru:** GFR 40 olan hastada COLCHICUM DISPERT dozu nasıl ayarlanmalı?
**F:** NaN | **CR:** 0.3333 | **Contexts:** 3 | **Yanıt:** 1277 karakter

**Ground Truth:**
> Kolşisin (COLCHICUM DISPERT) böbrek yetmezliğinde dikkatli kullanılmalıdır. Orta dereceli böbrek yetmezliğinde (GFR 30-60) doz azaltılmalı ve tedavi süresi kısaltılmalıdır. Nöromiyopati ve miyelosüpresyon riski artar.

**Sistem Yanıtı:**
```
Dikkatle kullanılır, doz ayarı gerekir.

Bu hastada COLCHICUM DISPERT® kullanımı mümkündür, ancak böbrek fonksiyonunun bozulması nedeniyle dozun dikkatle ayarlanması gereklidir. Hastanın GFR değeri 40 mL/dak/1.73m² olup, kreatinin klerensi 10 mL/dak'tan yüksektir. KÜB'de belirtilen kontrendikasyon "ciddi renal rahatsızlıkta (kreatinin klerensi 10 mL/dak altında olanlar)" [COLCHICUM DISPERT® 0,5 mg | Madde 4.3 | Kontrendikasyonlar] olarak tanımlandığından, bu hasta tam kontrendikasyonda değildir.

Ancak KÜB belgesinin "Böbrek / Karaciğer Yetmezliği" bölümünün başlangıcında metin kesilebilmiş olması nedeniyle [COLCHICUM DISPERT® 0,5 mg | Madde 4.2 | Pozoloji ve Uygulama Şekli — Böbrek / Karaciğer Yetmezliği], incelenen KÜB belgelerinde böbrek yetmezliğinde spesifik doz ayarlama talimatlarını...
```

**Analiz:** Sadece 3 context. Kolşisin böbrek dozu detayı yetersiz.

---

## Soru 17 — v3_q17 [cyp450_etkilesim]

**Soru:** CYMBALTA kullanan hastada ALTİZEM SR eklenirse ne olur?
**F:** NaN | **CR:** 0.6667 | **Contexts:** 9 | **Yanıt:** 2037 karakter

**Ground Truth:**
> Duloksetin (CYMBALTA) CYP1A2 ve CYP2D6 substratıdır. Diltiazem (ALTİZEM SR) orta düzey CYP3A4 inhibitörüdür. Duloksetin metabolizması üzerinde belirgin etkisi sınırlıdır ancak birlikte kullanımda duloksetin plazma düzeyi izlenmeli ve yan etkiler takip edilmelidir.

**Sistem Yanıtı:**
```
ALTİZEM SR (diltiazem) CYMBALTA (duloksetin) ile birlikte kullanırken dikkat gerektirir; bu kombinasyon KÜB belgelerinde spesifik kontrendikasyon olarak yer almamakla birlikte, önemli klinik hususlar mevcuttur.

**Kardiyak ve hemodynamik etkileşim:** ALTİZEM SR, AV nodal iletiyi ve AV düğümde refrakter periyodu uzatır [ALTİZEM SR | Madde 4.4]. CYMBALTA ise bazı hastalarda kan basıncında artış ve klinik olarak anlamlı hipertansiyonla ilişkilidir; bu duloksetinin noradrenerjik etkisine bağlıdır [CYMBALTA | Madde 4.4]. Hasta zaten hipertansiyon tanısı taşıdığından, bu kombinasyon kan basıncı kontrol etmeyi zorlaştırabilir.

**Kan basıncı izleminin kritik önemi:** CYMBALTA'nın Madde 4.4'ünde "Kontrol edilemeyen hipertansiyonu olan hastalarda duloksetin başlatılmamalı" ifadesi yer almaktadır [C...
```

**Analiz:** CR=0.67. Doğru substrat/inhibitör bilgisi.

---

## Soru 18 — v3_q18 [kontrendikasyon]

**Soru:** Gebelikte COZAAR kullanılabilir mi?
**F:** NaN | **CR:** 1.0000 | **Contexts:** 6 | **Yanıt:** 1497 karakter

**Ground Truth:**
> Losartan (COZAAR) gebelikte kontrendikedir. Gebelik kategorisi D olup özellikle 2. ve 3. trimesterde fetüste böbrek hasarı, oligohidramniyos ve ölüm riskiyle ilişkilidir. KÜB belgesinde gebelik mutlak kontrendikasyon olarak belirtilmiştir.

**Sistem Yanıtı:**
```
Hayır, COZAAR gebelikte kontrendikedir ve kullanılmamalıdır.

COZAAR (losartan) gebelik kategorisi D'dir ve KÜB belgesinde açıkça "COZAAR gebelik döneminde kullanılmamalıdır" ifadesi yer almaktadır [COZAAR 50 mg | Madde 4.6 | Gebelik kategorisi ve Gebelik dönemi]. Ayrıca Madde 4.3'te "gebelikte" COZAAR'ın mutlak kontrendikasyon olduğu belirtilmiştir [COZAAR 50 mg | Madde 4.3 | Kontrendikasyonlar].

Bu hasta gebelik durumunda olduğu için mevcut COZAAR 50 mg tedavisi derhal bırakılmalı ve uygun bir alternatif antihipertansif tedaviye geçilmelidir. KÜB belgesinde "Gebelik saptandığı anda losartan tedavisi derhal bırakılmalı ve uygun ise alternatif tedaviye başlanmalıdır" açıkça belirtilmiştir [COZAAR 50 mg | Madde 4.6 | Gebelik dönemi].

Losartan, özellikle gebeliğin 2. ve 3. trimesterlerinde...
```

**Analiz:** CR=1.00. Gebelik kategorisi D, fetal risk doğru.

---

## Soru 19 — v3_q19 [etkilesim_farmakodinamik]

**Soru:** CLEXANE kullanan hastaya PLAVIX eklenmesi kanama riskini nasıl etkiler?
**F:** NaN | **CR:** 1.0000 | **Contexts:** 8 | **Yanıt:** 2275 karakter

**Ground Truth:**
> Enoksaparin (CLEXANE) ve klopidogrel (PLAVIX) kombinasyonu kanama riskini artırır. Her ikisi de antitrombotik etki gösterir; birlikte kullanımda majör kanama ve gastrointestinal kanama riski yükselir. Klinik fayda-risk dengesi değerlendirilerek kullanılmalı, kanama belirtileri yakın izlenmelidir.

**Sistem Yanıtı:**
```
CLEXANE ile birlikte PLAVIX eklenmesi kanama riskini **önemli ölçüde artırır** ve dikkatli klinik izlem gerektirir.

KÜB belgelerine göre, PLAVIX (klopidogrel) birlikte kullanıldığında kanama riski artması nedeniyle özel uyarılar söz konusudur. PLAVIX KÜB Madde 4.4'te belirtildiği üzere, "diğer antiagregan ajanlarla olduğu gibi, klopidogrel de... heparin... dahil kanama riski ile ilişkilendirilebilecek diğer ilaçları birlikte alan hastalarda dikkatle kullanılmalıdır" [PLAVIX® 75 mg | Madde 4.4]. Ayrıca KÜB'de "kanama şiddetini artırabileceğinden, klopidogrelin oral antikoagülanlar ile birlikte uygulanması önerilmemektedir" ifadesi yer alır; bu uyarı antikoagülan ve antiagregan etkili ilaçların kombinasyonundaki kanama riskini vurgular [PLAVIX® 75 mg | Madde 4.4].

CLEXANE (enoksaparin) KÜB...
```

**Analiz:** CR=1.00. Kanama riski ve izlem doğru.

---

## Soru 20 — v3_q20 [doz_karaciger]

**Soru:** Child-Pugh A karaciğer yetmezliği olan hastada LİPİTOR dozu nasıl ayarlanmalı?
**F:** NaN | **CR:** NaN | **Contexts:** 8 | **Yanıt:** 2227 karakter

**Ground Truth:**
> Atorvastatin (LİPİTOR) aktif karaciğer hastalığında kontrendikedir. Child-Pugh A hastalarda dikkatli kullanım önerilir; karaciğer fonksiyon testleri yakın takip edilmelidir. ALT ve AST normalin 3 katını aşarsa tedavi kesilmelidir.

**Sistem Yanıtı:**
```
Child-Pugh A karaciğer yetmezliği olan bu hastada LİPİTOR kullanımı mümkündür ancak dikkatli takip gereklidir; doz ayarlamasına gerek yoktur fakat karaciğer fonksiyon testleri düzenli olarak yapılmalıdır.

KÜB belgesinde karaciğer yetmezliği için özel bir doz azaltması belirtilmemektedir. Bölüm 4.2'de primer hiperkolesterolemi ve kombine hiperlipidemi durumlarında "Bu hastaların çoğunda günde bir defa 10 mg atorvastatin tedavisi ile kontrol sağlanabilir" ve dozlar başlangıç LDL-K değerleri, tedavi amacı ve hastanın tedaviye yanıtına göre bireyselleştirilmeli olarak tanımlanmıştır [LİPİTOR 20 mg | Madde 4.2 | Primer Hiperkolesterolemi ve Kombine Hiperlipidemi]. Böbrek yetmezliği bölümünde de benzer şekilde doza ilişkin belirli bir azaltma önerilmemektedir [LİPİTOR 20 mg | Madde 4.2 | Böbrek...
```

**Analiz:** İkisi de NaN. Yanıt muhtemelen doğru yönde.

---

## Soru 21 — v3_q21 [etkilesim_ciddi]

**Soru:** PROPYCIL kullanan hastaya AMİODARON (SANORONE) eklenirse ne olur?
**F:** NaN | **CR:** 1.0000 | **Contexts:** 8 | **Yanıt:** 1939 karakter

**Ground Truth:**
> Propiltiourasil (PROPYCIL) ve amiodaron (SANORONE) kombinasyonunda dikkatli olunmalıdır. Amiodaron yüksek iyot içerir ve tiroid fonksiyonunu bozabilir; propiltiourasil ile birlikte hem hipotiroidizm hem hipertiroidizm riski değişebilir. Tiroid fonksiyon testleri yakın izlenmelidir.

**Sistem Yanıtı:**
```
**AÇIK KARAR:** Bu kombinasyon kontrendikedir ve kesinlikle kullanılmamalıdır.

**Kontrendikasyon Nedenleri:**

SANORONE (amiodaron) KÜB'de "Tiroid hastalıklarında" kullanımı kontrendike olarak belirtilmiştir [SANORONE 200 mg | Madde 4.3 | Kontrendikasyonlar]. Hastanın hipertiroidizm tanısı bulunmaktadır ve halen PROPYCIL 50 mg ile tedavi görmektedir. Hipertiroidizm bir tiroid hastalığıdır; bu nedenle amiodaron kontraendikedir.

Ek olarak, antiaritmiklerin kombine kullanımı kritik riskler taşır. SANORONE KÜB'de açık şekilde belirtilmiştir: "Farklı sınıflardan antiaritmiklerin kombinasyonu faydalı bir terapötik etki sağlayabilir, ancak, genellikle ÇOK DİKKAT gerektirir; bu durumda yakın klinik izlem ve EKG monitorizasyonu şarttır" [SANORONE 200 mg | Madde 4.5 | Diğer Tıbbi Ürünlerle Etkileş...
```

**Analiz:** GT 'dikkatli kullan' derken sistem 'kontrendike'. Aşırı muhafazakâr.

---

## Soru 22 — v3_q22 [doz_bobrek]

**Soru:** GFR 25 olan hastada JANUVIA'ya alternatif olarak AMARYL kullanılabilir mi?
**F:** NaN | **CR:** 0.0000 | **Contexts:** 5 | **Yanıt:** 1039 karakter

**Ground Truth:**
> Glimepirid (AMARYL) böbrek yetmezliğinde hipoglisemi riski nedeniyle dikkatli kullanılmalıdır. Şiddetli böbrek yetmezliğinde (GFR <30) kullanımından kaçınılması önerilir çünkü aktif metabolitler birikebilir. GFR 25 için AMARYL kontrendike değil ama yüksek hipoglisemi riski taşır.

**Sistem Yanıtı:**
```
Hayır, AMARYL bu hastada kontrendikedir.

GFR=25 mL/dak/1.73m² ile seyreden Evre 4 böbrek yetmezliği nedeniyle AMARYL kullanımı uygun değildir. KÜB belgelerine göre, ciddi böbrek fonksiyon bozukluğu olan hastalarda AMARYL kontrendikedir ve insüline geçilmesi gereklidir. [AMARYL 2 mg tablet | Madde 4.3 | Kontrendikasyonlar]

Hastanın böbrek fonksiyonlarının bozuk olması durumunda, AMARYL'in kan şekerini düşürücü etkisine daha hassas olacağı ve hipoglisemi riskinin arttığı belirtilmektedir. [AMARYL 2 mg tablet | Madde 4.2 | Böbrek/Karaciğer Yetmezliği] Özellikle 70 yaşındaki bu hastada, hipoglisemi semptomları (baş ağrısı, konsantrasyon bozukluğu, çaresizlik, deliryum gibi) yaşlı hastalarda tanınması daha zor olabilir ve ciddi komplikasyonlara yol açabilir.

AMARYL yerine böbrek yetmezliğind...
```

**Analiz:** CR=0.00. AMARYL/glimepirid GFR<30 uyarısı corpus'ta yok.

---

## Soru 23 — v3_q23 [kontrendikasyon]

**Soru:** Miyastenia gravis hastasına AVELOX başlanabilir mi?
**F:** 0.0000 | **CR:** 0.0000 | **Contexts:** 1 | **Yanıt:** 723 karakter

**Ground Truth:**
> Moksifloksasin (AVELOX) miyastenia gravis hastalarında kontrendikedir veya dikkatle kullanılmalıdır. Florokinolonların nöromüsküler blokajı artırabileceği ve miyasteniya semptomlarını şiddetlendirebileceği bilinmektedir. KÜB belgesinde bu uyarı mevcuttur.

**Sistem Yanıtı:**
```
[BİLGİ YOK: Bu konu incelenen KÜB belgelerinde yer almamaktadır.]

İncelenen KÜB belgelerinde AVELOX ile miyastenia gravis arasında spesifik bir kontrendikasyon veya etkileşim bilgisi yer almamaktadır. Ayrıca Graf veritabanı bulgularında da miyastenia gravis ile ilgili bilgi mevcut değildir. Bu nedenle KÜB-tabanlı bir değerlendirme yapılamamaktadır.

Miyastenia gravis gibi nöromüsküler bozukluk ve kinolonlar arasındaki olası ilişkiler hakkında detaylı bilgi için, incelenen belgeler dışında ek kaynaklar ve terapötik kılavuzların danışılması gerekebilir. Hasta profili ve klinik durum göz önünde bulundurularak (55 yaşında kadın, pnömoni tanısı, böbrek fonksiyonu bilinmiyor), klinik karar sağlık profesyoneline aittir.
```

**Analiz:** BOZUK — F=0.00, CR=0.00. Corpus tam boşluk. AVELOX miyastenia bölümü eksik.

---

## Soru 24 — v3_q24 [etkilesim_doz]

**Soru:** TEGRETOL kullanan hastada LAMICTAL DC dozu neden artırılmalıdır?
**F:** NaN | **CR:** 1.0000 | **Contexts:** 15 | **Yanıt:** 2028 karakter

**Ground Truth:**
> Karbamazepin (TEGRETOL) güçlü CYP3A4 indükleyicisidir ve aynı zamanda lamotrijin glukuronidasyonunu hızlandırır. Lamotrijin (LAMICTAL DC) karbamazepin ile birlikte kullanıldığında plazma yarılanma ömrü yaklaşık yarıya iner. Bu nedenle lamotrijin dozu karbamazepin alan hastalarda belirgin şekilde artırılmalıdır.

**Sistem Yanıtı:**
```
TEGRETOL (karbamazepin) kullanan bir hastaya LAMICTAL DC başlanırken doz artırılması gerekebilir, çünkü karbamazepin lamotrijinin metabolizmasını önemli ölçüde hızlandırmaktadır.

Karbamazepin, lamotrijinin metabolizmasından sorumlu olan UDP glukuronil transferaz (UGT) enzimlerini indüklemektedir. [LAMICTAL DC 100 mg çözünür / çiğneme tableti | Madde 4.5] LAMICTAL DC KÜB belgesinde, lamotrijin konsantrasyonunu düşüren ilaçlar tablosunda karbamazepin açıkça listelenmiştir. Bu indüksiyon, lamotrijinin klerensini artırarak plazmadaki konsantrasyonlarını düşürmektedir.

Sonuç olarak, terapötik etkiyi sağlamak için lamotrijin idame dozunun yükseltilmesi gerekebilmektedir. TEGRETOL gibi karbamazepin indükleyicileriyle birlikte kullanıldığında, lamotrijin monoterapisi için önerilen standart doz ş...
```

**Analiz:** CR=1.00. İndüksiyon mekanizması doğru (15 context).

---

## Soru 25 — v3_q25 [yan_etki]

**Soru:** JARDIANCE başlanan hastada üriner enfeksiyon riski hakkında neler söylenebilir?
**F:** 0.7500 | **CR:** 1.0000 | **Contexts:** 4 | **Yanıt:** 938 karakter

**Ground Truth:**
> Empagliflozin (JARDIANCE) üriner glukoz atılımını artırdığından genitoüriner enfeksiyon riskini yükseltir. KÜB belgesinde tekrarlayan üriner enfeksiyon öyküsü olan hastalarda dikkatli kullanım önerilmektedir. Üriner enfeksiyon belirtileri yakın izlenmelidir.

**Sistem Yanıtı:**
```
[BİLGİ YOK: Bu konu incelenen KÜB belgelerinde yer almamaktadır.]

İncelenen JARDIANCE 10 mg film kaplı tablet KÜB belgesinin Madde 4.4 (Özel Kullanım Uyarıları ve Önlemleri) ve Madde 4.5 (Diğer Tıbbi Ürünlerle Etkileşimler) bölümlerinde üriner enfeksiyon riski hakkında spesifik bilgi yer almamaktadır. KÜB metninde ketoasidoz, diüretiklerin dehidratasyon riski, hipoglisemi riski ve diğer etkileşimler dokumente edilmiş olsa da, üriner enfeksiyon veya idrar yolu enfeksiyonlarına ilişkin uyarı bulunmamaktadır.

Hasta profilinin değerlendirilmesinde, 58 yaşındaki kadın hastanın Evre 2 böbrek hastalığı (GFR=65.0) ve HbA1c değeri 8.1 ile kontrol altında olmayan tip-2 diyabeti bulunduğu dikkate alınmıştır; ancak sağlanan KÜB belgelerine göre bu konuda herhangi bir kontrendikasyon veya özel uyarı ...
```

**Analiz:** F=0.75, CR=1.00. BİLGİ YOK yanıtı ama context mevcut — anomali.

---

## Soru 26 — v3_q26 [kontrendikasyon]

**Soru:** Hiperpotasemi olan hastada CO-DIOVAN kullanılabilir mi?
**F:** 0.6000 | **CR:** 1.0000 | **Contexts:** 4 | **Yanıt:** 1139 karakter

**Ground Truth:**
> Valsartan/hidroklorotiyazid (CO-DIOVAN) kombinasyonunda valsartan bileşeni potasyum düzeyini artırabilir. Hiperpotasemisi olan hastalarda ARB içeren ilaçlar dikkatle kullanılmalıdır. Serum potasyum izlemi zorunludur; ciddi hiperpotasemi durumunda kontrendikedir.

**Sistem Yanıtı:**
```
Hayır, hiperpotasemisi olan bu hastada CO-DIOVAN kullanımı kontrendikedir.

KÜB belgesine göre, CO-DIOVAN'ın kontrendikasyonları arasında "refrakter hipokalemi, hiponatremi, hiperkalsemi ve semptomatik hiperürisemi" yer almaktadır [CO-DIOVAN® 160 mg/12,5 mg | Madde 4.3 | Kontrendikasyonlar]. Mevcut hastada serum potasyum değeri 6,1 mEq/L olup kritik düzey hiperpotasemisi bulunmaktadır.

Ek olarak, KÜB belgesinin 4.4. Maddesinde valsartan bileşeni hakkında açık uyarı verilmektedir: "Potasyum takviyesi, potasyum tutucu diüretikler, potasyum içeren yapay tuzlar veya potasyum düzeylerini artıran heparin vs. gibi diğer ilaçlar CO-DIOVAN ile birlikte tavsiye edilmemektedir. Uygun şekilde potasyum takibi yapılmalıdır" [CO-DIOVAN® 160 mg/12,5 mg | Madde 4.4 | Serum elektrolit değişiklikleri]. Bu i...
```

**Analiz:** F=0.60. K=6.1 için kontrendike kararı klinik doğru.

---

## Soru 27 — v3_q27 [doz_geriyatrik]

**Soru:** 80 yaşındaki hastada RENITEC başlangıç dozu ne olmalı?
**F:** NaN | **CR:** 1.0000 | **Contexts:** 4 | **Yanıt:** 1080 karakter

**Ground Truth:**
> Enalapril (RENITEC) yaşlı hastalarda böbrek fonksiyonu azalmış olabileceğinden düşük başlangıç dozuyla başlanmalıdır. Geriyatrik hastalarda 2.5 mg başlangıç dozu önerilir, böbrek fonksiyonu ve kan basıncı yanıtına göre titre edilir.

**Sistem Yanıtı:**
```
Dikkatle kullanılır, doz ayarı gerekir.

Bu 80 yaşındaki kadın hasta için RENITEC başlangıç dozu belirlenirken, geriyatrik popülasyona özgü kurallara uyulması gerekir. KÜB'de geriyatrik hasta grubu için "Doz, yaşlı hastanın böbrek fonksiyonuna uygun olmalıdır" belirtilmektedir [RENITEC 5 mg tablet | Madde 4.2 | Geriyatrik Popülasyon].

Hastanın böbrek fonksiyonu GFR=55.0 mL/dak/1.73m² (Evre 3a) olan hafif-orta düzeyde böbrek fonksiyon bozukluğu göstermektedir. İncelenen KÜB belgesinde, çocuk hastalarda GFR <30 ml/min/1.73 m2 durumunda RENITEC önerilmediği belirtilmekle birlikte [RENITEC 5 mg tablet | Madde 4.2 | Pediyatrik Popülasyon], bu hasta için ilgili KÜB belgelerinde evre 3a böbrek fonksiyon bozukluğunda kullanılacak belirli başlangıç dozu açıkça yazılmamaktadır.

İncelenen KÜB belge...
```

**Analiz:** CR=1.00. 2.5 mg başlangıç dozu genel yön doğru.

---

## Soru 28 — v3_q28 [etkilesim_ciddi]

**Soru:** İMURAN kullanan hastada ÜRİKOLİZ başlanırsa ne olur?
**F:** NaN | **CR:** 0.6667 | **Contexts:** 8 | **Yanıt:** 2060 karakter

**Ground Truth:**
> Allopurinol (ÜRİKOLİZ) azatioprinin (İMURAN) metabolizmasını inhibe eder; ksantin oksidaz inhibisyonu nedeniyle azatioprin toksisite riski dramatik biçimde artar. Birlikte kullanımda azatioprin dozu dörtte birine indirilmelidir veya bu kombinasyondan kaçınılmalıdır. KÜB belgesinde bu etkileşim kontraendikasyon olarak belirtilmiştir.

**Sistem Yanıtı:**
```
**ÖNEMLİ: İMURAN ve ÜRİKOLİZ birlikte kullanılmamalıdır — doz ayarı zorunludur.**

İMURAN (azatioprin) kullanan hastaya ÜRİKOLİZ (allopurinol) başlanması ciddi bir ilaç etkileşimidir ve bu kombinasyon kontrollü bir biçimde uygulanmalıdır. Şu nedenlerden dikkat edilmelidir:

**Kritik Etkileşim Mekanizması:**

Azatioprin, ksantin oksidaz enzimi tarafından metabolize edilerek inaktif hale getirilir. ÜRİKOLİZ (allopurinol), ksantin oksidaz inhibitörü olduğundan, azatioprinin metabolizasyonunu engelleyerek serum konsantrasyonlarını toksik düzeylere çıkarabilir. [ÜRİKOLİZ® 300 mg tablet | KÜB Madde 4.5 | Etkileşimler] Bu durumun sonucu yaşamı tehdit eden pansitopeni ve miyelosupresyon gelişebilir. [ÜRİKOLİZ® 300 mg tablet | KÜB Madde 4.5 | Etkileşimler]

**Doz Ayarı Gereklidir:**

ÜRİKOLİZ ve İM...
```

**Analiz:** CR=0.67. Doz azaltım (1/4) ve mekanizma doğru.

---

## Soru 29 — v3_q29 [kontrendikasyon]

**Soru:** Feokromasitoma hastasına NORODOL başlanabilir mi?
**F:** 0.8571 | **CR:** 0.6667 | **Contexts:** 4 | **Yanıt:** 1451 karakter

**Ground Truth:**
> Haloperidol (NORODOL) feokromasitomada kontrendikedir. Dopamin reseptör blokajı nedeniyle hipertansif kriz tetiklenebilir. KÜB belgesinde feokromasitoma kontrendikasyon olarak yer almaktadır.

**Sistem Yanıtı:**
```
Hayır, feokromasitoma hastasına NORODOL başlanması kontrendikedir.

NORODOL® (haloperidol) KÜB belgesinin 4.3. Kontrendikasyonlar bölümünde "bazal gangliyon lezyonlarında kontrendikedir" ifadesi yer almaktadır [NORODOL® 5 mg tablet | Madde 4.3]. Feokromasitoma, endokrin sistemin bir tümörü olup, hastalık sürecinde katekolomin salınımına bağlı olarak ciddi kardiyovasküler ve nörolojik komplikasyonlara yol açabilir. Haloperidol, bu hastalarda sempatik aktivitede ve kardiyovasküler instabilite riskinde artış yaratabilir.

Ayrıca NORODOL® KÜB belgesinin 4.3. bölümünde belirtilen kontrendikasyonlar arasında kardiyak risk faktörleri önemli bir yer tutmaktadır. Haloperidol "QT aralığı uzamasına neden olabilecek potansiyeli" taşımakta ve "2. veya 3. derece kalp blogu, düzeltilmemiş hipokalemi, Tor...
```

**Analiz:** F=0.86. Kontrendike kararı doğru ama mekanizma dolaylı.

---

## Soru 30 — v3_q30 [doz_bobrek]

**Soru:** GFR 15 olan hastada METAFORMAL kullanılabilir mi?
**F:** NaN | **CR:** 0.5000 | **Contexts:** 5 | **Yanıt:** 1199 karakter

**Ground Truth:**
> Metformin (METAFORMAL) GFR 30 mL/dak altında kontrendikedir. GFR 15 şiddetli böbrek yetmezliği olup laktik asidoz riski nedeniyle METAFORMAL bu hastada kesinlikle kullanılmamalıdır.

**Sistem Yanıtı:**
```
**Hayır, kontrendikedir.**

Bu hasta GFR=15 mL/dak/1.73m² ile Evre 4 böbrek yetmezliğine sahiptir. METAFORMAL KÜB belgelerinde açıkça belirtilmiştir: "Şiddetli böbrek yetmezliği (GFR <30 mL/dak)" metformin kullanımının kontrendikasyonudur [METAFORMAL 1000 mg film kaplı tablet | Madde 4.3 | Kontrendikasyonlar].

Hastanın GFR değeri 15 mL/dak olup, bu değer <30 mL/dak eşiğinin altındadır. Bu durum mutlak kontrendikasyondur ve metformin tedavisi başlanmamalıdır.

Ek olarak, KÜB belgesinde böbrek fonksiyonlarının değerlendirilmesine ilişkin genel uyarı yapılmıştır: "Metformin ile tedaviye başlamadan önce ve sonrasında her yıl en az bir kez olmak üzere Glomerüler Filtrasyon Hızı (GFR) değerlendirilmelidir" [METAFORMAL 1000 mg film kaplı tablet | Madde 4.2 | Böbrek/Karaciğer Yetmezliği]. Bu hast...
```

**Analiz:** CR=0.50. Kontrendike kararı doğru, laktik asidoz kısmen.

---

## Kritik Sorunlar Özeti

### 1. Yanlış Klinik Karar

| Soru | GT Sonucu | Sistem Sonucu | Risk |
|------|-----------|---------------|------|
| v3_q10 (PLAVIX+CANDİDİN) | Antiplatelet etki **azalır** | Etki **değişmez** | 🔴 Kritik (stent hasta) |
| v3_q01 (TEGRETOL+SANORONE) | Kontrendike **değil** | **Kontrendike** | 🟡 Aşırı muhafazakâr |
| v3_q02 (PRADAXA+GFR20) | **Kontrendike** | Doz azalt | 🟡 Yetersiz uyarı |
| v3_q21 (PROPYCIL+SANORONE) | Dikkatli kullan | **Kontrendike** | 🟡 Aşırı muhafazakâr |

### 2. Corpus Boşluğu

| Soru | Eksik Bilgi |
|------|-------------|
| v3_q23 (AVELOX+miyastenia) | Florokinolon-nöromüsküler blokaj |
| v3_q22 (AMARYL+GFR25) | Glimepirid GFR<30 hipoglisemi uyarısı |
| v3_q11 (LUSTRAL emzirme) | Sertralin laktasyon bölümü |
| v3_q25 (JARDIANCE) | Genitoüriner enfeksiyon (context var, model göremedi) |

### 3. Teknik Sorunlar

| Sorun | Açıklama |
|-------|----------|
| Faithfulness NaN %60 | Mistral 300s timeout — 18/30 soru değerlendirilemedi |
| Aşırı uzun yanıtlar | q12: 3099 karakter, q17: 3177 karakter |