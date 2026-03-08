"""
Episodic Memory Bank for the Analyst Engine.
Uses ChromaDB to store past theses and correction logs.
Enforces strict metadata tagging (sector, regime, outcome) to retrieve 
contextually relevant historical mistakes instead of keyword matching.
"""

import os
import chromadb
from chromadb.config import Settings
import hashlib
from typing import Dict, List, Any, Optional
import json

class EpisodicMemory:
    def __init__(self, db_path: str = "data/chroma_db", collection_name: str = "aegis_theses"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize local persistent client
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Create or get the collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _generate_id(self, ticker: str, content: str) -> str:
        """Create unique but deterministic ID."""
        return hashlib.sha256(f"{ticker}_{content}".encode()).hexdigest()

    def store_memory(self, ticker: str, content: str, sector: str, regime: str, outcome: str = "Unknown", memory_type: str = "Thesis") -> str:
        """
        Stores a generated thesis or correction log with mandatory metadata.
        """
        doc_id = self._generate_id(ticker, content)
        
        metadata = {
            "ticker": ticker,
            "sector": sector,
            "regime": regime,
            "outcome": outcome,
            "type": memory_type
        }

        self.collection.upsert(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return doc_id

    def retrieve_lessons(self, sector: str, regime: str, outcome: str = "Loss", n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Queries memory bank explicitly filtered by metadata to retrieve 
        applicable historical lessons (e.g. past losses in specific regimes).
        If the collection is empty, returns [].
        """
        if self.collection.count() == 0:
            return []
            
        where_clause = {
            "$and": [
                {"sector": sector},
                {"regime": regime},
                {"outcome": outcome} # usually we want to learn from losses
            ]
        }
        
        safe_n = min(n_results, self.collection.count())
        if safe_n == 0:
            return []
            
        # Query with semantic concept of trading mistakes since we rely on metadata for strict bounds
        res = self.collection.query(
            query_texts=["trading lesson reflection mistake"],
            n_results=safe_n,
            where=where_clause
        )
        
        results = []
        if res and "documents" in res and res["documents"] and len(res["documents"][0]) > 0:
            for i in range(len(res["documents"][0])):
                results.append({
                    "content": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i]
                })
        return results
