import os
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./memory/vector_store")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./memory/trade_history.db")

class MemoryManager:
    def __init__(self):
        """Initializes SQLite and ChromaDB connections and ensures schema exists."""
        # Ensure directories exist
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        os.makedirs(CHROMA_DB_DIR, exist_ok=True)
        
        # Initialize SQLite
        self.sql_conn = sqlite3.connect(SQLITE_DB_PATH)
        self._init_sqlite_schema()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        self.theses_collection = self.chroma_client.get_or_create_collection(
            name="investment_theses",
            metadata={"hnsw:space": "cosine"}
        )

    def _init_sqlite_schema(self):
        """Creates table for execution logs if it doesn't exist."""
        cursor = self.sql_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                qty REAL NOT NULL,
                execution_price REAL,
                status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                exit_reason TEXT
            )
        ''')
        self.sql_conn.commit()

    def log_trade(self, trade_data: Dict[str, Any], exit_reason: str = "") -> int:
        """
        Logs a trade execution to SQLite.
        Returns the inserted row ID.
        """
        cursor = self.sql_conn.cursor()
        cursor.execute('''
            INSERT INTO trades (order_id, symbol, side, qty, execution_price, status, exit_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get("id"),
            trade_data.get("symbol"),
            trade_data.get("side"),
            trade_data.get("qty"),
            trade_data.get("filled_avg_price"),
            trade_data.get("status"),
            exit_reason
        ))
        self.sql_conn.commit()
        return cursor.lastrowid

    def get_recent_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent trades from SQLite."""
        cursor = self.sql_conn.cursor()
        cursor.execute('''
            SELECT id, order_id, symbol, side, qty, execution_price, status, timestamp, exit_reason
            FROM trades ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def store_thesis(self, symbol: str, thesis_text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Stores an investment thesis into ChromaDB vector store.
        """
        document_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        meta = metadata or {}
        meta["symbol"] = symbol
        meta["timestamp"] = datetime.now().isoformat()
        
        self.theses_collection.add(
            documents=[thesis_text],
            metadatas=[meta],
            ids=[document_id]
        )
        return document_id

    def retrieve_theses(self, query: str, symbol_filter: Optional[str] = None, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top k closest theses from ChromaDB based on semantic similarity.
        Optionally filter by ticker symbol.
        """
        where_clause = {"symbol": symbol_filter} if symbol_filter else None
        
        results = self.theses_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_clause
        )
        
        formatted_results = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {}
                })
                
        return formatted_results

    def get_all_theses_for_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Retrieves all theses for a specific symbol.
        """
        results = self.theses_collection.get(
            where={"symbol": symbol}
        )
        
        formatted_results = []
        if results and results.get("documents"):
            for i in range(len(results["documents"])):
                formatted_results.append({
                    "id": results["ids"][i],
                    "document": results["documents"][i],
                    "metadata": results["metadatas"][i] if results.get("metadatas") else {}
                })
                
        return formatted_results
        
    def close(self):
        """Close connections."""
        self.sql_conn.close()
