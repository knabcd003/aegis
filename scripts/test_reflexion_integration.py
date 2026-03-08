import os
import json
from dotenv import load_dotenv

from engines.analyst.reflexion import ReflexionEngine
from engines.analyst.episodic_memory import EpisodicMemory

def run_reflexion_test():
    print("=" * 60)
    print("🚀 INITIALIZING POST-MORTEM REFLEXION TEST")
    print("=" * 60)
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is not set.")
        return

    # Initialize Memory explicitly to verify the write later
    memory = EpisodicMemory(collection_name="test_memory")
    
    print("\n[System] Booting Reflexion Engine (Claude-based Autopsy)...")
    try:
        engine = ReflexionEngine(memory=memory)
    except Exception as e:
        print(f"Failed to initialize Reflexion Engine: {e}")
        return

    # Mock Data for a Failed Trade
    ticker = "NVDA"
    quant_context = {
        "sector": "Semiconductors",
        "regime": "High Volatility Bear Market",
        "vpin_toxicity": 0.92
    }
    
    original_thesis = json.dumps({
        "decision": "BUY",
        "confidence": 0.85,
        "reasoning": "Despite the high VPIN toxicity of 0.92 indicating informed selling, the underlying growth story for AI chips remains completely unprecedented. We assume the VPIN is standard pre-earnings volatility, and the fundamental strength will overpower the High Volatility Bear Market regime."
    })
    
    actual_outcome = "The stock immediately cratered 18% over the next 3 days following an unexpected supply chain constraint report, validating the extreme VPIN toxicity warning."

    print(f"\n[Test] Running Autopsy for {ticker} trade failure...")
    print(f" > Original Thesis ignored VPIN=0.92 in a Bear Market.")
    print(f" > Actual Outcome: Dropped 18%.")
    
    print("\n[Execution] Passing data to LangGraph. Watch the node routing...")
    try:
        final_lesson = engine.run_autopsy(
            ticker=ticker,
            original_thesis=original_thesis,
            quant_context=quant_context,
            actual_outcome=actual_outcome
        )
        print("\n" + "=" * 50)
        print("📝 FINAL EXTRACTED LESSON (Saved to Memory):")
        print("=" * 50)
        print(final_lesson)
        
        # Verify Database Write
        print("\n[Verification] Querying ChromaDB for the generated rule...")
        lessons = memory.retrieve_lessons(
            sector=quant_context["sector"],
            regime=quant_context["regime"],
            outcome="Loss",
            n_results=1
        )
        
        if lessons and final_lesson in lessons[0]["content"]:
            print("✅ SUCCESS: The exact lesson was successfully retrieved from Episodic Memory.")
        else:
            print("❌ FAILURE: The lesson was not retrieved correctly.")
            
    except Exception as e:
        print(f"Graph execution failed: {e}")

if __name__ == "__main__":
    load_dotenv()
    run_reflexion_test()
