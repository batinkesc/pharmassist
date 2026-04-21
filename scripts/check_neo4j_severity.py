#!/usr/bin/env python3
"""
Neo4j Severity Coverage Check

AŞAMA 1.3: Şu an kaç interaction'ın severity'si "unknown"?
Target: Tüm interaction'ların severity tanımlı olması (Dalga 7'e kadar).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph.neo4j_client import run_query

print("=" * 80)
print("NEO4J SEVERITY COVERAGE ANALYSIS")
print("=" * 80)

# Query 1: Severity dağılımı
print("\n1. INTERACTS_WITH Severity Dağılımı:")
result = run_query("""
    MATCH ()-[r:INTERACTS_WITH]->()
    RETURN r.severity as severity, COUNT(r) as count
    ORDER BY count DESC
""")

total_relationships = 0
severity_dist = {}
for row in result:
    severity = row['severity'] or 'unknown'
    count = row['count']
    total_relationships += count
    severity_dist[severity] = count
    print(f"  {severity:20}: {count:6} ({count*100//total_relationships if total_relationships > 0 else 0}%)")

print(f"\n  TOPLAM: {total_relationships}")

# Query 2: Unknown olanları neden unknown?
print("\n2. Unknown Severity Kaynakları:")
unknown_result = run_query("""
    MATCH (d1:Drug)-[r:INTERACTS_WITH {severity: null}]->(d2:Drug)
    LIMIT 10
    RETURN d1.name as drug1, d2.name as drug2, r.kaynak_madde as source
""")

if unknown_result:
    print(f"  Örnek {len(unknown_result)} unknown interaction (ilk 10):")
    for row in unknown_result[:10]:
        print(f"    {row['drug1'][:30]:30} + {row['drug2'][:30]:30}")
        print(f"      → Kaynak: {row['source']}")
else:
    print("  Unknown severity var mı? KONTROL EDILIYOR...")

# Query 3: Critical interactions
print("\n3. Severity Distribution Özeti:")
print(f"  Tanımlanmış:  {severity_dist.get('severe', 0) + severity_dist.get('moderate', 0) + severity_dist.get('mild', 0) + severity_dist.get('contraindicated', 0)}")
print(f"  Unknown:      {severity_dist.get('unknown', 0)}")

# Hedef
if severity_dist.get('unknown', 0) == 0:
    print("\n✅ TÜM SEVERITY'LER TANIMLI")
else:
    unknown_ratio = severity_dist.get('unknown', 0) * 100 // total_relationships
    print(f"\n⚠️  {unknown_ratio}% severity unknown — AŞAMA 2'de otomatik extraction ile çözülecek")

print("\n" + "=" * 80)
