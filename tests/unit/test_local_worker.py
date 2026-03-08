import pytest
from engines.analyst.local_worker import LocalWorker

@pytest.mark.integration
def test_local_worker_extraction():
    """
    Test that the local Qwen 2.5 worker can successfully read a block of 
    text locally and answer a query about it without hallucinating.
    """
    worker = LocalWorker(model_name="qwen2.5", temperature=0.0)
    
    mock_10k_section = (
        "Item 1A. Risk Factors.\n"
        "We depend heavily on our supply chain in Southeast Asia. "
        "Due to recent severe weather events and port closures, we expect severe "
        "supply chain delays in Q3, which may negatively impact our EBITDA margins by roughly 200 basis points."
    )
    
    query = "What exactly does the company expect regarding their supply chain in Q3?"
    
    output = worker.extract_information(document_text=mock_10k_section, query=query)
    
    print(f"\n[DEBUG] Worker Output: {output}")
    
    # Assert it grabbed the correct fundamental info
    assert "delays" in output.lower()
    assert "q3" in output.lower()
    
    # Assert it didn't throw an Ollama connection error
    assert "Error" not in output
