import pytest
import os
import shutil
from engines.analyst.episodic_memory import EpisodicMemory

@pytest.fixture
def memory():
    test_db_path = "/tmp/aegis_test_chroma"
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)
    
    mem = EpisodicMemory(db_path=test_db_path)
    yield mem
    
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)

def test_store_and_retrieve_precise_metadata(memory):
    """
    Test that retrieving lessons strictly filters out irrelevant scenarios
    and respects metadata flags like 'Loss', 'Regime', and 'Sector'.
    """
    # Store a successful tech trade in bull market
    memory.store_memory(
        ticker="AAPL",
        content="Bought AAPL due to strong earnings and momentum.",
        sector="Tech",
        regime="Bull",
        outcome="Win",
        memory_type="Thesis"
    )
    
    # Store a failed tech trade in volatile market
    memory.store_memory(
        ticker="NVDA",
        content="Correction Log: Overleveraged during high chop. VPIN spiked but I ignored it.",
        sector="Tech",
        regime="Volatile/Chop",
        outcome="Loss",
        memory_type="Correction"
    )
    
    # Store a failed energy trade in volatile market
    memory.store_memory(
        ticker="XOM",
        content="Correction Log: Oil plummeted unexpectedly.",
        sector="Energy",
        regime="Volatile/Chop",
        outcome="Loss",
        memory_type="Correction"
    )
    
    # We want to retrieve lessons for a Tech stock during a Volatile/Chop regime
    # It should ONLY return the NVDA mistake, completely ignoring the AAPL win and the XOM mistake.
    results = memory.retrieve_lessons(sector="Tech", regime="Volatile/Chop", outcome="Loss")
    
    assert len(results) == 1
    assert results[0]["metadata"]["ticker"] == "NVDA"
    assert "VPIN spiked" in results[0]["content"]
    assert results[0]["metadata"]["outcome"] == "Loss"
