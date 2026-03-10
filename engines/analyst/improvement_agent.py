import json
import os
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

# Pydantic schema enforcing the 1-parameter mutation budget
class ParameterMutation(BaseModel):
    proposal_id: str = Field(description="Unique ID for this mutation proposal.")
    target_category: str = Field(description="The top-level config category (e.g., 'quant_engine', 'fundamental_engine', 'sandbox').")
    target_parameter: str = Field(description="The specific dot-path parameter to change (e.g., 'quant_engine.vpin.toxicity_threshold').")
    current_value: Any = Field(description="The current value of the parameter.")
    proposed_value: Any = Field(description="The new proposed value.")
    rationale: str = Field(description="Detailed rationale explaining EXACTLY why this single parameter change addresses a specific failure or missed opportunity in the trace logs.")

class ConfigMutationProposal(BaseModel):
    mutation: ParameterMutation = Field(description="The single parameter mutation proposed for this iteration. MUST be exactly one.")

class ImprovementAgent:
    """
    Analyzes MLflow run artifacts and proposes exactly ONE parameter mutation
    to improve trading performance based on trace failures.
    """
    def __init__(self, model: str, provider: str = "ollama"):
        self.provider = provider
        self.model = model
        
        if self.provider == "ollama":
            self.llm = ChatOllama(model=self.model, temperature=0.2)
        else:
            raise ValueError(f"Unsupported provider for Sandbox: {self.provider}")
            
        self.parser = JsonOutputParser(pydantic_object=ConfigMutationProposal)

    def analyze_run(self, config_dump: Dict[str, Any], metrics: Dict[str, float], trace_path: str) -> ConfigMutationProposal:
        """
        Reads the run artifacts and proposes a mutation.
        """
        # Load the trace events (limit to last 50 to avoid prompt overflow during dev)
        traces = []
        if os.path.exists(trace_path):
            with open(trace_path, "r") as f:
                for line in f:
                    if line.strip():
                        traces.append(json.loads(line))
        traces = traces[-50:] # Keep context window manageable for 3b model
        
        system_prompt = """You are the Aegis AI Improvement Analyzer.
Your job is to read the results of a trading strategy backtest and propose exactly ONE parameter change to the configuration to improve performance.

CURRENT METRICS (Optimization Partition):
- Total Return: {opt_return:.2f}
- Sharpe Ratio: {opt_sharpe:.2f}
- Num Trades: {opt_num_trades}

You will be given the current Configuration and a sample of the Agent Traces from the run.

CRITICAL RULES:
1. MUTATION BUDGET: You may only propose EXACTLY ONE parameter change. Changing multiple parameters makes it impossible to attribute causality.
2. CAUSALITY: Your rationale must cite specific behavior from the traces (e.g. "Risk agent vetoed 8 times due to VIX threshold being too low").
3. FORMAT: You must output ONLY valid JSON matching the provided schema. Do not add markdown blocks or conversational text.

{format_instructions}
"""
        
        human_prompt = """
CURRENT CONFIGURATION:
{config_json}

RECENT AGENT TRACES:
{traces_json}

Analyze the logs and output your proposed mutation.
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        chain = prompt | self.llm | self.parser
        
        # Invoke the chain
        response = chain.invoke({
            "opt_return": metrics.get("opt_total_return", 0.0),
            "opt_sharpe": metrics.get("opt_sharpe", 0.0),
            "opt_num_trades": metrics.get("opt_num_trades", 0),
            "format_instructions": self.parser.get_format_instructions(),
            "config_json": json.dumps(config_dump, indent=2),
            "traces_json": json.dumps(traces, indent=2)
        })
        
        # Validate and return
        return ConfigMutationProposal(**response)

    def apply_mutation(self, current_config: Dict[str, Any], proposal: ConfigMutationProposal) -> Dict[str, Any]:
        """
        Applies a validated mutation to a configuration dictionary safely.
        """
        new_config = json.loads(json.dumps(current_config)) # Deep copy
        
        param_path = proposal.mutation.target_parameter.split(".")
        
        # Traverse and set
        curr = new_config
        for i, key in enumerate(param_path):
            if i == len(param_path) - 1:
                # Type coerce the proposed value to match the current value's type if possible
                old_val = curr.get(key)
                if old_val is not None:
                    try:
                        proposed = type(old_val)(proposal.mutation.proposed_value)
                        curr[key] = proposed
                    except (ValueError, TypeError):
                        curr[key] = proposal.mutation.proposed_value
                else:
                    curr[key] = proposal.mutation.proposed_value
            else:
                if key not in curr or not isinstance(curr[key], dict):
                    curr[key] = {}
                curr = curr[key]
                
        return new_config
