# Aegis AI — Current Phase Tracker

> **Phase 2: Intelligence Layer & Orchestration**
> **Progress:** 60% [██████░░░░]

---

## 🎯 Current Objectives
Building the reasoning and safety layers. The Intelligence Layer orchestrates specialized agents through a dynamic mesh to produce high-fidelity investment theses.

## 📋 Tasks

### 1. Analyst Mesh (Dynamic LangGraph) ✅
- [x] Implement `AgenticSupervisor` with manifest-based DAG
- [x] Create Node Registry for flexible agent plug-and-play
- [x] Implement DFS Connectivity guardrails
- [x] Support explicit edge routing in strategy JSONs

### 2. High-Fidelity Health Audit ✅
- [x] Implement `health.py` for pre-flight probes
- [x] Integrated `psutil` for unified memory monitoring
- [x] Calibrated cold/warm start latency targets
- [x] Verified qwen3:8b readiness

### 3. Improvement Analyzer Layer 🔨
- [ ] Implement post-run failure analysis
- [ ] Generate Exactly-One parameter mutations
- [ ] Connect traces to configuration improvement loops

## 📁 File Structure Focus
```text
engines/
├── analyst/              ✅ (Completed)
│   ├── supervisor.py     (Orchestrator)
│   ├── analyst.py        (Persona)
│   └── risk_manager.py   (Guardrail)
├── system/               ✅ (Completed)
│   └── health.py         (Pre-flight)
└── improvement/          🔨 (Current Focus)
    └── analyzer.py
```

## 🧠 Key Decisions
- **HMM vs Simple Moving Averages:** Using HMM for probabilistic regime detection (from research report) rather than simple technical indicators.
- **HRP vs Markowitz:** Using Hierarchical Risk Parity via Riskfolio-Lib because it handles out-of-sample data better than traditional Mean-Variance optimization.

## 🚧 Blockers / Needs
- Need to verify `flowrisk` and `riskfolio-lib` pip installation compatibility.
