import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)
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

    def analyze_run(self, config_dump: Dict[str, Any], metrics: Dict[str, float], trace_path: str, run_id: str = None) -> ConfigMutationProposal:
        """
        Reads the run artifacts and proposes a mutation.
        """
        import mlflow

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
3. DIAGNOSIS TROUBLESHOOTING:
   - If Num Trades is 0:
     a. Inspect Traces: Did the 'Analyst' produce any 'BUY' actions?
     b. If NO 'BUY' signals: The problem is likely in 'fundamental_engine' or 'signal_gate' thresholds. Do NOT change position sizing.
     c. If YES 'BUY' signals but they were 'VETOED': The problem is in the 'risk_manager' or 'compliance' thresholds.
     d. If YES 'BUY' signals were 'APPROVED' but not executed: Only then consider 'position_sizing.capital' or 'max_position_pct'.
4. FORMAT: You must output ONLY valid JSON matching the provided schema. Do not add markdown blocks or conversational text.

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
        
        # Validate
        proposal = ConfigMutationProposal(**response)

        # FIX 2: Durable Reasoning - Write rationale to MLflow
        if run_id:
            try:
                # Reopen run if closed using nested=True to avoid active run conflicts
                with mlflow.start_run(run_id=run_id, nested=True):
                    mutation = proposal.mutation
                    mlflow.set_tag("aegis_mutation_rationale", mutation.rationale)
                    mlflow.set_tag("aegis_change_made", f"{mutation.target_parameter}: {mutation.current_value} -> {mutation.proposed_value}")
                    mlflow.set_tag("aegis_change_field", mutation.target_parameter)
                    mlflow.set_tag("aegis_change_value_before", str(mutation.current_value))
                    mlflow.set_tag("aegis_change_value_after", str(mutation.proposed_value))
                    
                    # Track iteration if available in metadata, default to 1
                    it_count = metrics.get("iteration_count", 1)
                    mlflow.set_tag("aegis_iteration_num", str(int(it_count)))
                    
                logger.info(f"Durable rationale persisted to MLflow for run {run_id}")
            except Exception as e:
                logger.error(f"Failed to persist durable rationale to MLflow: {e}")

        return proposal


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
