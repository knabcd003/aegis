"""
Local RAG Worker Agent for Deep Document Analysis.
Interfaces with local Ollama models (like Qwen 2.5) to read large chunks of 
financial documents (10-Ks, earnings transcripts) locally, securely, and for free, 
without blowing up the Claude API context window.
"""

import logging
from typing import Dict, Any

from engines.data_ingestion.semantic_cache import SemanticCache

try:
    from langchain_community.chat_models import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

logger = logging.getLogger(__name__)

class LocalWorker:
    def __init__(self, model_name: str = "qwen2.5", temperature: float = 0.0, use_cache: bool = True):
        """
        Initializes the local worker agent using Ollama.
        """
        if not HAS_LANGCHAIN:
            raise ImportError("Please install `langchain` and `langchain-community` to use the LocalWorker.")
            
        self.model_name = model_name
        self.use_cache = use_cache
        self.cache = SemanticCache() if use_cache else None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info(f"Connecting to local Ollama instance for model: {self.model_name}")
        self.llm = ChatOllama(model=self.model_name, temperature=temperature)

    def extract_information(self, document_text: str, query: str) -> str:
        """
        Reads the large document text and attempts to extract the requested information.
        
        Args:
            document_text: The large block of text (e.g. an SEC filing section).
            query: What the Supervisor wants to know (e.g. 'Summarize CAPEX risks').
            
        Returns:
            The concise answer extracted by the local model.
        """
        system_prompt = (
            "You are a highly analytical expert financial extraction AI. "
            "Read the provided document and answer the user's query PRECISELY "
            "based ONLY on the information in the text. Be concise, objective, and "
            "do not hallucinate outside the text provided."
        )
        
        user_prompt = f"DOCUMENT TEXT:\n{document_text}\n\nQUERY:\n{query}"
        
        if self.use_cache and self.cache:
            cached_response = self.cache.get_cached_response(self.model_name, system_prompt, user_prompt)
            if cached_response:
                return cached_response
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            
            if self.use_cache and self.cache:
                self.cache.save_response(self.model_name, system_prompt, user_prompt, response.content)
                
            return response.content
        except Exception as e:
            self.logger.error(f"Error extracting info via local {self.model_name}: {e}")
            return f"Error extracting info via local {self.model_name}: {e}"
