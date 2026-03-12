import os
import argparse
import mlflow
import json
import logging
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Setup logging
logging.basicConfig(level=logging.WARNING)

class AuditChat:
    def __init__(self, run_id: str, model_name: str = "qwen3:8b"):
        self.run_id = run_id
        self.model = ChatOllama(
            model=model_name,
            temperature=0.1,  # Keep it grounded
            num_predict=1000  # Allow for detailed explanations
        )
        self.messages = []
        self.session_log_path = f"audit_sessions/{self.run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        os.makedirs("audit_sessions", exist_ok=True)
        os.makedirs("prompt_patches", exist_ok=True)
        
        # Internal context cache
        self.config = {}
        self.metrics = {}
        self.supervisor_traces = []
        self.subagent_traces = []
        self.is_subagent_context_loaded = False
        
        self._load_run_data()
        self._init_system_prompt()

    def _load_run_data(self):
        """Loads metrics, config, and top-level traces (Lazy Loading Stage 1)."""
        print(f"Loading context for Run ID: {self.run_id}...")
        mlflow.set_tracking_uri("sqlite:///mlflow.db")
        try:
            run = mlflow.get_run(self.run_id)
            self.metrics = run.data.metrics
            # In a real scenario, you'd fetch the artifact config. Using empty for safe fallback if missing.
            self.config = run.data.params
            print("✅ Loaded Metrics & Config.")
        except Exception as e:
            print(f"⚠️ Failed to load MLflow run (it might not exist or the DB is empty): {e}")

        # Load partial traces
        trace_path = f"debug/traces/recommendation_trace_{self.run_id}.jsonl"
        if os.path.exists(trace_path):
            with open(trace_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("node") == "supervisor" or "recommendation" in entry:
                            self.supervisor_traces.append(entry)
                        else:
                            self.subagent_traces.append(entry)
                    except:
                        pass
            print(f"✅ Loaded {len(self.supervisor_traces)} Supervisor/Evaluation traces.")
        else:
            print(f"⚠️ Warning: No trace file found at {trace_path}.")

    def _init_system_prompt(self):
        prompt = f"""You are the Aegis AI Auditor. 
Your job is to answer the user's questions about a specific backtest run (Run ID: {self.run_id}).

AVAILABLE CONTEXT:
Metrics: {json.dumps(self.metrics, indent=2)}
Config Params: {json.dumps(self.config, indent=2)}
Supervisor Traces: {json.dumps(self.supervisor_traces, indent=2)}

INSTRUCTIONS:
1. Answer the user's questions truthfully based on the context.
2. If the user asks for deep reasoning or sub-agent logs (like Analyst thoughts or Risk Manager vetoes) that are NOT in the current context, politely ask them to type '/load_deep_traces' so you can access that information.
3. If the user asks you to modify a system prompt or instruction based on this audit, you MUST propose a prompt patch instead of modifying files directly.
"""
        self.messages.append(SystemMessage(content=prompt))
        self._log_to_file("SYSTEM", "Initialized context.")

    def _load_deep_traces(self):
        """Loads sub-agent traces (Lazy Loading Stage 2)."""
        if self.is_subagent_context_loaded:
            print("Deep traces are already loaded.")
            return

        print("Loading deep sub-agent traces...")
        prompt_update = f"""\nNEW DEEP TRACES ADDED TO CONTEXT:
Sub-Agent Traces: {json.dumps(self.subagent_traces, indent=2)}
"""
        # Append as a system message to override early assumptions
        self.messages.append(SystemMessage(content=prompt_update))
        self.is_subagent_context_loaded = True
        self._log_to_file("SYSTEM", "Loaded deep sub-agent traces (Analyst, Risk Manager).")
        print("✅ Deep traces loaded into context window.")

    def _create_patch(self, instruction: str):
        """Generates a prompt patch file."""
        patch_file = f"prompt_patches/{self.run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.patch.md"
        content = f"""# Prompt Patch Proposal
Run ID: {self.run_id}
Requested By: Aegis Auditor Chat

## Proposed Modification
{instruction}

---
*To apply this patch, manually update the corresponding `system_prompt` in the `/engines/analyst/` files.*
"""
        with open(patch_file, "w") as f:
            f.write(content)
        
        msg = f"✅ Proposed patch written to: {patch_file}. Please review and apply manually."
        print(msg)
        self._log_to_file("SYSTEM", msg)
        return msg

    def _log_to_file(self, role: str, content: str):
        with open(self.session_log_path, "a") as f:
            f.write(f"\n**{role}**: {content}\n")

    def chat_loop(self):
        print(f"\n💬 Audit Chat Initialized for Run ID: {self.run_id}")
        print("Type 'exit' or 'quit' to end the session.")
        print("Type '/load_deep_traces' if the Auditor needs more detail about Analyst/Risk Manager thoughts.")
        print("Type '/patch <instruction>' to propose a system prompt modification.")
        print("-" * 60)

        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    print(f"Session saved to {self.session_log_path}")
                    break
                
                self._log_to_file("USER", user_input)

                if user_input.lower() == "/load_deep_traces":
                    self._load_deep_traces()
                    continue
                
                if user_input.lower().startswith("/patch "):
                    instruction = str(user_input)[7:]
                    msg = self._create_patch(instruction)
                    self.messages.append(SystemMessage(content=msg))
                    continue

                # Standard chat
                self.messages.append(HumanMessage(content=user_input))
                print("Auditor is thinking...")
                
                response = self.model.invoke(self.messages)
                ai_text = response.content
                
                self.messages.append(AIMessage(content=ai_text))
                self._log_to_file("AUDITOR", ai_text)
                
                print(f"\nAuditor: {ai_text}")

            except KeyboardInterrupt:
                print(f"\nSession saved to {self.session_log_path}")
                break
            except Exception as e:
                print(f"\n⚠️ Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aegis AI Audit Chat")
    parser.add_argument("run_id", help="The MLflow Run ID to audit (e.g., 23d2edf92a52442fbc31baa2cf6de348)")
    
    args = parser.parse_args()
    auditor = AuditChat(args.run_id)
    auditor.chat_loop()
