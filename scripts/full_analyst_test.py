"""
Full Analyst Engine Integration Test

Tests all components built so far in Phase 3 working together:
1. Episodic Memory (ChromaDB)
2. Semantic Cache (SQLite)
3. Local Worker Agent (Qwen 2.5 + LangChain)
4. Semantic Trigger (DeBERTa-v3)
"""
import asyncio
import time
from dotenv import load_dotenv

from engines.data_ingestion.data_engine import DataEngine
from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
from engines.data_ingestion.connectors.sec_edgar_connector import SECEdgarConnector

from engines.analyst.local_worker import LocalWorker
from engines.analyst.episodic_memory import EpisodicMemory
from engines.sentinel.semantic_trigger import SemanticTrigger
from engines.data_ingestion.semantic_cache import SemanticCache

async def run_full_test():
    print("=" * 60)
    print("🚀 INITIALIZING FULL ANALYST COMPONENT TEST")
    print("=" * 60)
    
    # 1. Initialize Everything
    print("\n[System] Booting Data Connectors...")
    engine = DataEngine()
    engine.register(YFinanceConnector())
    engine.register(SECEdgarConnector())
    
    print("[System] Booting Memory & Caching Layers...")
    memory = EpisodicMemory(collection_name="test_memory")
    cache = SemanticCache()
    # Clear cache for the test to prove the speedup
    cache.clear_cache()
    
    print("[System] Booting Local AI Models (Ollama & PyTorch)...")
    worker = LocalWorker(model_name="qwen2.5", use_cache=True)
    trigger = SemanticTrigger()

    ticker = "AAPL"
    
    # ---------------------------------------------------------
    # TEST 1: EPISODIC MEMORY (Storing and Retrieving a Lesson)
    # ---------------------------------------------------------
    print(f"\n" + "-"*40)
    print(f"🧪 TEST 1: EPISODIC MEMORY BANK (ChromaDB)")
    print("-" * 40)
    
    # Simulate a past mistake being saved
    past_mistake = "We bought heavy into tech during a high-inflation regime, ignoring supply chain warnings. We lost 15%."
    print("[Memory] Saving previous mistake to ChromaDB...")
    memory.store_memory(
        ticker=ticker,
        content=past_mistake,
        sector="Technology",
        regime="High Inflation",
        outcome="Loss",
        memory_type="Correction"
    )
    
    # Simulate the Analyst querying for past lessons before making a new tech trade
    print("[Memory] Analyst querying Memory for 'Technology' and 'High Inflation' lessons...")
    lessons = memory.retrieve_lessons(
        sector="Technology",
        regime="High Inflation",
        outcome="Loss",
        n_results=1
    )
    if lessons:
        print(f" > 🧠 Retrieved Lesson: '{lessons[0]['content']}'")
    else:
        print(" > ❌ Failed to retrieve lesson.")


    # ---------------------------------------------------------
    # TEST 2 & 3: QWEN 2.5 RAG + SEMANTIC CACHE SPEEDUP
    # ---------------------------------------------------------
    print(f"\n" + "-"*40)
    print(f"🧪 TEST 2 & 3: QWEN 2.5 RAG WORKER & SEMANTIC CACHE")
    print("-" * 40)
    
    print(f"[Data] Fetching real 10-K fundamentals for {ticker}...")
    fundamentals = engine.get_fundamentals(ticker)
    doc_chunk = str(fundamentals)
    query = "Summarize the top 1 risk factor for this company. Keep it to 1 sentence."
    
    print("\n[Worker] PASS 1: Asking Qwen 2.5 (Cache MISS - Should take 5-15s)...")
    start_time = time.time()
    qwen_answer_1 = worker.extract_information(document_text=doc_chunk, query=query)
    pass1_duration = time.time() - start_time
    print(f" > ⏱️ Time taken: {pass1_duration:.2f} seconds")
    print(f" > 🤖 Output: {qwen_answer_1}")
    
    print("\n[Worker] PASS 2: Asking Qwen 2.5 the EXACT same question (Cache HIT - Should be <0.1s)...")
    start_time = time.time()
    qwen_answer_2 = worker.extract_information(document_text=doc_chunk, query=query)
    pass2_duration = time.time() - start_time
    print(f" > ⏱️ Time taken: {pass2_duration:.4f} seconds")
    print(f" > ⚡ Cache Speedup: {pass1_duration / pass2_duration:.0f}x faster!")


    # ---------------------------------------------------------
    # TEST 4: DEBERTA SEMANTIC TRIGGER
    # ---------------------------------------------------------
    print(f"\n" + "-"*40)
    print(f"🧪 TEST 4: SEMANTIC TRIGGER (DeBERTa-v3) on Live News")
    print("-" * 40)
    
    print(f"[Data] Fetching live Yahoo Finance news for {ticker}...")
    news = engine.get_news(ticker, days=3)
    
    if not news:
        print("[Warning] No recent news found to test.")
    else:
        live_headlines = [item["headline"] for item in news[:3]]
        bearish_trigger = "The company's supply chain is disrupted."
        print(f"[Analyst Trigger Condition]: '{bearish_trigger}'")
        
        print("\n[Sentinel] Scanning live headlines through DeBERTa Cross-Encoder...")
        results = trigger.evaluate(bearish_trigger, live_headlines)
        
        for r in results:
            tripped = "🚨 TRIGGERED" if r["is_invalidated"] else "✅ Safe"
            score = r["entailment_probability"] * 100
            print(f" > [{score:05.2f}% Entailment] {tripped} | {r['headline']}")

    print("\n" + "=" * 60)
    print("✅ FULL INTEGRATION TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run_full_test())
