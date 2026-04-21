// Merge variant '% 0,8 LİDODEKS %5 Dekstroz İçinde İ.V. İnfüzyon İçin Çözelti' into canonical '% 0,4 LİDODEKS %5 Dekstroz İçinde İ.V. İnfüzyon İçin Çözelti'
MATCH (v:Drug {name: '% 0,8 LİDODEKS %5 Dekstroz İçinde İ.V. İnfüzyon İçin Çözelti'}), (c:Drug {name: '% 0,4 LİDODEKS %5 Dekstroz İçinde İ.V. İnfüzyon İçin Çözelti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ACEPER 4 mg tablet' into canonical 'ACEPER 2 mg tablet'
MATCH (v:Drug {name: 'ACEPER 4 mg tablet'}), (c:Drug {name: 'ACEPER 2 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ACEPER 8 mg tablet' into canonical 'ACEPER 2 mg tablet'
MATCH (v:Drug {name: 'ACEPER 8 mg tablet'}), (c:Drug {name: 'ACEPER 2 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ACEPER PLUS 4 mg/1.25 mg tablet' into canonical 'ACEPER 2 mg tablet'
MATCH (v:Drug {name: 'ACEPER PLUS 4 mg/1.25 mg tablet'}), (c:Drug {name: 'ACEPER 2 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ACNOR 50 mg tablet' into canonical 'ACNOR'
MATCH (v:Drug {name: 'ACNOR 50 mg tablet'}), (c:Drug {name: 'ACNOR'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ADAMAKS 200mg/5ml Oral Süspansiyon Hazırlamak İçin Toz' into canonical 'ADAMAKS 500 mg film kaplı tablet'
MATCH (v:Drug {name: 'ADAMAKS 200mg/5ml Oral Süspansiyon Hazırlamak İçin Toz'}), (c:Drug {name: 'ADAMAKS 500 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AKSEF 750 mg IM enjeksiyonluk çözelti hazırlamak için toz ve çözücü' into canonical 'AKSEF 250 mg IM enjeksiyonluk çözelti hazırlamak için toz ve çözücü'
MATCH (v:Drug {name: 'AKSEF 750 mg IM enjeksiyonluk çözelti hazırlamak için toz ve çözücü'}), (c:Drug {name: 'AKSEF 250 mg IM enjeksiyonluk çözelti hazırlamak için toz ve çözücü'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AKTAZİD 50 mg/50 mg film kaplı tablet' into canonical 'AKTAZİD 25 mg/25 mg film kaplı tablet'
MATCH (v:Drug {name: 'AKTAZİD 50 mg/50 mg film kaplı tablet'}), (c:Drug {name: 'AKTAZİD 25 mg/25 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ALDACTONE® -A 25 mg tablet' into canonical 'ALDACTONE® 100 mg tablet'
MATCH (v:Drug {name: 'ALDACTONE® -A 25 mg tablet'}), (c:Drug {name: 'ALDACTONE® 100 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ALTİZEM SR 120 mg Mikropellet Kapsül' into canonical 'ALTİZEM SR 60 mg Mikropellet Kapsül'
MATCH (v:Drug {name: 'ALTİZEM SR 120 mg Mikropellet Kapsül'}), (c:Drug {name: 'ALTİZEM SR 60 mg Mikropellet Kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ALTİZEM SR 180 mg Mikropellet Kapsül' into canonical 'ALTİZEM SR 60 mg Mikropellet Kapsül'
MATCH (v:Drug {name: 'ALTİZEM SR 180 mg Mikropellet Kapsül'}), (c:Drug {name: 'ALTİZEM SR 60 mg Mikropellet Kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ALTİZEM SR 90 mg Mikropellet Kapsül' into canonical 'ALTİZEM SR 60 mg Mikropellet Kapsül'
MATCH (v:Drug {name: 'ALTİZEM SR 90 mg Mikropellet Kapsül'}), (c:Drug {name: 'ALTİZEM SR 60 mg Mikropellet Kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMARYL 2 mg tablet' into canonical 'AMARYL 1 mg tablet'
MATCH (v:Drug {name: 'AMARYL 2 mg tablet'}), (c:Drug {name: 'AMARYL 1 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMARYL 3 mg tablet' into canonical 'AMARYL 1 mg tablet'
MATCH (v:Drug {name: 'AMARYL 3 mg tablet'}), (c:Drug {name: 'AMARYL 1 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMARYL 4 mg tablet' into canonical 'AMARYL 1 mg tablet'
MATCH (v:Drug {name: 'AMARYL 4 mg tablet'}), (c:Drug {name: 'AMARYL 1 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMARYL 6 mg tablet' into canonical 'AMARYL 1 mg tablet'
MATCH (v:Drug {name: 'AMARYL 6 mg tablet'}), (c:Drug {name: 'AMARYL 1 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMLİPİN 10/10 mg film tablet' into canonical 'AMLİPİN 5/5 mg film tablet'
MATCH (v:Drug {name: 'AMLİPİN 10/10 mg film tablet'}), (c:Drug {name: 'AMLİPİN 5/5 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMLİPİN 10/20 mg film tablet' into canonical 'AMLİPİN 5/5 mg film tablet'
MATCH (v:Drug {name: 'AMLİPİN 10/20 mg film tablet'}), (c:Drug {name: 'AMLİPİN 5/5 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMLİPİN 5/10 mg film tablet' into canonical 'AMLİPİN 5/5 mg film tablet'
MATCH (v:Drug {name: 'AMLİPİN 5/10 mg film tablet'}), (c:Drug {name: 'AMLİPİN 5/5 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMLONEB 10/10 mg tablet' into canonical 'AMLONEB 5/5 mg tablet'
MATCH (v:Drug {name: 'AMLONEB 10/10 mg tablet'}), (c:Drug {name: 'AMLONEB 5/5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMLONEB 10/2,5 mg tablet' into canonical 'AMLONEB 5/5 mg tablet'
MATCH (v:Drug {name: 'AMLONEB 10/2,5 mg tablet'}), (c:Drug {name: 'AMLONEB 5/5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMLONEB 10/5 mg tablet' into canonical 'AMLONEB 5/5 mg tablet'
MATCH (v:Drug {name: 'AMLONEB 10/5 mg tablet'}), (c:Drug {name: 'AMLONEB 5/5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMLONEB 5/10 mg tablet' into canonical 'AMLONEB 5/5 mg tablet'
MATCH (v:Drug {name: 'AMLONEB 5/10 mg tablet'}), (c:Drug {name: 'AMLONEB 5/5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMLONEB 5/2,5 mg tablet' into canonical 'AMLONEB 5/5 mg tablet'
MATCH (v:Drug {name: 'AMLONEB 5/2,5 mg tablet'}), (c:Drug {name: 'AMLONEB 5/5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AMLOPER 4 mg/10 mg film kaplı tablet' into canonical 'AMLOPER 4/5 mg film kaplı tablet'
MATCH (v:Drug {name: 'AMLOPER 4 mg/10 mg film kaplı tablet'}), (c:Drug {name: 'AMLOPER 4/5 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ANKEP 100 mg film kaplı tablet' into canonical 'ANKEP 25 mg film kaplı tablet'
MATCH (v:Drug {name: 'ANKEP 100 mg film kaplı tablet'}), (c:Drug {name: 'ANKEP 25 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ANKEP 200 mg film kaplı tablet' into canonical 'ANKEP 25 mg film kaplı tablet'
MATCH (v:Drug {name: 'ANKEP 200 mg film kaplı tablet'}), (c:Drug {name: 'ANKEP 25 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ANKEP  300 mg film kaplı tablet' into canonical 'ANKEP 25 mg film kaplı tablet'
MATCH (v:Drug {name: 'ANKEP  300 mg film kaplı tablet'}), (c:Drug {name: 'ANKEP 25 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ANKEP  400 mg film kaplı tablet' into canonical 'ANKEP 25 mg film kaplı tablet'
MATCH (v:Drug {name: 'ANKEP  400 mg film kaplı tablet'}), (c:Drug {name: 'ANKEP 25 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ANKEP 50 mg film kaplı tablet' into canonical 'ANKEP 25 mg film kaplı tablet'
MATCH (v:Drug {name: 'ANKEP 50 mg film kaplı tablet'}), (c:Drug {name: 'ANKEP 25 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'APO-GO 50 mg/5 ml enjeksiyonluk veya infüzyonluk çözelti içeren ampul' into canonical 'APO-GO 20 mg/2 ml enjeksiyonluk veya infüzyonluk çözelti içeren ampul'
MATCH (v:Drug {name: 'APO-GO 50 mg/5 ml enjeksiyonluk veya infüzyonluk çözelti içeren ampul'}), (c:Drug {name: 'APO-GO 20 mg/2 ml enjeksiyonluk veya infüzyonluk çözelti içeren ampul'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'Aritmal %2 I.M./I.V./S.C. Enjeksiyonluk Çözelti' into canonical 'Aritmal %10 I.M./I.V. Enjeksiyonluk Çözelti'
MATCH (v:Drug {name: 'Aritmal %2 I.M./I.V./S.C. Enjeksiyonluk Çözelti'}), (c:Drug {name: 'Aritmal %10 I.M./I.V. Enjeksiyonluk Çözelti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARLEC® 12,5 mg tablet' into canonical 'ARLEC® 25 mg tablet'
MATCH (v:Drug {name: 'ARLEC® 12,5 mg tablet'}), (c:Drug {name: 'ARLEC® 25 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARLEC® 3.125 mg tablet' into canonical 'ARLEC® 25 mg tablet'
MATCH (v:Drug {name: 'ARLEC® 3.125 mg tablet'}), (c:Drug {name: 'ARLEC® 25 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARLEC® 6,25 mg tablet' into canonical 'ARLEC® 25 mg tablet'
MATCH (v:Drug {name: 'ARLEC® 6,25 mg tablet'}), (c:Drug {name: 'ARLEC® 25 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARLİPTİN MET 50 mg/1000 mg film kaplı tablet' into canonical 'ARLİPTİN MET 50 mg/500 mg film kaplı tablet'
MATCH (v:Drug {name: 'ARLİPTİN MET 50 mg/1000 mg film kaplı tablet'}), (c:Drug {name: 'ARLİPTİN MET 50 mg/500 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARLİPTİN MET 50 mg/850 mg film kaplı tablet' into canonical 'ARLİPTİN MET 50 mg/500 mg film kaplı tablet'
MATCH (v:Drug {name: 'ARLİPTİN MET 50 mg/850 mg film kaplı tablet'}), (c:Drug {name: 'ARLİPTİN MET 50 mg/500 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AROKAN 100 mg tablet' into canonical 'AROKAN 50 mg tablet'
MATCH (v:Drug {name: 'AROKAN 100 mg tablet'}), (c:Drug {name: 'AROKAN 50 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARTJET 10 mg/ 0,4 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör' into canonical 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'ARTJET 10 mg/ 0,4 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'}), (c:Drug {name: 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARTJET 12,5 mg/ 0,5 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör' into canonical 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'ARTJET 12,5 mg/ 0,5 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'}), (c:Drug {name: 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARTJET 15 mg/0,6 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör' into canonical 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'ARTJET 15 mg/0,6 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'}), (c:Drug {name: 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARTJET 17,5 mg/ 0,7 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör' into canonical 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'ARTJET 17,5 mg/ 0,7 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'}), (c:Drug {name: 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARTJET 20 mg/0,8 mL enjeksiyonluk solüsyon içeren kullanıma hazır enjektör' into canonical 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'ARTJET 20 mg/0,8 mL enjeksiyonluk solüsyon içeren kullanıma hazır enjektör'}), (c:Drug {name: 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARTJET 22,5 mg/ 0,9 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör' into canonical 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'ARTJET 22,5 mg/ 0,9 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'}), (c:Drug {name: 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARTJET 7,5 mg/ 0,3 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör' into canonical 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'ARTJET 7,5 mg/ 0,3 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'}), (c:Drug {name: 'ARTJET 25 mg/ 1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ARTROJECT 15 mg/1,5 ml S.C. enjeksiyonluk çözelti içeren kullanıma hazır şırınga' into canonical 'ARTROJECT 10 mg/ml S.C. enjeksiyonluk çözelti içeren kullanıma hazır şırınga'
MATCH (v:Drug {name: 'ARTROJECT 15 mg/1,5 ml S.C. enjeksiyonluk çözelti içeren kullanıma hazır şırınga'}), (c:Drug {name: 'ARTROJECT 10 mg/ml S.C. enjeksiyonluk çözelti içeren kullanıma hazır şırınga'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ASPİRİN® 500 mg tablet' into canonical 'ASPİRİN® 100 mg tablet'
MATCH (v:Drug {name: 'ASPİRİN® 500 mg tablet'}), (c:Drug {name: 'ASPİRİN® 100 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ASPİRİN® COMPLEX 500 mg/30 mg oral süspansiyon için granül içeren saşe' into canonical 'ASPİRİN® 100 mg tablet'
MATCH (v:Drug {name: 'ASPİRİN® COMPLEX 500 mg/30 mg oral süspansiyon için granül içeren saşe'}), (c:Drug {name: 'ASPİRİN® 100 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ASPİRİN® PLUS C 400 mg/ 240 mg efervesan tablet' into canonical 'ASPİRİN® 100 mg tablet'
MATCH (v:Drug {name: 'ASPİRİN® PLUS C 400 mg/ 240 mg efervesan tablet'}), (c:Drug {name: 'ASPİRİN® 100 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AS-KALMEKS 100 mg film tablet' into canonical 'AS-KALMEKS 25 mg film tablet'
MATCH (v:Drug {name: 'AS-KALMEKS 100 mg film tablet'}), (c:Drug {name: 'AS-KALMEKS 25 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AS-KALMEKS 200 mg film tablet' into canonical 'AS-KALMEKS 25 mg film tablet'
MATCH (v:Drug {name: 'AS-KALMEKS 200 mg film tablet'}), (c:Drug {name: 'AS-KALMEKS 25 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AUGMENTİN 400 mg/57 mg oral süspansiyon hazırlamak için kuru toz içeren saşe' into canonical 'AUGMENTİN 500 mg/125 mg film kaplı tablet'
MATCH (v:Drug {name: 'AUGMENTİN 400 mg/57 mg oral süspansiyon hazırlamak için kuru toz içeren saşe'}), (c:Drug {name: 'AUGMENTİN 500 mg/125 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AUGMENTİN  875 mg/ 125 mg film kaplı tablet' into canonical 'AUGMENTİN 500 mg/125 mg film kaplı tablet'
MATCH (v:Drug {name: 'AUGMENTİN  875 mg/ 125 mg film kaplı tablet'}), (c:Drug {name: 'AUGMENTİN 500 mg/125 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AUGMENTİN BID 200 mg+28 mg/5 mL oral süspansiyon hazırlamak için kuru toz' into canonical 'AUGMENTİN 500 mg/125 mg film kaplı tablet'
MATCH (v:Drug {name: 'AUGMENTİN BID 200 mg+28 mg/5 mL oral süspansiyon hazırlamak için kuru toz'}), (c:Drug {name: 'AUGMENTİN 500 mg/125 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AUGMENTİN ES 600 mg+42,9 mg/5 mL oral süspansiyon hazırlamak için kuru toz' into canonical 'AUGMENTİN 500 mg/125 mg film kaplı tablet'
MATCH (v:Drug {name: 'AUGMENTİN ES 600 mg+42,9 mg/5 mL oral süspansiyon hazırlamak için kuru toz'}), (c:Drug {name: 'AUGMENTİN 500 mg/125 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'AVELOX 400 mg/250 ml i.v. infüzyon solüsyonu' into canonical 'AVELOX 400 mg film kaplı tablet'
MATCH (v:Drug {name: 'AVELOX 400 mg/250 ml i.v. infüzyon solüsyonu'}), (c:Drug {name: 'AVELOX 400 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'A-FERİN® 1 mg+160 mg/5 mL pediyatrik şurup' into canonical 'A-FERİN® 300 mg/2 mg/10 mg kapsül'
MATCH (v:Drug {name: 'A-FERİN® 1 mg+160 mg/5 mL pediyatrik şurup'}), (c:Drug {name: 'A-FERİN® 300 mg/2 mg/10 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'A-FERİN FORTE 500 mg/4 mg Film Kaplı Tablet' into canonical 'A-FERİN® 300 mg/2 mg/10 mg kapsül'
MATCH (v:Drug {name: 'A-FERİN FORTE 500 mg/4 mg Film Kaplı Tablet'}), (c:Drug {name: 'A-FERİN® 300 mg/2 mg/10 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'A-FERİN® FORTE 650 mg / 4 mg Film Kaplı Tablet' into canonical 'A-FERİN® 300 mg/2 mg/10 mg kapsül'
MATCH (v:Drug {name: 'A-FERİN® FORTE 650 mg / 4 mg Film Kaplı Tablet'}), (c:Drug {name: 'A-FERİN® 300 mg/2 mg/10 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'A-FERİN SİNÜS 500 mg/30 mg/1,25 mg film kaplı tablet' into canonical 'A-FERİN® 300 mg/2 mg/10 mg kapsül'
MATCH (v:Drug {name: 'A-FERİN SİNÜS 500 mg/30 mg/1,25 mg film kaplı tablet'}), (c:Drug {name: 'A-FERİN® 300 mg/2 mg/10 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'A-FERİN ZERO 120 mg/5 mL pediatrik şurup' into canonical 'A-FERİN® 300 mg/2 mg/10 mg kapsül'
MATCH (v:Drug {name: 'A-FERİN ZERO 120 mg/5 mL pediatrik şurup'}), (c:Drug {name: 'A-FERİN® 300 mg/2 mg/10 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'A-FERİN ZERO 6 PLUS 250 mg/5 mL oral süspansiyon' into canonical 'A-FERİN® 300 mg/2 mg/10 mg kapsül'
MATCH (v:Drug {name: 'A-FERİN ZERO 6 PLUS 250 mg/5 mL oral süspansiyon'}), (c:Drug {name: 'A-FERİN® 300 mg/2 mg/10 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'BELOC® 5 mg/5 ml IV Enjeksiyonluk Çözelti' into canonical 'BELOC'
MATCH (v:Drug {name: 'BELOC® 5 mg/5 ml IV Enjeksiyonluk Çözelti'}), (c:Drug {name: 'BELOC'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'BELOC® ZOK 100 mg kontrollü salımlı film kaplı tablet' into canonical 'BELOC'
MATCH (v:Drug {name: 'BELOC® ZOK 100 mg kontrollü salımlı film kaplı tablet'}), (c:Drug {name: 'BELOC'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'BELOC® ZOK 25 mg kontrollü salımlı film kaplı tablet' into canonical 'BELOC'
MATCH (v:Drug {name: 'BELOC® ZOK 25 mg kontrollü salımlı film kaplı tablet'}), (c:Drug {name: 'BELOC'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'BELOC® ZOK 50 mg kontrollü salımlı film kaplı tablet' into canonical 'BELOC'
MATCH (v:Drug {name: 'BELOC® ZOK 50 mg kontrollü salımlı film kaplı tablet'}), (c:Drug {name: 'BELOC'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'BİVOLEN 10 mg tablet' into canonical 'BİVOLEN 5 mg tablet'
MATCH (v:Drug {name: 'BİVOLEN 10 mg tablet'}), (c:Drug {name: 'BİVOLEN 5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'BRUFEN 600 mg film kaplı tablet' into canonical 'BRUFEN 400 mg film tablet'
MATCH (v:Drug {name: 'BRUFEN 600 mg film kaplı tablet'}), (c:Drug {name: 'BRUFEN 400 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'BRUFEN COLD & FLU 200 mg/30 mg film kaplı tablet' into canonical 'BRUFEN 400 mg film tablet'
MATCH (v:Drug {name: 'BRUFEN COLD & FLU 200 mg/30 mg film kaplı tablet'}), (c:Drug {name: 'BRUFEN 400 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'BRUFEN Retard 800 mg yavaş salımlı film tablet' into canonical 'BRUFEN 400 mg film tablet'
MATCH (v:Drug {name: 'BRUFEN Retard 800 mg yavaş salımlı film tablet'}), (c:Drug {name: 'BRUFEN 400 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CALBİCOR® 12.5 mg tablet' into canonical 'CALBİCOR® 25 mg tablet'
MATCH (v:Drug {name: 'CALBİCOR® 12.5 mg tablet'}), (c:Drug {name: 'CALBİCOR® 25 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CALBİCOR® 6.25 mg tablet' into canonical 'CALBİCOR® 25 mg tablet'
MATCH (v:Drug {name: 'CALBİCOR® 6.25 mg tablet'}), (c:Drug {name: 'CALBİCOR® 25 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CALİRA 10 mg film kaplı tablet' into canonical 'CALİRA 5 mg film kaplı tablet'
MATCH (v:Drug {name: 'CALİRA 10 mg film kaplı tablet'}), (c:Drug {name: 'CALİRA 5 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CALİRA-MET 5 mg/1000 mg film kaplı tablet' into canonical 'CALİRA-MET 5 mg/850 mg film kaplı tablet'
MATCH (v:Drug {name: 'CALİRA-MET 5 mg/1000 mg film kaplı tablet'}), (c:Drug {name: 'CALİRA-MET 5 mg/850 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CALİRA-MET XR 10 mg/1000 mg film kaplı tablet' into canonical 'CALİRA-MET 5 mg/850 mg film kaplı tablet'
MATCH (v:Drug {name: 'CALİRA-MET XR 10 mg/1000 mg film kaplı tablet'}), (c:Drug {name: 'CALİRA-MET 5 mg/850 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CALİRA-MET XR 5 mg/1000 mg film kaplı tablet' into canonical 'CALİRA-MET 5 mg/850 mg film kaplı tablet'
MATCH (v:Drug {name: 'CALİRA-MET XR 5 mg/1000 mg film kaplı tablet'}), (c:Drug {name: 'CALİRA-MET 5 mg/850 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CALİRA-MET XR 5 mg/500 mg film kaplı tablet' into canonical 'CALİRA-MET 5 mg/850 mg film kaplı tablet'
MATCH (v:Drug {name: 'CALİRA-MET XR 5 mg/500 mg film kaplı tablet'}), (c:Drug {name: 'CALİRA-MET 5 mg/850 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CANDİDİN 150 mg kapsül' into canonical 'CANDİDİN 50 mg kapsül'
MATCH (v:Drug {name: 'CANDİDİN 150 mg kapsül'}), (c:Drug {name: 'CANDİDİN 50 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CANDİMAX 100 mg kapsül' into canonical 'CANDİMAX 50 mg kapsül'
MATCH (v:Drug {name: 'CANDİMAX 100 mg kapsül'}), (c:Drug {name: 'CANDİMAX 50 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CANDİMAX 150 mg kapsül' into canonical 'CANDİMAX 50 mg kapsül'
MATCH (v:Drug {name: 'CANDİMAX 150 mg kapsül'}), (c:Drug {name: 'CANDİMAX 50 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CANDİMAX 200 mg kapsül' into canonical 'CANDİMAX 50 mg kapsül'
MATCH (v:Drug {name: 'CANDİMAX 200 mg kapsül'}), (c:Drug {name: 'CANDİMAX 50 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CELEBREX® 200 mg kapsül' into canonical 'CELEBREX® 100 mg kapsül'
MATCH (v:Drug {name: 'CELEBREX® 200 mg kapsül'}), (c:Drug {name: 'CELEBREX® 100 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CELGYN 200 mg kapsül' into canonical 'CELGYN 100 mg kapsül'
MATCH (v:Drug {name: 'CELGYN 200 mg kapsül'}), (c:Drug {name: 'CELGYN 100 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CIPRALEX® 10 mg film kaplı tablet' into canonical 'CIPRALEX® 5 mg film tablet'
MATCH (v:Drug {name: 'CIPRALEX® 10 mg film kaplı tablet'}), (c:Drug {name: 'CIPRALEX® 5 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CIPRALEX® 10 mg/ml Oral Damla, Solüsyon' into canonical 'CIPRALEX® 5 mg film tablet'
MATCH (v:Drug {name: 'CIPRALEX® 10 mg/ml Oral Damla, Solüsyon'}), (c:Drug {name: 'CIPRALEX® 5 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CIPRALEX® 20 mg film kaplı tablet' into canonical 'CIPRALEX® 5 mg film tablet'
MATCH (v:Drug {name: 'CIPRALEX® 20 mg film kaplı tablet'}), (c:Drug {name: 'CIPRALEX® 5 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CIPRALEX® 20 mg/ml Oral Damla' into canonical 'CIPRALEX® 5 mg film tablet'
MATCH (v:Drug {name: 'CIPRALEX® 20 mg/ml Oral Damla'}), (c:Drug {name: 'CIPRALEX® 5 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CİPRO® 250 mg film kaplı tablet' into canonical 'CİPRO® % 0,3 göz damlası'
MATCH (v:Drug {name: 'CİPRO® 250 mg film kaplı tablet'}), (c:Drug {name: 'CİPRO® % 0,3 göz damlası'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CİPRO® 500 mg film kaplı tablet' into canonical 'CİPRO® % 0,3 göz damlası'
MATCH (v:Drug {name: 'CİPRO® 500 mg film kaplı tablet'}), (c:Drug {name: 'CİPRO® % 0,3 göz damlası'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CİPRO® 750 mg film kaplı tablet' into canonical 'CİPRO® % 0,3 göz damlası'
MATCH (v:Drug {name: 'CİPRO® 750 mg film kaplı tablet'}), (c:Drug {name: 'CİPRO® % 0,3 göz damlası'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CLEXANE 120 anti-Xa/0,8 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör' into canonical 'CLEXANE 10000 anti-Xa/1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'CLEXANE 120 anti-Xa/0,8 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'}), (c:Drug {name: 'CLEXANE 10000 anti-Xa/1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CLEXANE 2000 anti-Xa/0,2 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör' into canonical 'CLEXANE 10000 anti-Xa/1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'CLEXANE 2000 anti-Xa/0,2 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'}), (c:Drug {name: 'CLEXANE 10000 anti-Xa/1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CLEXANE 4000 anti-Xa IU/0,4 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör' into canonical 'CLEXANE 10000 anti-Xa/1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'CLEXANE 4000 anti-Xa IU/0,4 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'}), (c:Drug {name: 'CLEXANE 10000 anti-Xa/1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CLEXANE 6000 anti-Xa/0,6 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör' into canonical 'CLEXANE 10000 anti-Xa/1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'CLEXANE 6000 anti-Xa/0,6 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'}), (c:Drug {name: 'CLEXANE 10000 anti-Xa/1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CLEXANE 8000 anti-Xa/0,8 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör' into canonical 'CLEXANE 10000 anti-Xa/1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'
MATCH (v:Drug {name: 'CLEXANE 8000 anti-Xa/0,8 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'}), (c:Drug {name: 'CLEXANE 10000 anti-Xa/1 mL enjeksiyonluk çözelti içeren kullanıma hazır enjektör'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CONTRAMAL 100 mg/2 ml enjeksiyonluk çözelti' into canonical 'CONTRAMAL 50 mg kapsül'
MATCH (v:Drug {name: 'CONTRAMAL 100 mg/2 ml enjeksiyonluk çözelti'}), (c:Drug {name: 'CONTRAMAL 50 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CONTRAMAL 100 mg/ml damla, çözelti' into canonical 'CONTRAMAL 50 mg kapsül'
MATCH (v:Drug {name: 'CONTRAMAL 100 mg/ml damla, çözelti'}), (c:Drug {name: 'CONTRAMAL 50 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CONTRAMAL RETARD 100 mg film kaplı tablet' into canonical 'CONTRAMAL 50 mg kapsül'
MATCH (v:Drug {name: 'CONTRAMAL RETARD 100 mg film kaplı tablet'}), (c:Drug {name: 'CONTRAMAL 50 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'COZAAR 100 mg film kaplı tablet' into canonical 'COZAAR 50 mg film kaplı tablet'
MATCH (v:Drug {name: 'COZAAR 100 mg film kaplı tablet'}), (c:Drug {name: 'COZAAR 50 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CO-DIOVAN® 160 mg/12,5 mg film kaplı tablet' into canonical 'CO-DIOVAN® 160 mg/25 mg film kaplı tablet'
MATCH (v:Drug {name: 'CO-DIOVAN® 160 mg/12,5 mg film kaplı tablet'}), (c:Drug {name: 'CO-DIOVAN® 160 mg/25 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CO-DIOVAN® 320 mg/12,5 mg film kaplı tablet' into canonical 'CO-DIOVAN® 160 mg/25 mg film kaplı tablet'
MATCH (v:Drug {name: 'CO-DIOVAN® 320 mg/12,5 mg film kaplı tablet'}), (c:Drug {name: 'CO-DIOVAN® 160 mg/25 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CO-DIOVAN® 320 mg/25 mg film kaplı tablet' into canonical 'CO-DIOVAN® 160 mg/25 mg film kaplı tablet'
MATCH (v:Drug {name: 'CO-DIOVAN® 320 mg/25 mg film kaplı tablet'}), (c:Drug {name: 'CO-DIOVAN® 160 mg/25 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CO-DIOVAN® 80 mg/12,5 mg film kaplı tablet' into canonical 'CO-DIOVAN® 160 mg/25 mg film kaplı tablet'
MATCH (v:Drug {name: 'CO-DIOVAN® 80 mg/12,5 mg film kaplı tablet'}), (c:Drug {name: 'CO-DIOVAN® 160 mg/25 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CRESTOR 10 mg film kaplı tablet' into canonical 'CRESTOR 5 mg film kaplı tablet'
MATCH (v:Drug {name: 'CRESTOR 10 mg film kaplı tablet'}), (c:Drug {name: 'CRESTOR 5 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CRESTOR 20 mg film kaplı tablet' into canonical 'CRESTOR 5 mg film kaplı tablet'
MATCH (v:Drug {name: 'CRESTOR 20 mg film kaplı tablet'}), (c:Drug {name: 'CRESTOR 5 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CRESTOR® 40 mg film kaplı tablet' into canonical 'CRESTOR 5 mg film kaplı tablet'
MATCH (v:Drug {name: 'CRESTOR® 40 mg film kaplı tablet'}), (c:Drug {name: 'CRESTOR 5 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CYLORİN 100 mg yumuşak kapsül' into canonical 'CYLORİN 25 mg yumuşak kapsül'
MATCH (v:Drug {name: 'CYLORİN 100 mg yumuşak kapsül'}), (c:Drug {name: 'CYLORİN 25 mg yumuşak kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CYMBALTA® 30 mg gastro-rezistan sert kapsül' into canonical 'CYMBALTA® 30 mg kapsül'
MATCH (v:Drug {name: 'CYMBALTA® 30 mg gastro-rezistan sert kapsül'}), (c:Drug {name: 'CYMBALTA® 30 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CYMBALTA® 60 mg gastro-rezistan sert kapsül' into canonical 'CYMBALTA® 30 mg kapsül'
MATCH (v:Drug {name: 'CYMBALTA® 60 mg gastro-rezistan sert kapsül'}), (c:Drug {name: 'CYMBALTA® 30 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'CYMBALTA® 60 mg kapsül' into canonical 'CYMBALTA® 30 mg kapsül'
MATCH (v:Drug {name: 'CYMBALTA® 60 mg kapsül'}), (c:Drug {name: 'CYMBALTA® 30 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DEMOXİF %0,5 göz damlası, çözelti' into canonical 'DEMOXİF 400 mg film kaplı tablet'
MATCH (v:Drug {name: 'DEMOXİF %0,5 göz damlası, çözelti'}), (c:Drug {name: 'DEMOXİF 400 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DEPALEX XR 500 mg uzun etkili film kaplı tablet' into canonical 'DEPALEX XR 300 mg uzun etkili film kaplı tablet'
MATCH (v:Drug {name: 'DEPALEX XR 500 mg uzun etkili film kaplı tablet'}), (c:Drug {name: 'DEPALEX XR 300 mg uzun etkili film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DEPORES % 0.05 oftalmik emülsiyon içeren tek dozluk flakon' into canonical 'DEPORES %0,09 göz damlası, çözelti'
MATCH (v:Drug {name: 'DEPORES % 0.05 oftalmik emülsiyon içeren tek dozluk flakon'}), (c:Drug {name: 'DEPORES %0,09 göz damlası, çözelti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DEPORES FREE % 0,05 göz damlası, emülsiyon' into canonical 'DEPORES %0,09 göz damlası, çözelti'
MATCH (v:Drug {name: 'DEPORES FREE % 0,05 göz damlası, emülsiyon'}), (c:Drug {name: 'DEPORES %0,09 göz damlası, çözelti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DEPORES X %0.1 göz damlası, emülsiyon' into canonical 'DEPORES %0,09 göz damlası, çözelti'
MATCH (v:Drug {name: 'DEPORES X %0.1 göz damlası, emülsiyon'}), (c:Drug {name: 'DEPORES %0,09 göz damlası, çözelti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DEPREXİNAT® 10 mg ağızda dağılabilir tablet' into canonical 'DEPREXİNAT® 10 mg film tablet'
MATCH (v:Drug {name: 'DEPREXİNAT® 10 mg ağızda dağılabilir tablet'}), (c:Drug {name: 'DEPREXİNAT® 10 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DEPREXİNAT® 15 mg ağızda dağılabilir tablet' into canonical 'DEPREXİNAT® 10 mg film tablet'
MATCH (v:Drug {name: 'DEPREXİNAT® 15 mg ağızda dağılabilir tablet'}), (c:Drug {name: 'DEPREXİNAT® 10 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DEPREXİNAT® 15 mg film tablet' into canonical 'DEPREXİNAT® 10 mg film tablet'
MATCH (v:Drug {name: 'DEPREXİNAT® 15 mg film tablet'}), (c:Drug {name: 'DEPREXİNAT® 10 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DİAMİCRON MR 60 mg değiştirilmiş salımlı tablet' into canonical 'DİAMİCRON MR 30 mg değiştirilmiş salımlı tablet'
MATCH (v:Drug {name: 'DİAMİCRON MR 60 mg değiştirilmiş salımlı tablet'}), (c:Drug {name: 'DİAMİCRON MR 30 mg değiştirilmiş salımlı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DİGOXİN-ASSOS® 0,5 mg/2 ml I.V. Enjeksiyonluk Çözelti' into canonical 'DİGOXİN-ASSOS® 0,25 mg Tablet'
MATCH (v:Drug {name: 'DİGOXİN-ASSOS® 0,5 mg/2 ml I.V. Enjeksiyonluk Çözelti'}), (c:Drug {name: 'DİGOXİN-ASSOS® 0,25 mg Tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DİGOXİN-ASSOS® 0,5 mg/ml Oral Damla, Çözelti' into canonical 'DİGOXİN-ASSOS® 0,25 mg Tablet'
MATCH (v:Drug {name: 'DİGOXİN-ASSOS® 0,5 mg/ml Oral Damla, Çözelti'}), (c:Drug {name: 'DİGOXİN-ASSOS® 0,25 mg Tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DİLKOR SR 180 mg Mikropellet Kapsül' into canonical 'DİLKOR SR 60 mg Mikropellet Kapsül'
MATCH (v:Drug {name: 'DİLKOR SR 180 mg Mikropellet Kapsül'}), (c:Drug {name: 'DİLKOR SR 60 mg Mikropellet Kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DİLKOR SR 90 mg Mikropellet Kapsül' into canonical 'DİLKOR SR 60 mg Mikropellet Kapsül'
MATCH (v:Drug {name: 'DİLKOR SR 90 mg Mikropellet Kapsül'}), (c:Drug {name: 'DİLKOR SR 60 mg Mikropellet Kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DİLTİZEM 240 mg uzatılmış salımlı tablet' into canonical 'DİLTİZEM 120 mg uzatılmış salımlı tablet'
MATCH (v:Drug {name: 'DİLTİZEM 240 mg uzatılmış salımlı tablet'}), (c:Drug {name: 'DİLTİZEM 120 mg uzatılmış salımlı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DOSETİA 60 mg gastro-rezistan sert kapsül' into canonical 'DOSETİA 30 mg gastro-rezistan sert kapsül'
MATCH (v:Drug {name: 'DOSETİA 60 mg gastro-rezistan sert kapsül'}), (c:Drug {name: 'DOSETİA 30 mg gastro-rezistan sert kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DROSPORİN 100 mg yumuşak jelatin kapsül' into canonical 'DROSPORİN 25 mg yumuşak jelatin kapsül'
MATCH (v:Drug {name: 'DROSPORİN 100 mg yumuşak jelatin kapsül'}), (c:Drug {name: 'DROSPORİN 25 mg yumuşak jelatin kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'DROSPORİN 50 mg yumuşak jelatin kapsül' into canonical 'DROSPORİN 25 mg yumuşak jelatin kapsül'
MATCH (v:Drug {name: 'DROSPORİN 50 mg yumuşak jelatin kapsül'}), (c:Drug {name: 'DROSPORİN 25 mg yumuşak jelatin kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'EFEXOR® XR 37,5 mg mikropellet kapsül' into canonical 'EFEXOR® XR 75 mg mikropellet kapsül'
MATCH (v:Drug {name: 'EFEXOR® XR 37,5 mg mikropellet kapsül'}), (c:Drug {name: 'EFEXOR® XR 75 mg mikropellet kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ELİQUİS® 2,5 mg film kaplı tablet' into canonical 'ELİQUİS® 5 mg film kaplı tablet'
MATCH (v:Drug {name: 'ELİQUİS® 2,5 mg film kaplı tablet'}), (c:Drug {name: 'ELİQUİS® 5 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'EPAMOR 30 mg/3 mL SC enjeksiyonluk çözelti' into canonical 'EPAMOR 20 mg/2 ml enjeksiyonluk çözelti'
MATCH (v:Drug {name: 'EPAMOR 30 mg/3 mL SC enjeksiyonluk çözelti'}), (c:Drug {name: 'EPAMOR 20 mg/2 ml enjeksiyonluk çözelti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'EPAMOR 50 mg/5 ml enjeksiyonluk çözelti' into canonical 'EPAMOR 20 mg/2 ml enjeksiyonluk çözelti'
MATCH (v:Drug {name: 'EPAMOR 50 mg/5 ml enjeksiyonluk çözelti'}), (c:Drug {name: 'EPAMOR 20 mg/2 ml enjeksiyonluk çözelti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ESMARA 40 mg enterik kaplı pellet tablet' into canonical 'ESMARA 20 mg enterik kaplı pellet tablet'
MATCH (v:Drug {name: 'ESMARA 40 mg enterik kaplı pellet tablet'}), (c:Drug {name: 'ESMARA 20 mg enterik kaplı pellet tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ESNEKS 40 mg enterik kaplı pellet tablet' into canonical 'ESNEKS 20 mg enterik kaplı pellet tablet'
MATCH (v:Drug {name: 'ESNEKS 40 mg enterik kaplı pellet tablet'}), (c:Drug {name: 'ESNEKS 20 mg enterik kaplı pellet tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ESOM 40 mg enterik kaplı mikropellet kapsül' into canonical 'ESOM 20 mg enterik kaplı mikropellet kapsül'
MATCH (v:Drug {name: 'ESOM 40 mg enterik kaplı mikropellet kapsül'}), (c:Drug {name: 'ESOM 20 mg enterik kaplı mikropellet kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ESOM 40 mg IV infüzyonluk/enjeksiyonluk çözelti hazırlamak için toz' into canonical 'ESOM 20 mg enterik kaplı mikropellet kapsül'
MATCH (v:Drug {name: 'ESOM 40 mg IV infüzyonluk/enjeksiyonluk çözelti hazırlamak için toz'}), (c:Drug {name: 'ESOM 20 mg enterik kaplı mikropellet kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'EUTHYROX 100 mcg tablet' into canonical 'EUTHYROX 25 mcg tablet'
MATCH (v:Drug {name: 'EUTHYROX 100 mcg tablet'}), (c:Drug {name: 'EUTHYROX 25 mcg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'EUTHYROX 125 mcg tablet' into canonical 'EUTHYROX 25 mcg tablet'
MATCH (v:Drug {name: 'EUTHYROX 125 mcg tablet'}), (c:Drug {name: 'EUTHYROX 25 mcg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'EUTHYROX 150 mcg tablet' into canonical 'EUTHYROX 25 mcg tablet'
MATCH (v:Drug {name: 'EUTHYROX 150 mcg tablet'}), (c:Drug {name: 'EUTHYROX 25 mcg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'EUTHYROX 175 mcg tablet' into canonical 'EUTHYROX 25 mcg tablet'
MATCH (v:Drug {name: 'EUTHYROX 175 mcg tablet'}), (c:Drug {name: 'EUTHYROX 25 mcg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'EUTHYROX 200 mcg tablet' into canonical 'EUTHYROX 25 mcg tablet'
MATCH (v:Drug {name: 'EUTHYROX 200 mcg tablet'}), (c:Drug {name: 'EUTHYROX 25 mcg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'EUTHYROX 50 mcg tablet' into canonical 'EUTHYROX 25 mcg tablet'
MATCH (v:Drug {name: 'EUTHYROX 50 mcg tablet'}), (c:Drug {name: 'EUTHYROX 25 mcg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'EUTHYROX 75 mcg tablet' into canonical 'EUTHYROX 25 mcg tablet'
MATCH (v:Drug {name: 'EUTHYROX 75 mcg tablet'}), (c:Drug {name: 'EUTHYROX 25 mcg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'EXEN 15 mg/1.5 ml İ.M. Ampul' into canonical 'EXEN'
MATCH (v:Drug {name: 'EXEN 15 mg/1.5 ml İ.M. Ampul'}), (c:Drug {name: 'EXEN'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'FAXİVEN XR 37,5 mg uzatılmış salımlı sert kapsül' into canonical 'FAXİVEN XR 75 mg uzatılmış salımlı sert kapsül'
MATCH (v:Drug {name: 'FAXİVEN XR 37,5 mg uzatılmış salımlı sert kapsül'}), (c:Drug {name: 'FAXİVEN XR 75 mg uzatılmış salımlı sert kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'FİASP® FlexTouch® 100 U/mL enjeksiyonluk çözelti içeren kullanıma hazır kalem' into canonical 'FİASP® Penfill® 100 U/mL enjeksiyonluk çözelti içeren kartuş'
MATCH (v:Drug {name: 'FİASP® FlexTouch® 100 U/mL enjeksiyonluk çözelti içeren kullanıma hazır kalem'}), (c:Drug {name: 'FİASP® Penfill® 100 U/mL enjeksiyonluk çözelti içeren kartuş'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'FIBROCARD L.P. 240 mg Mikropellet İçeren Yavaş Salımlı Kapsül' into canonical 'FIBROCARD L.P. 180 mg Mikropellet İçeren Yavaş Salımlı Kapsül'
MATCH (v:Drug {name: 'FIBROCARD L.P. 240 mg Mikropellet İçeren Yavaş Salımlı Kapsül'}), (c:Drug {name: 'FIBROCARD L.P. 180 mg Mikropellet İçeren Yavaş Salımlı Kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'FLAGYL 125 mg/5 mL oral süspansiyon' into canonical 'FLAGYL 500 mg film kaplı tablet'
MATCH (v:Drug {name: 'FLAGYL 125 mg/5 mL oral süspansiyon'}), (c:Drug {name: 'FLAGYL 500 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'GLUCOTROL  XL  10 mg  kontrollü salım tablet' into canonical 'GLUCOTROL  XL  5 mg  kontrollü salım tablet'
MATCH (v:Drug {name: 'GLUCOTROL  XL  10 mg  kontrollü salım tablet'}), (c:Drug {name: 'GLUCOTROL  XL  5 mg  kontrollü salım tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'HUMALOG 100 IU/ml 10 ml çözelti içeren flakon' into canonical 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'
MATCH (v:Drug {name: 'HUMALOG 100 IU/ml 10 ml çözelti içeren flakon'}), (c:Drug {name: 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'HUMALOG 100 IU/ml 3 ml çözelti içeren kartuş' into canonical 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'
MATCH (v:Drug {name: 'HUMALOG 100 IU/ml 3 ml çözelti içeren kartuş'}), (c:Drug {name: 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'HUMALOG KWIKPEN 100 U/ml s.c. kullanıma hazır çözelti içeren enjeksiyon kalemi' into canonical 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'
MATCH (v:Drug {name: 'HUMALOG KWIKPEN 100 U/ml s.c. kullanıma hazır çözelti içeren enjeksiyon kalemi'}), (c:Drug {name: 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'HUMALOG KWIKPEN 200 U/mL enjeksiyonluk çözelti içeren kullanıma hazır kalem' into canonical 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'
MATCH (v:Drug {name: 'HUMALOG KWIKPEN 200 U/mL enjeksiyonluk çözelti içeren kullanıma hazır kalem'}), (c:Drug {name: 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'HUMALOG MIX25 100 IU/ml 10ml süspansiyon içeren flakon' into canonical 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'
MATCH (v:Drug {name: 'HUMALOG MIX25 100 IU/ml 10ml süspansiyon içeren flakon'}), (c:Drug {name: 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'HUMALOG MIX25 100 IU/ml 3 ml süspansiyon içeren kartuş' into canonical 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'
MATCH (v:Drug {name: 'HUMALOG MIX25 100 IU/ml 3 ml süspansiyon içeren kartuş'}), (c:Drug {name: 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'HUMALOG MIX25 KWIKPEN 100 U/ml s.c. kullanıma hazır süspansiyon içeren enjeksiyon' into canonical 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'
MATCH (v:Drug {name: 'HUMALOG MIX25 KWIKPEN 100 U/ml s.c. kullanıma hazır süspansiyon içeren enjeksiyon'}), (c:Drug {name: 'HUMALOG MIX25 100 IU/ml 3 ml kartuş'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'İMURAN 50 mg film kaplı tablet' into canonical 'İMURAN 25 mg film kaplı tablet'
MATCH (v:Drug {name: 'İMURAN 50 mg film kaplı tablet'}), (c:Drug {name: 'İMURAN 25 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'İSOPTİN 5mg/2 ml IV infüzyonluk çözelti içeren ampul' into canonical 'İSOPTİN'
MATCH (v:Drug {name: 'İSOPTİN 5mg/2 ml IV infüzyonluk çözelti içeren ampul'}), (c:Drug {name: 'İSOPTİN'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'İSOPTİN® KKH 120 mg uzatılmış salımlı tablet' into canonical 'İSOPTİN'
MATCH (v:Drug {name: 'İSOPTİN® KKH 120 mg uzatılmış salımlı tablet'}), (c:Drug {name: 'İSOPTİN'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'İSOPTİN® SR 240 mg Film Tablet' into canonical 'İSOPTİN'
MATCH (v:Drug {name: 'İSOPTİN® SR 240 mg Film Tablet'}), (c:Drug {name: 'İSOPTİN'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'JARDIANCE 25 mg film kaplı tablet' into canonical 'JARDIANCE 10 mg film kaplı tablet'
MATCH (v:Drug {name: 'JARDIANCE 25 mg film kaplı tablet'}), (c:Drug {name: 'JARDIANCE 10 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'KARAZEPİN 400 mg tablet' into canonical 'KARAZEPİN 200 mg tablet'
MATCH (v:Drug {name: 'KARAZEPİN 400 mg tablet'}), (c:Drug {name: 'KARAZEPİN 200 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'KARBALEX 600 mg uzatılmış salımlı tablet' into canonical 'KARBALEX 300 mg uzatılmış salımlı tablet'
MATCH (v:Drug {name: 'KARBALEX 600 mg uzatılmış salımlı tablet'}), (c:Drug {name: 'KARBALEX 300 mg uzatılmış salımlı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'KARVERA SR 240 mg Mikropellet Kapsül' into canonical 'KARVERA SR 120 mg Mikropellet Kapsül'
MATCH (v:Drug {name: 'KARVERA SR 240 mg Mikropellet Kapsül'}), (c:Drug {name: 'KARVERA SR 120 mg Mikropellet Kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'KEPPRA 250 mg film kaplı tablet' into canonical 'KEPPRA 100 mg/mL oral çözelti'
MATCH (v:Drug {name: 'KEPPRA 250 mg film kaplı tablet'}), (c:Drug {name: 'KEPPRA 100 mg/mL oral çözelti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'KEPPRA 500 mg film kaplı tablet' into canonical 'KEPPRA 100 mg/mL oral çözelti'
MATCH (v:Drug {name: 'KEPPRA 500 mg film kaplı tablet'}), (c:Drug {name: 'KEPPRA 100 mg/mL oral çözelti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'KLACID 125 mg/5 ml oral süspansiyon için granül' into canonical 'KLACİD 500 mg film kaplı tablet'
MATCH (v:Drug {name: 'KLACID 125 mg/5 ml oral süspansiyon için granül'}), (c:Drug {name: 'KLACİD 500 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'KLACID 250 mg/5 ml Oral  Süspansiyon İçin Granül' into canonical 'KLACİD 500 mg film kaplı tablet'
MATCH (v:Drug {name: 'KLACID 250 mg/5 ml Oral  Süspansiyon İçin Granül'}), (c:Drug {name: 'KLACİD 500 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'KLACİD® 500 mg I.V. liyofilize toz içeren flakon' into canonical 'KLACİD 500 mg film kaplı tablet'
MATCH (v:Drug {name: 'KLACİD® 500 mg I.V. liyofilize toz içeren flakon'}), (c:Drug {name: 'KLACİD 500 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'KLACİD® MR 500 mg Değiştirilmiş Salım Tablet' into canonical 'KLACİD 500 mg film kaplı tablet'
MATCH (v:Drug {name: 'KLACİD® MR 500 mg Değiştirilmiş Salım Tablet'}), (c:Drug {name: 'KLACİD 500 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LAMICTAL DC 100 mg çözünür / çiğneme tableti' into canonical 'LAMICTAL DC 5 mg çözünür / çiğneme tableti'
MATCH (v:Drug {name: 'LAMICTAL DC 100 mg çözünür / çiğneme tableti'}), (c:Drug {name: 'LAMICTAL DC 5 mg çözünür / çiğneme tableti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LAMICTAL DC 200 mg çözünür / çiğneme tableti' into canonical 'LAMICTAL DC 5 mg çözünür / çiğneme tableti'
MATCH (v:Drug {name: 'LAMICTAL DC 200 mg çözünür / çiğneme tableti'}), (c:Drug {name: 'LAMICTAL DC 5 mg çözünür / çiğneme tableti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LAMICTAL DC 25 mg çözünür / çiğneme tableti' into canonical 'LAMICTAL DC 5 mg çözünür / çiğneme tableti'
MATCH (v:Drug {name: 'LAMICTAL DC 25 mg çözünür / çiğneme tableti'}), (c:Drug {name: 'LAMICTAL DC 5 mg çözünür / çiğneme tableti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LAMICTAL DC 50 mg çözünür / çiğneme tableti' into canonical 'LAMICTAL DC 5 mg çözünür / çiğneme tableti'
MATCH (v:Drug {name: 'LAMICTAL DC 50 mg çözünür / çiğneme tableti'}), (c:Drug {name: 'LAMICTAL DC 5 mg çözünür / çiğneme tableti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LANSOR 30 mg mikropellet kapsül' into canonical 'LANSOR 15 mg mikropellet kapsül'
MATCH (v:Drug {name: 'LANSOR 30 mg mikropellet kapsül'}), (c:Drug {name: 'LANSOR 15 mg mikropellet kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LANTUS® OptiPen®  100 U/ml Subkutan Kullanım için Enjeksiyonluk Solüsyon' into canonical 'LANTUS® SoloStar® 100 U/mL S.C. Enjeksiyonluk Çözelti'
MATCH (v:Drug {name: 'LANTUS® OptiPen®  100 U/ml Subkutan Kullanım için Enjeksiyonluk Solüsyon'}), (c:Drug {name: 'LANTUS® SoloStar® 100 U/mL S.C. Enjeksiyonluk Çözelti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LAROXYL 25 mg film kaplı tablet' into canonical 'LAROXYL 10 mg film kaplı tablet'
MATCH (v:Drug {name: 'LAROXYL 25 mg film kaplı tablet'}), (c:Drug {name: 'LAROXYL 10 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LASİX 20 mg/2 ml IM/IV enjeksiyonluk çözelti' into canonical 'LASİX 40 mg tablet'
MATCH (v:Drug {name: 'LASİX 20 mg/2 ml IM/IV enjeksiyonluk çözelti'}), (c:Drug {name: 'LASİX 40 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LASİX®  500 mg tablet' into canonical 'LASİX 40 mg tablet'
MATCH (v:Drug {name: 'LASİX®  500 mg tablet'}), (c:Drug {name: 'LASİX 40 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LATRİGAL 100 mg çiğneme tableti' into canonical 'LATRİGAL 25 mg çiğneme tableti'
MATCH (v:Drug {name: 'LATRİGAL 100 mg çiğneme tableti'}), (c:Drug {name: 'LATRİGAL 25 mg çiğneme tableti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LATRİGAL 200 mg çiğneme tableti' into canonical 'LATRİGAL 25 mg çiğneme tableti'
MATCH (v:Drug {name: 'LATRİGAL 200 mg çiğneme tableti'}), (c:Drug {name: 'LATRİGAL 25 mg çiğneme tableti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LATRİGAL 50 mg çiğneme tableti' into canonical 'LATRİGAL 25 mg çiğneme tableti'
MATCH (v:Drug {name: 'LATRİGAL 50 mg çiğneme tableti'}), (c:Drug {name: 'LATRİGAL 25 mg çiğneme tableti'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LEVEMIR® FlexPen® 100 U/mL enjeksiyonluk çözelti içeren kullanıma hazır kalem' into canonical 'LEVEMIR® Penfill®  100 U/mL enjeksiyonluk çözelti içeren kartuş'
MATCH (v:Drug {name: 'LEVEMIR® FlexPen® 100 U/mL enjeksiyonluk çözelti içeren kullanıma hazır kalem'}), (c:Drug {name: 'LEVEMIR® Penfill®  100 U/mL enjeksiyonluk çözelti içeren kartuş'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LİPİTOR 20 mg film kaplı tablet' into canonical 'LİPİTOR 10 mg film kaplı tablet'
MATCH (v:Drug {name: 'LİPİTOR 20 mg film kaplı tablet'}), (c:Drug {name: 'LİPİTOR 10 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LİPİTOR 40 mg film kaplı tablet' into canonical 'LİPİTOR 10 mg film kaplı tablet'
MATCH (v:Drug {name: 'LİPİTOR 40 mg film kaplı tablet'}), (c:Drug {name: 'LİPİTOR 10 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LİPİTOR 80 mg film kaplı tablet' into canonical 'LİPİTOR 10 mg film kaplı tablet'
MATCH (v:Drug {name: 'LİPİTOR 80 mg film kaplı tablet'}), (c:Drug {name: 'LİPİTOR 10 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'LUSTRAL SPECIAL® 100 mg film kaplı tablet' into canonical 'LUSTRAL® 50 mg çentikli film kaplı tablet'
MATCH (v:Drug {name: 'LUSTRAL SPECIAL® 100 mg film kaplı tablet'}), (c:Drug {name: 'LUSTRAL® 50 mg çentikli film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'METAFORMAL 1000 mg film kaplı tablet' into canonical 'METAFORMAL 850 mg film kaplı tablet'
MATCH (v:Drug {name: 'METAFORMAL 1000 mg film kaplı tablet'}), (c:Drug {name: 'METAFORMAL 850 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'M-ESLON 100 mg mikropellet kapsül' into canonical 'M-ESLON 10 mg mikropellet kapsül'
MATCH (v:Drug {name: 'M-ESLON 100 mg mikropellet kapsül'}), (c:Drug {name: 'M-ESLON 10 mg mikropellet kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NAPROSYN 500 mg supozituvar' into canonical 'NAPROSYN %10 jel'
MATCH (v:Drug {name: 'NAPROSYN 500 mg supozituvar'}), (c:Drug {name: 'NAPROSYN %10 jel'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NAPROSYN EC 500 mg fort tablet' into canonical 'NAPROSYN %10 jel'
MATCH (v:Drug {name: 'NAPROSYN EC 500 mg fort tablet'}), (c:Drug {name: 'NAPROSYN %10 jel'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NAPROSYN PLUS %10 + %5 deriye uygulanacak sprey, çözelti' into canonical 'NAPROSYN %10 jel'
MATCH (v:Drug {name: 'NAPROSYN PLUS %10 + %5 deriye uygulanacak sprey, çözelti'}), (c:Drug {name: 'NAPROSYN %10 jel'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NAPROSYN Plus % 10 + % 5 jel' into canonical 'NAPROSYN %10 jel'
MATCH (v:Drug {name: 'NAPROSYN Plus % 10 + % 5 jel'}), (c:Drug {name: 'NAPROSYN %10 jel'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NEURONTİN 300 mg kapsül' into canonical 'NEURONTİN 100 mg kapsül'
MATCH (v:Drug {name: 'NEURONTİN 300 mg kapsül'}), (c:Drug {name: 'NEURONTİN 100 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NEURONTİN 400 mg kapsül' into canonical 'NEURONTİN 100 mg kapsül'
MATCH (v:Drug {name: 'NEURONTİN 400 mg kapsül'}), (c:Drug {name: 'NEURONTİN 100 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NEURONTİN 600 mg çentikli film kaplı tablet' into canonical 'NEURONTİN 100 mg kapsül'
MATCH (v:Drug {name: 'NEURONTİN 600 mg çentikli film kaplı tablet'}), (c:Drug {name: 'NEURONTİN 100 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NEURONTİN 800 mg çentikli film kaplı tablet' into canonical 'NEURONTİN 100 mg kapsül'
MATCH (v:Drug {name: 'NEURONTİN 800 mg çentikli film kaplı tablet'}), (c:Drug {name: 'NEURONTİN 100 mg kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NEVESO XR 199.8 mg/87 mg uzatılmış salımlı film kaplı tablet' into canonical 'NEVESO XR 333 mg/145 mg uzatılmış salımlı film kaplı tablet'
MATCH (v:Drug {name: 'NEVESO XR 199.8 mg/87 mg uzatılmış salımlı film kaplı tablet'}), (c:Drug {name: 'NEVESO XR 333 mg/145 mg uzatılmış salımlı film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NORODOL®  2mg/mL oral damla' into canonical 'NORODOL'
MATCH (v:Drug {name: 'NORODOL®  2mg/mL oral damla'}), (c:Drug {name: 'NORODOL'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NORODOL ® 5 mg tablet' into canonical 'NORODOL'
MATCH (v:Drug {name: 'NORODOL ® 5 mg tablet'}), (c:Drug {name: 'NORODOL'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NORVASC® 10 mg ağızda dağılan tablet' into canonical 'NORVASC® 5 mg tablet'
MATCH (v:Drug {name: 'NORVASC® 10 mg ağızda dağılan tablet'}), (c:Drug {name: 'NORVASC® 5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NORVASC® 5 mg ağızda dağılan tablet' into canonical 'NORVASC® 5 mg tablet'
MATCH (v:Drug {name: 'NORVASC® 5 mg ağızda dağılan tablet'}), (c:Drug {name: 'NORVASC® 5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NovoMix 30 FlexPen  100 U/mL enjeksiyonluk süspansiyon içeren kullanıma hazır kalem' into canonical 'NovoMix 30 Penfill  100 U/mL enjeksiyonluk süspansiyon içeren kartuş'
MATCH (v:Drug {name: 'NovoMix 30 FlexPen  100 U/mL enjeksiyonluk süspansiyon içeren kullanıma hazır kalem'}), (c:Drug {name: 'NovoMix 30 Penfill  100 U/mL enjeksiyonluk süspansiyon içeren kartuş'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NovoMix 50 FlexPen  100 U/mL enjeksiyonluk süspansiyon içeren kullanıma hazır kalem' into canonical 'NovoMix 30 Penfill  100 U/mL enjeksiyonluk süspansiyon içeren kartuş'
MATCH (v:Drug {name: 'NovoMix 50 FlexPen  100 U/mL enjeksiyonluk süspansiyon içeren kullanıma hazır kalem'}), (c:Drug {name: 'NovoMix 30 Penfill  100 U/mL enjeksiyonluk süspansiyon içeren kartuş'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NovoRapid®  100 U/mL enjeksiyonluk çözelti içeren flakon' into canonical 'NovoRapid® FlexPen® 3 ml,100 U/ml'
MATCH (v:Drug {name: 'NovoRapid®  100 U/mL enjeksiyonluk çözelti içeren flakon'}), (c:Drug {name: 'NovoRapid® FlexPen® 3 ml,100 U/ml'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NovoRapid FlexPen 100 U/mL enjeksiyonluk çözelti içeren kullanıma hazır kalem' into canonical 'NovoRapid® FlexPen® 3 ml,100 U/ml'
MATCH (v:Drug {name: 'NovoRapid FlexPen 100 U/mL enjeksiyonluk çözelti içeren kullanıma hazır kalem'}), (c:Drug {name: 'NovoRapid® FlexPen® 3 ml,100 U/ml'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'NovoRapid Penfill  100 U/mL enjeksiyonluk çözelti içeren kartuş' into canonical 'NovoRapid® FlexPen® 3 ml,100 U/ml'
MATCH (v:Drug {name: 'NovoRapid Penfill  100 U/mL enjeksiyonluk çözelti içeren kartuş'}), (c:Drug {name: 'NovoRapid® FlexPen® 3 ml,100 U/ml'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ONAXAN® 15 mg film kaplı tablet' into canonical 'ONAXAN® 10 mg film kaplı tablet'
MATCH (v:Drug {name: 'ONAXAN® 15 mg film kaplı tablet'}), (c:Drug {name: 'ONAXAN® 10 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ONAXAN® 20 mg film kaplı tablet' into canonical 'ONAXAN® 10 mg film kaplı tablet'
MATCH (v:Drug {name: 'ONAXAN® 20 mg film kaplı tablet'}), (c:Drug {name: 'ONAXAN® 10 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ONAXAN® 2,5 mg film kaplı tablet' into canonical 'ONAXAN® 10 mg film kaplı tablet'
MATCH (v:Drug {name: 'ONAXAN® 2,5 mg film kaplı tablet'}), (c:Drug {name: 'ONAXAN® 10 mg film kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'PANTPAS® 40 mg IV enjeksiyonluk toz içeren flakon' into canonical 'PANTPAS® 40 mg enterik kaplı tablet'
MATCH (v:Drug {name: 'PANTPAS® 40 mg IV enjeksiyonluk toz içeren flakon'}), (c:Drug {name: 'PANTPAS® 40 mg enterik kaplı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'PLASORİN 10 mg tablet' into canonical 'PLASORİN 5 mg tablet'
MATCH (v:Drug {name: 'PLASORİN 10 mg tablet'}), (c:Drug {name: 'PLASORİN 5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'PRADAXA® 150 mg sert kapsül' into canonical 'PRADAXA® 75 mg sert kapsül'
MATCH (v:Drug {name: 'PRADAXA® 150 mg sert kapsül'}), (c:Drug {name: 'PRADAXA® 75 mg sert kapsül'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'PRECORT 16 mg Tablet' into canonical 'PRECORT 4 mg Tablet'
MATCH (v:Drug {name: 'PRECORT 16 mg Tablet'}), (c:Drug {name: 'PRECORT 4 mg Tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'PREDLOCORT 250 mg I.M./I.V. enjeksiyonluk/infüzyonluk çözelti hazırlamak için liyofilize' into canonical 'PREDLOCORT 20 mg I.M./I.V. enjeksiyonluk/infüzyonluk çözelti hazırlamak için liyofilize'
MATCH (v:Drug {name: 'PREDLOCORT 250 mg I.M./I.V. enjeksiyonluk/infüzyonluk çözelti hazırlamak için liyofilize'}), (c:Drug {name: 'PREDLOCORT 20 mg I.M./I.V. enjeksiyonluk/infüzyonluk çözelti hazırlamak için liyofilize'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'PREDLOCORT 40 mg I.M./I.V. enjeksiyonluk/infüzyonluk çözelti hazırlamak için liyofilize' into canonical 'PREDLOCORT 20 mg I.M./I.V. enjeksiyonluk/infüzyonluk çözelti hazırlamak için liyofilize'
MATCH (v:Drug {name: 'PREDLOCORT 40 mg I.M./I.V. enjeksiyonluk/infüzyonluk çözelti hazırlamak için liyofilize'}), (c:Drug {name: 'PREDLOCORT 20 mg I.M./I.V. enjeksiyonluk/infüzyonluk çözelti hazırlamak için liyofilize'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'PROKSİVAL XR 500mg Uzun Etkili Film Tablet' into canonical 'PROKSİVAL XR 300mg Uzun Etkili Film Tablet'
MATCH (v:Drug {name: 'PROKSİVAL XR 500mg Uzun Etkili Film Tablet'}), (c:Drug {name: 'PROKSİVAL XR 300mg Uzun Etkili Film Tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'RENITEC 10 mg tablet' into canonical 'RENITEC 5 mg tablet'
MATCH (v:Drug {name: 'RENITEC 10 mg tablet'}), (c:Drug {name: 'RENITEC 5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'RENITEC 20 mg tablet' into canonical 'RENITEC 5 mg tablet'
MATCH (v:Drug {name: 'RENITEC 20 mg tablet'}), (c:Drug {name: 'RENITEC 5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'RİLACE 10 mg tablet' into canonical 'RİLACE'
MATCH (v:Drug {name: 'RİLACE 10 mg tablet'}), (c:Drug {name: 'RİLACE'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'RİLACE 20 mg tablet' into canonical 'RİLACE'
MATCH (v:Drug {name: 'RİLACE 20 mg tablet'}), (c:Drug {name: 'RİLACE'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'RİLACE 40 mg tablet' into canonical 'RİLACE'
MATCH (v:Drug {name: 'RİLACE 40 mg tablet'}), (c:Drug {name: 'RİLACE'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'SUTRIL NEO 10 mg uzatılmış salımlı tablet' into canonical 'SUTRIL NEO 5 mg uzatılmış salımlı tablet'
MATCH (v:Drug {name: 'SUTRIL NEO 10 mg uzatılmış salımlı tablet'}), (c:Drug {name: 'SUTRIL NEO 5 mg uzatılmış salımlı tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'TEGRETOL® 100 mg/5 ml oral süspansiyon' into canonical 'TEGRETOL® % 2 şurup'
MATCH (v:Drug {name: 'TEGRETOL® 100 mg/5 ml oral süspansiyon'}), (c:Drug {name: 'TEGRETOL® % 2 şurup'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'TEGRETOL® 200 mg değiştirilmiş salımlı tablet' into canonical 'TEGRETOL® % 2 şurup'
MATCH (v:Drug {name: 'TEGRETOL® 200 mg değiştirilmiş salımlı tablet'}), (c:Drug {name: 'TEGRETOL® % 2 şurup'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'TORVENTA 10 mg tablet' into canonical 'TORVENTA 5 mg tablet'
MATCH (v:Drug {name: 'TORVENTA 10 mg tablet'}), (c:Drug {name: 'TORVENTA 5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'TORVENTA 200 mg tablet' into canonical 'TORVENTA 5 mg tablet'
MATCH (v:Drug {name: 'TORVENTA 200 mg tablet'}), (c:Drug {name: 'TORVENTA 5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'TORVENTA 20 mg tablet' into canonical 'TORVENTA 5 mg tablet'
MATCH (v:Drug {name: 'TORVENTA 20 mg tablet'}), (c:Drug {name: 'TORVENTA 5 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'VOLTAREN® 100 mg suppozituvar' into canonical 'VOLTAREN EMULGEL'
MATCH (v:Drug {name: 'VOLTAREN® 100 mg suppozituvar'}), (c:Drug {name: 'VOLTAREN EMULGEL'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'VOLTAREN 100 mg uzatılmış salımlı tablet' into canonical 'VOLTAREN EMULGEL'
MATCH (v:Drug {name: 'VOLTAREN 100 mg uzatılmış salımlı tablet'}), (c:Drug {name: 'VOLTAREN EMULGEL'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'VOLTAREN 25 mg enterik kaplı tablet' into canonical 'VOLTAREN EMULGEL'
MATCH (v:Drug {name: 'VOLTAREN 25 mg enterik kaplı tablet'}), (c:Drug {name: 'VOLTAREN EMULGEL'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'VOLTAREN EMULGEL %1,16 Jel' into canonical 'VOLTAREN EMULGEL'
MATCH (v:Drug {name: 'VOLTAREN EMULGEL %1,16 Jel'}), (c:Drug {name: 'VOLTAREN EMULGEL'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'VOLTAREN EMULGEL FORTE %2,32 jel' into canonical 'VOLTAREN EMULGEL'
MATCH (v:Drug {name: 'VOLTAREN EMULGEL FORTE %2,32 jel'}), (c:Drug {name: 'VOLTAREN EMULGEL'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'VOLTAREN Retard 100 mg Tablet' into canonical 'VOLTAREN EMULGEL'
MATCH (v:Drug {name: 'VOLTAREN Retard 100 mg Tablet'}), (c:Drug {name: 'VOLTAREN EMULGEL'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'VOLTAREN SR 75 mg film kaplı tablet' into canonical 'VOLTAREN EMULGEL'
MATCH (v:Drug {name: 'VOLTAREN SR 75 mg film kaplı tablet'}), (c:Drug {name: 'VOLTAREN EMULGEL'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'XANAX® 0.5 mg tablet' into canonical 'XANAX® 1 mg tablet'
MATCH (v:Drug {name: 'XANAX® 0.5 mg tablet'}), (c:Drug {name: 'XANAX® 1 mg tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ZOFRANTM 4 mg/2 mL IM/IV enjeksiyonluk /infüzyonluk çözelti' into canonical 'ZOFRANTM 4 mg film tablet'
MATCH (v:Drug {name: 'ZOFRANTM 4 mg/2 mL IM/IV enjeksiyonluk /infüzyonluk çözelti'}), (c:Drug {name: 'ZOFRANTM 4 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ZOFRANTM 8 mg/4 mL IM/IV enjeksiyonluk /infüzyonluk çözelti' into canonical 'ZOFRANTM 4 mg film tablet'
MATCH (v:Drug {name: 'ZOFRANTM 8 mg/4 mL IM/IV enjeksiyonluk /infüzyonluk çözelti'}), (c:Drug {name: 'ZOFRANTM 4 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ZOFRANTM 8 mg film tablet' into canonical 'ZOFRANTM 4 mg film tablet'
MATCH (v:Drug {name: 'ZOFRANTM 8 mg film tablet'}), (c:Drug {name: 'ZOFRANTM 4 mg film tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v

// Merge variant 'ZOFRAN  ZYDİSTM 8 mg hızlı çözünen dil üstü tablet' into canonical 'ZOFRAN  ZYDİSTM 4mg hızlı çözünen dil üstü tablet'
MATCH (v:Drug {name: 'ZOFRAN  ZYDİSTM 8 mg hızlı çözünen dil üstü tablet'}), (c:Drug {name: 'ZOFRAN  ZYDİSTM 4mg hızlı çözünen dil üstü tablet'})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{type: r.type}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{type: r2.type}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v