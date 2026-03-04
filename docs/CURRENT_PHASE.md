# Aegis AI — Current Phase Tracker

> **Phase 2: Quant Engine**
> **Progress:** 0% [⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜]

---

## 🎯 Current Objectives
Build the mathematical core of the system. The Quant Engine takes raw market data and computes regime probabilities, portfolio weights, and order flow toxicity.

## 📋 Tasks

### 1. HMM Regime Detection (`hmmlearn`)
- [ ] Implement `hmm_model.py`
- [ ] Train GaussianHMM on VIX & SPY returns
- [ ] Output current market state (Bull, Bear, Chop)
- [ ] Cache state outputs

### 2. Portfolio Optimization (`riskfolio-lib`)
- [ ] Implement `portfolio_optimizer.py`
- [ ] Pull historical price data via DataEngine
- [ ] Calculate Hierarchical Risk Parity (HRP) weights
- [ ] Calculate Conditional Drawdown at Risk (CDaR) constraints
- [ ] Output target portfolio allocations

### 3. VPIN Order Flow (`flowrisk`)
- [ ] Implement `vpin_calculator.py`
- [ ] Compute Volume-Synchronized Probability of Informed Trading
- [ ] Flag high-toxicity (dumping) conditions

## 📁 File Structure Focus
```text
engines/
├── data_ingestion/       ✅ (Completed)
└── quant/                🔨 (Current Focus)
    ├── __init__.py
    ├── hmm_model.py
    ├── portfolio_optimizer.py
    └── vpin_calculator.py
```

## 🧠 Key Decisions
- **HMM vs Simple Moving Averages:** Using HMM for probabilistic regime detection (from research report) rather than simple technical indicators.
- **HRP vs Markowitz:** Using Hierarchical Risk Parity via Riskfolio-Lib because it handles out-of-sample data better than traditional Mean-Variance optimization.

## 🚧 Blockers / Needs
- Need to verify `flowrisk` and `riskfolio-lib` pip installation compatibility.
