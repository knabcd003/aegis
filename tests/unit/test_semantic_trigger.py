import pytest
from engines.sentinel.semantic_trigger import SemanticTrigger

# This downloads a ~350MB model, mark as integration so it doesn't slow down pure unit test suites unless explicitly run
@pytest.mark.integration
def test_semantic_trigger_entailment():
    trigger = SemanticTrigger("cross-encoder/nli-deberta-v3-base")
    
    # Premise: The Analyst's explicit invalidation criteria
    # Framing it as a hypothesis about the world that would invalidate the trade.
    condition = "The company's CEO resigns unexpectedly."
    
    # Hypotheses: Simulated live incoming news headlines
    # In NLI, Premise entails Hypothesis if Premise being true means Hypothesis is true.
    # Actually, the trigger condition is the Premise. The news headline is the Hypothesis.
    headlines = [
        "Company XYZ reports a breakout quarter with record earnings.", # Neutral/Contradiction
        "NVIDIA unveils new AI chip targeting enterprise data centers.", # Neutral
        "Breaking: The CEO of the company has abruptly stepped down from his position.", # Entailment
        "The company settles an old tax dispute with the IRS." # Neutral
    ]
    
    # Evaluate headlines against the trigger
    results = trigger.evaluate(condition, headlines)
    
    print(f"\n[DEBUG] Results: {results}")

    assert len(results) == 4
    
    # Headline 1: Earnings (Not resignation)
    assert results[0]["is_invalidated"] is False
    assert results[0]["entailment_probability"] < 0.5
    
    # Headline 3: CEO Resigns (Match!)
    assert results[2]["is_invalidated"] is True
    assert results[2]["entailment_probability"] > 0.75
    
    # Test batch size 1 boundary using known 99% hit
    single_res = trigger.evaluate(condition, ["Breaking: The CEO of the company has abruptly stepped down from his position."])
    assert single_res[0]["is_invalidated"] is True
    assert single_res[0]["entailment_probability"] > 0.5
    assert single_res[0]["entailment_probability"] > 0.5
