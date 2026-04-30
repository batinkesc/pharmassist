#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from src.graph.neo4j_client import get_driver

driver = get_driver()
with driver.session() as s:
    r = s.run("MATCH (d:Drug)-[r]->(e:CYPEnzyme) RETURN type(r) as rel, count(*) as cnt")
    print("=== CYP ilişki tipleri ===")
    for rec in r:
        print(f"  {rec['rel']}: {rec['cnt']}")

    print()
    r2 = s.run("MATCH (d:Drug {name:'SPORANOX 10 MG / ML ORAL COZELTI'})-[r]->(e:CYPEnzyme) RETURN type(r) as rel, e.name as enzyme")
    print("=== SPORANOX CYP ===")
    for rec in r2:
        print(f"  {rec['rel']} -> {rec['enzyme']}")

    print()
    r3 = s.run("MATCH (d:Drug {name:'CORDARONE 150 MG/3 ML IV ENJEKSIYONLUK COZELTI'})-[r]->(e:CYPEnzyme) RETURN type(r) as rel, e.name as enzyme")
    print("=== CORDARONE CYP ===")
    for rec in r3:
        print(f"  {rec['rel']} -> {rec['enzyme']}")

    print()
    r4 = s.run("MATCH (d:Drug {name:'CANDIDIN 150 MG KAPSUL'})-[r]->(e:CYPEnzyme) RETURN type(r) as rel, e.name as enzyme")
    print("=== CANDIDIN CYP ===")
    for rec in r4:
        print(f"  {rec['rel']} -> {rec['enzyme']}")
