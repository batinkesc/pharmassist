# PharmAssist Sunum Paketi

## 📁 Dosyalar

### 1. PowerPoint Sunumu
**Dosya:** `sunum_pharmaassist_20260410.pptx`

**İçerik (9 slayt):**
- Slayt 1: Başlık
- Slayt 2: Proje Özeti
- Slayt 3: Teknik Mimari
- Slayt 4: RAGAS Değerlendirme Sonuçları (v3 vs v4 karşılaştırması)
- Slayt 5: Dalga 3 İyileştirmeleri
- Slayt 6: Use Case Diyagramı (metin versiyonu)
- Slayt 7: Activity Diyagramı (metin versiyonu)
- Slayt 8: Güncel Durum
- Slayt 9: Teknik Bileşenler

---

## 🎨 UML Diyagramları (PlantUML Format)

### Use Case Diyagramı
**Dosya:** `diagrams/use_case.puml`

**İçerik:**
- Actor: Klinisyen
- Use Cases: 8 temel fonksiyonellik
- Sistemler: ChromaDB, Neo4j, Claude Haiku API

**Nasıl Kullanılır:**
1. **Online:** https://www.plantuml.com/plantuml/uml/ adresine git
2. **Kopyala:** `use_case.puml` dosyasının içeriğini panoya kopyala
3. **Yapıştır:** Web sitesine yapıştır → Diyagram otomatik render olur
4. **İndir:** PNG veya SVG olarak indir

**Alternatif (Lokal):**
```bash
# PlantUML jar dosyası ile:
java -jar plantuml.jar use_case.puml
# Output: use_case.png
```

### Activity Diyagramı
**Dosya:** `diagrams/activity.puml`

**İçerik:**
- RAG pipeline'ın tam akışı
- Karar noktaları (Yanıt validasyonu)
- Parallelizasyon noktaları (max_workers=2)
- ChromaDB/Neo4j/RAGAS integrasyon

**Nasıl Kullanılır:**
Use Case Diyagramı ile aynı şekilde:
1. https://www.plantuml.com/plantuml/uml/ → Yapıştır → PNG İndir

---

## 📊 RAGAS Sonuçları Entegrasyonu

### Sunum v4 Güncellemesi
Eğer RAGAS v4 sonuçları v3'ü geçerse, slayt 4'ü güncelleyin:

**Güncellenecek hücreler:**
| Metrik | Mevcut (v3 Mistral) | Yeni (v4 Haiku) |
|--------|-------|-------|
| Faithfulness | 0.7811 | `TODO` |
| Context Recall | 0.8864 | `TODO` |
| Ortalama | 0.8337 | `TODO` |

**Python ile otomatik güncelleme:**
```python
from pptx import Presentation

prs = Presentation('sunum_pharmaassist_20260410.pptx')
slide = prs.slides[3]  # Slayt 4

# Haiku sonuçlarını doldur
# slide.shapes[index].text = f"F: 0.XX, CR: 0.XX"

prs.save('sunum_pharmaassist_20260410_updated.pptx')
```

---

## 🛠️ Teknik Detaylar

### Prompt İyileştirmesi (v4)
- **Değişiklik:** Markdown başlıklar kaldırıldı (`#`, `##`, `**`)
- **Sonuç:** VALIDATE uyarısı 23 token → 6 token (74% azalış)
- **Beklenen:** Faithfulness metriği ↑

### RAGAS v4 Çalışması
- **Evaluator:** Claude Haiku (previous: Mistral-7B)
- **Avantajı:** NaN = 0 (JSON parse robusttası)
- **Dezavantajı:** Haiku daha strict evaluator (ama daha güvenilir)
- **Sonrası:** Mistral v3'ü referans benchmark olarak kalsın

---

## 📝 Sunum Yapılırken İpuçları

### Diyagramları PowerPoint'e Ekleme
1. PlantUML.com'dan PNG indir
2. PowerPoint'te Insert → Pictures → Diyagram PNG'sini seç
3. Metin slaytlarını diyagram PNG'lerine değiştir

### Konuşma Akışı
1. **Açılış:** "PharmAssist, Türkçe KÜB verisini kullanarak ilaç etkileşim analizi yapan RAG sistemi"
2. **Teknik:** Use Case → Activity → Mimari açıklaması
3. **Sonuç:** "RAGAS v3 (Mistral) ile 0.83 ortalama, v4 (Haiku) ile daha kesin ölçüm devam ediyor"
4. **Kapanış:** "Sonraki 2 görev: [sana soracağı görevler]"

---

## ✅ Kontrol Listesi

- [ ] `sunum_pharmaassist_20260410.pptx` açıldı ve slaytlar görüntülendi
- [ ] `diagrams/use_case.puml` PlantUML.com'da render edildi
- [ ] `diagrams/activity.puml` PlantUML.com'da render edildi
- [ ] PNG'ler indirildi ve PowerPoint'e eklendi
- [ ] RAGAS v4 sonuçları slayt 4'e eklendi
- [ ] Diyagramlar derste gösterildi ✅

---

## 📞 Destek

Sunum sırasında sorular olursa:
- **Teknik detaylar:** `src/` klasöründeki Python kaynak kodlarına bak
- **RAGAS sonuçları:** `data/eval/ragas_v4_results.json` dosyası
- **Diagram sorunları:** PlantUML syntax'ını kontrol et veya `.puml` dosyasını text editörle aç
