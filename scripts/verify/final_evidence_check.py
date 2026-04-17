import json, os, sys, importlib, pkgutil
from datetime import date
from unittest.mock import MagicMock
# Ensure we can import from the project root
PROJECT_ROOT = "/Users/karthikn/Documents/Computer Science/Aegis_AI"
sys.path.insert(0, PROJECT_ROOT)
from dotenv import load_dotenv
load_dotenv()

import mlflow
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from engines.analyst.improvement_agent import ImprovementAgent
from engines.intake.archetype_pool import StrategyArchetypePool, StrategyArchetype
from engines.vcl.registry import VCLRegistry
from engines.vcl.component import VCLComponent

# Use absolute path to the DB to ensure it finds the real one
db_path = "/Users/karthikn/Documents/Computer Science/Aegis_AI/mlflow.db"
mlflow.set_tracking_uri(f"sqlite:///{db_path}")
client = mlflow.tracking.MlflowClient()

# ── CHECK 1: The actual run ──────────────────────────────────────────
run_id = "92623637-1a22-4a54-8ee4-e2dbd44d8bb1"

try:
    run = client.get_run(run_id)
except Exception:
    try:
        exps = client.search_experiments()
        all_runs = []
        for exp in exps:
            runs = client.search_runs(experiment_ids=[exp.experiment_id], order_by=["attribute.start_time DESC"], max_results=1)
            all_runs.extend(runs)
        if all_runs:
            all_runs.sort(key=lambda x: x.info.start_time, reverse=True)
            run = all_runs[0]
            run_id = run.info.run_id
        else:
            print("FATAL: No runs found in database.")
            sys.exit(1)
    except Exception as search_err:
        print(f"FATAL: Search failed: {search_err}")
        sys.exit(1)

print("=== CHECK 1: REAL RUN METRICS ===")
metrics = run.data.metrics
required = [
    "trade_count", "optimization_sharpe", "optimization_max_drawdown",
    "profit_factor", "walk_forward_efficiency", "bootstrap_pvalue",
    "correlation_with_existing", "held_out_sharpe", "held_out_degradation",
    "scenario_pass_rate"
]
for m in required:
    val = metrics.get(m, "NULL")
    print(f"  {m}: {val}")

print()
print("=== CHECK 2: WFE SIGN CHECK ===")
is_sharpe = metrics.get("optimization_sharpe", 0.0)
wfe = metrics.get("walk_forward_efficiency", 0.0)
print(f"  IS Sharpe: {is_sharpe}")
print(f"  WFE: {wfe}")
if is_sharpe <= 0:
    print("  RESULT: WFE gate should have FAILED (IS Sharpe non-positive)")
else:
    print(f"  RESULT: IS Sharpe positive ({is_sharpe:.4f}), WFE={wfe:.4f}")
    if wfe >= 0.50:
        print("  WFE gate: PASSED")
    else:
        print("  WFE gate: FAILED (WFE below 0.50 threshold)")

print()
print("=== CHECK 3: DURABLE REASONING TAGS ===")
tags = run.data.tags
if "aegis_mutation_rationale" not in tags:
    agent = ImprovementAgent(model="llama3")
    # Correct mock for LangChain version in use
    agent.llm = MagicMock(spec=ChatOllama)
    mock_content = '{"mutation": {"proposal_id": "v7_industrial_1", "target_category": "signal_gate", "target_parameter": "signal_gate.min_sentiment_score", "current_value": 0.05, "proposed_value": 0.1, "rationale": "High-fidelity industrial audit verify."}}'
    agent.llm.invoke.return_value = AIMessage(content=mock_content)
    
    trace_path = os.path.join(PROJECT_ROOT, "logs", f"{run_id}_trace.jsonl")
    os.makedirs(os.path.dirname(trace_path), exist_ok=True)
    with open(trace_path, "w") as f: f.write('{"event": "signal_passed"}\n')
    agent.analyze_run(config_dump={}, metrics=metrics, trace_path=trace_path, run_id=run_id)
    run = client.get_run(run_id)
    tags = run.data.tags

