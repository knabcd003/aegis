"""
Analyst Engine Live Integration Demo
Tests Qwen 2.5 (LocalWorker) and DeBERTa-v3 (SemanticTrigger) against real
live data pulled directly from the Data Engine.
"""
import asyncio
from dotenv import load_dotenv

from engines.data_ingestion.data_engine import DataEngine
from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
from engines.data_ingestion.connectors.sec_edgar_connector import SECEdgarConnector
from engines.data_ingestion.connectors.finbert_connector import FinBERTConnector

from engines.analyst.local_worker import LocalWorker
from engines.sentinel.semantic_trigger import SemanticTrigger

async def run_live_analyst_test():
    print("=" * 60)
    print("🚀 INITIALIZING AEGIS AI LIVE DATA TEST")
    print("=" * 60)
    
    # 1. Initialize Engines
    print("\n[System] Booting Data Connectors...")
    engine = DataEngine()
    engine.register(YFinanceConnector())
    engine.register(SECEdgarConnector())
    finbert = FinBERTConnector()
    
    print("[System] Booting Local AI Models (Ollama & PyTorch)...")
    worker = LocalWorker(model_name="qwen2.5")
    trigger = SemanticTrigger()

    ticker = "AAPL"
    
    # 2. Test 1: Qwen 2.5 reading Real SEC Filings
    print(f"\n" + "-"*40)
    print(f"🧪 TEST 1: RAG WORKER (Qwen 2.5) on {ticker} SEC Filings")
    print("-" * 40)
    print(f"[Data] Fetching real 10-K fundamentals for {ticker}...")
    
    fundamentals = engine.get_fundamentals(ticker)
    
    print("\n[Worker] Asking Qwen 2.5 to extract Apple's supply chain risks from the raw filing output...")
    # Convert dict to string block to simulate text chunking output
    doc_chunk = str(fundamentals)
    
    query = "Based on this data structure, summarize the top 2 risk factors or challenges mentioned for this company's operations. Keep it under 3 sentences."
    qwen_answer = worker.extract_information(document_text=doc_chunk, query=query)
    
    print("\n🤖 QWEN 2.5 OUTPUT:")
    print(qwen_answer)
    
    # 3. Test 2: DeBERTa Semantic Entailment on Real News
    print(f"\n" + "-"*40)
    print(f"🧪 TEST 2: SEMANTIC TRIGGER on {ticker} Live News")
    print("-" * 40)
    print(f"[Data] Fetching live Yahoo Finance news for {ticker}...")
    
    news = engine.get_news(ticker, days=3)
    
    if not news:
        print("[Warning] No recent news found to test.")
    else:
        # Get top 5 headlines
        live_headlines = [item["headline"] for item in news[:5]]
        
        # We will test two triggers: one that shouldn't hit, and one we force to hit
        bearish_trigger = "The company reports declining iPhone sales or revenue misses."
        
        print(f"\n[Analyst Trigger Condition]: '{bearish_trigger}'")
        
        print("\n[Sentinel] Scanning live headlines through DeBERTa Cross-Encoder...")
        results = trigger.evaluate(bearish_trigger, live_headlines)
        
        for r in results:
            tripped = "🚨 TRIGGERED" if r["is_invalidated"] else "✅ Safe"
            score = r["entailment_probability"] * 100
            print(f" > [{score:05.2f}% Entailment] {tripped} | {r['headline']}")
            
            # Use FinBERT just to show the contrast
            sentiment = finbert.score_text(r['headline'])
            print(f"    └─ (FinBERT Base Sentiment: {sentiment['sentiment'].upper()} [{sentiment['score']}])")
            print("")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run_live_analyst_test())
