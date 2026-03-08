# Aegis AI: CI/CD & Maintenance Strategy

Before we transition into Live Execution and building the API layer (Phase 4), it is critical to establish a robust CI/CD pipeline. The goal is to ensure stability as we add more complexity, preventing regressions in our data fetching, quant analysis, and LLM reasoning.

## 1. Automated Testing Strategy (Continuous Integration)

Every code push should trigger an automated pipeline (e.g., GitHub Actions) to run the following checks:

### A. Static Analysis & Linting
- **Type Checking (`mypy` / `pyre`):** Ensure type hints are enforced across state dictionaries and API responses.
- **Code Quality (`flake8` / `ruff`):** Lint the codebase to maintain a consistent style.
- **Security Scans (`bandit`):** Scan for hardcoded API keys or vulnerabilities in our connectors.

### B. Unit & Integration Tests (The `pytest` Suite)
- **Local Components:** Run tests for the `SemanticCache`, `EpisodicMemory`, and `SemanticTrigger` (mocking the cross-encoder). Ensure the SQLite and ChromaDB instances initialize correctly in a clean CI runner environment.
- **Agent Output Verification:** Use assertions on LLM test outputs with mock responses to ensure our LangGraph routers obey rules (e.g., stopping on `END` vs. infinite looping).

*Note: Tests requiring actual LLM inference (like Claude) should be mocked in the CI environment to save costs and avoid flaky tests due to network/API latency.*

## 2. Model & Agent Re-Evaluation (Continuous Testing)

Because LLMs are non-deterministic, code passing isn't enough; the AI's *reasoning* must not regress.
- **Golden Dataset Testing:** Maintain a JSON file of 5–10 historical "golden" scenarios containing known Quant data and the expected trading decision.
- **Nightly Smoke Tests:** Run the `AnalystSupervisor` against the golden dataset nightly. If the LLM changes its verdict from "SELL" to "BUY" on an obvious historical crash, fail the pipeline and alert the maintainers.

## 3. Infrastructure & Deployment (Continuous Deployment)

As we build the API layer and prepare for live deployment, the pipeline will need to manage external dependencies:
- **Dockerization:** Containerize the entire engine (FastAPI + LangGraph + ChromaDB + MLflow) into a `Dockerfile`.
- **Environment Management:** Use strict CI secrets for API keys (Anthropic, SEC EDGAR, YFinance proxy). Ensure the runner never leaks these into the logs.
- **Ollama Proxying (If Hosted):** If moving off local Mac execution, the CI/CD pipeline should verify the health of the hosted Ollama/Qwen instances before deploying the main API.

## 4. Proposed GitHub Actions Pipeline Steps:
```yaml
stages:
  - lint
  - test_unit
  - test_integration_mocks
  - nightly_llm_eval (scheduled)
```
