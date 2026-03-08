import os
import sqlite3
import pytest
from engines.data_ingestion.semantic_cache import SemanticCache

@pytest.fixture
def temp_cache(tmp_path):
    """Provides a temporary SemanticCache instance for testing."""
    db_file = tmp_path / "test_cache.db"
    cache = SemanticCache(db_path=str(db_file))
    yield cache
    # Cleanup
    if db_file.exists():
        os.remove(db_file)

def test_semantic_cache_initialization(temp_cache):
    """Test that the database and table are created successfully."""
    assert os.path.exists(temp_cache.db_path)
    
    conn = sqlite3.connect(temp_cache.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_cache'")
    assert cursor.fetchone() is not None
    conn.close()

def test_semantic_cache_store_and_retrieve(temp_cache):
    """Test storing a mock LLM response and retrieving it via hash match."""
    model = "mock-model-1b"
    sys_prompt = "You are a helpful AI."
    user_prompt = "What is 2+2?"
    response = '{"answer": 4}'
    
    # Initial check should be a miss
    miss = temp_cache.get_cached_response(model, sys_prompt, user_prompt)
    assert miss is None
    
    # Save the response
    temp_cache.save_response(model, sys_prompt, user_prompt, response)
    
    # Second check should be a hit
    hit = temp_cache.get_cached_response(model, sys_prompt, user_prompt)
    assert hit == response

def test_semantic_cache_clear(temp_cache):
    """Test wiping the cache."""
    temp_cache.save_response("qwen", "sys", "user", "resp")
    assert temp_cache.get_cached_response("qwen", "sys", "user") == "resp"
    
    temp_cache.clear_cache()
    
    assert temp_cache.get_cached_response("qwen", "sys", "user") is None

def test_hash_collision_prevention(temp_cache):
    """Ensure different models or slightly different prompts generate unique hashes."""
    temp_cache.save_response("qwen", "sys", "user", "resp_qwen")
    
    # Same prompt, different model -> should be a miss
    assert temp_cache.get_cached_response("llama", "sys", "user") is None
    
    # Same model, different prompt -> should be a miss
    assert temp_cache.get_cached_response("qwen", "sys", "user2") is None