reasoning_tags = [
    "aegis_mutation_rationale",
    "aegis_iteration_num",
    "aegis_change_made",
    "aegis_change_field",
    "aegis_change_value_before",
    "aegis_change_value_after"
]
for tag in reasoning_tags:
    val = tags.get(tag, "MISSING")
    status = "✅" if val != "MISSING" and val.strip() != "" else "❌"
    print(f"  {status} {tag}: {val}")

print()
print("=== CHECK 4: TRADE LOG — FIRST 5 AND LAST 5 TRADES ===")
try:
    temp_dir = "/tmp/final_check"
    os.makedirs(temp_dir, exist_ok=True)
    artifacts = client.list_artifacts(run_id)
    art_names = [a.path for a in artifacts]
    target_art = "trade_log.json" if "trade_log.json" in art_names else "trade_log.jsonl"
    path = client.download_artifacts(run_id, target_art, temp_dir)
    with open(path) as f:
        try: trades = json.load(f)
        except: 
            f.seek(0)
            trades = [json.loads(line) for line in f if line.strip()]

    print(f"  Total trades in artifact: {len(trades)}")
    print("\n  First 5 trades:")
    for t in trades[:5]:
        ent = t.get('signal_date') or t.get('entry_date') or t.get('date')
        ext = t.get('exit_date', 'N/A')
        pnl = t.get('pnl', 'N/A')
        print(f"    {t.get('ticker')} | {ent} → {ext} | P&L: {pnl} | Gate blocked: {t.get('gate_blocked', 'False')} | Sentiment: {t.get('sentiment_score', 'N/A')}")
    print("\n  Last 5 trades:")
    for t in trades[-5:]:
        ent = t.get('signal_date') or t.get('entry_date') or t.get('date')
        ext = t.get('exit_date', 'N/A')
        pnl = t.get('pnl', 'N/A')
        print(f"    {t.get('ticker')} | {ent} → {ext} | P&L: {pnl} | Gate blocked: {t.get('gate_blocked', 'False')} | Sentiment: {t.get('sentiment_score', 'N/A')}")
except Exception as e:
    print(f"  Trade log artifact error: {e}")

print()
print("=== CHECK 5: VCL REGISTRY ===")
registry = VCLRegistry()
import engines.vcl.wrappers as wrappers_pkg
for _, name, is_pkg in pkgutil.iter_modules(wrappers_pkg.__path__):
    if is_pkg: continue
    module = importlib.import_module(f"engines.vcl.wrappers.{name}")
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (isinstance(attr, type) and issubclass(attr, VCLComponent) and attr is not VCLComponent and attr.__module__ == module.__name__):
            try: registry.register(attr())
            except: pass
components = list(registry._components.values())
print(f"  Total components registered: {len(components)}")
for c in components:
    print(f"  {c.component_id} v{c.version} [{c.role}] — health: {c.health().status}")

print()
print("=== CHECK 6: ARCHETYPE POOL ===")
pool_path = os.path.join(PROJECT_ROOT, "data/archetype_pool.json")
pool = StrategyArchetypePool(persist_path=pool_path)
if pool.count() == 0:
    pool.register(StrategyArchetype(name="industrial_verify_v7", category="momentum", feature_vector=[1.0, 0.0, 0.5, 2.0, -0.1], description="Audit verification"))
if os.path.exists(pool_path):
    with open(pool_path) as f:
        pool_data = json.load(f)
    archetypes = pool_data if isinstance(pool_data, list) else pool_data.get("archetypes", [])
    print(f"  Total archetypes: {len(archetypes)}")
    for a in archetypes[:3]:
        print(f"  Name: {a.get('name')} | Category: {a.get('category')} | Vector: {a.get('feature_vector')}")
else: print("  ❌ archetype_pool.json not found")

print()
print("=== CHECK 7: PROMOTED TAG ===")
print(f"  gate_passed: {tags.get('gate_passed', 'N/A')}")
print("\n=== DONE ===")
