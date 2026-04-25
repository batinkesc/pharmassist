"""
Neo4j bağlantı yöneticisi — singleton driver pattern.
"""

import os
from functools import lru_cache
from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv
from loguru import logger

load_dotenv(override=True)


@lru_cache(maxsize=1)
def get_driver() -> Driver:
    url  = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pwd  = os.environ.get("NEO4J_PASSWORD", "password")
    driver = GraphDatabase.driver(url, auth=(user, pwd), connection_timeout=5)
    driver.verify_connectivity()
    logger.info(f"Neo4j bağlandı: {url}")
    return driver


def run_query(cypher: str, params: dict | None = None) -> list[dict]:
    """Verilen Cypher sorgusunu çalıştırır, sonuçları dict listesi olarak döner."""
    driver = get_driver()
    params = params or {}
    with driver.session() as session:
        result = session.run(cypher, params)
        return [record.data() for record in result]


def close_driver() -> None:
    driver = get_driver()
    driver.close()
    get_driver.cache_clear()
    logger.info("Neo4j bağlantısı kapatıldı.")
