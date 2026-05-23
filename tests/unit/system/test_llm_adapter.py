import pytest
import litellm
import json
from unittest.mock import patch, MagicMock

from engines.system.llm_adapter import LLMAdapter, AllProvidersExhaustedError, AdapterResponse
from engines.system.llm_router.quota_tracker import QuotaTracker
from engines.system.llm_router.router import ProviderRouter

@pytest.fixture(autouse=True)
def isolate_quota(tmp_path, monkeypatch):
    original_init = QuotaTracker.__init__
    def patched_init(self, providers, persist_path=None):
        original_init(self, providers, persist_path=str(tmp_path / "test_llm_quota.json"))
    monkeypatch.setattr(QuotaTracker, "__init__", patched_init)


@pytest.fixture
def mock_yaml(tmp_path):
    yaml_db = tmp_path / "test_providers.yaml"
    content = """providers:
  - id: local/qwen3:8b
    model: qwen3:8b
    type: ollama
    litellm_model_string: ollama/qwen3:8b
    cost_per_1k_tokens: 0.0
    limits:
      rpd: null
      
  - id: groq/llama-4-scout
    model: llama-4-scout
    type: openai_compatible
    litellm_model_string: groq/llama-4-scout
    cost_per_1k_tokens: 0.05
    limits:
      rpd: 10
      
role_assignments:
  general:
    primary: groq/llama-4-scout
    fallback_chain: [local/qwen3:8b]
    
settings:
  claude_budget_total_usd: 20.0
"""
    yaml_db.write_text(content)
    return str(yaml_db)

@patch('litellm.completion')
def test_successful_invocation(mock_completion, mock_yaml):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Success!"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_completion.return_value = mock_response

    adapter = LLMAdapter(config_path=mock_yaml)
    
    # 1. Quota should be untouched pre-call
    start_rpd = adapter.quota._usage.get("groq/llama-4-scout", 0)
    assert start_rpd == 0
    
    response = adapter.invoke([{"role": "user", "content": "hi"}], "general")
    
    assert response.content == "Success!"
    assert response.provider_id == "groq"
    assert response.prompt_tokens == 10
    assert response.completion_tokens == 20
    
    # Assert quota incremented on success
    end_rpd = adapter.quota._usage.get("groq/llama-4-scout", 0)
    assert end_rpd == 1

@patch('litellm.completion')
def test_fallback_on_429(mock_completion, mock_yaml):
    """
    Test outcome: A RateLimitError on the primary causes the adapter to successfully
    return a response from the secondary provider.
    """
    mock_success = MagicMock()
    mock_success.choices = [MagicMock()]
    mock_success.choices[0].message.content = "Secondary fallback response"
    
    # First call throws RateLimitError, second returns success
    mock_completion.side_effect = [
        litellm.RateLimitError(message="Slow down", llm_provider="", model=""),
        mock_success
    ]

    adapter = LLMAdapter(config_path=mock_yaml)
    response = adapter.invoke([{"role": "user", "content": "hello"}], "general")
    
    # The output should natively come from the secondary fallback chain gracefully
    assert response.provider_id == "local"
    assert response.model_id == "qwen3:8b"
    assert response.was_primary is False
    assert response.content == "Secondary fallback response"
    # Primary groq should now be securely blocked for future router executions
    assert adapter.quota.is_exhausted("groq/llama-4-scout")

@patch('litellm.completion')
def test_all_providers_exhausted(mock_completion, mock_yaml):
    """
    Test that all providers exhausted -> AllProvidersExhaustedError is natively raised
    and we avoid recursion stack panics.
    """
    # Cause every provider in the chain to constantly throw 429
    mock_completion.side_effect = litellm.RateLimitError(message="Always blocked", llm_provider="", model="")
    
    adapter = LLMAdapter(config_path=mock_yaml)
    with pytest.raises(AllProvidersExhaustedError):
        adapter.invoke([{"role": "user", "content": "break everything"}], "general")
