#!/bin/bash
set -e

echo "========================================="
echo " Aegis AI Security & Vulnerability Scan"
echo "========================================="

echo ""
echo "[1] Running Bandit (AST Security Scanner)..."
# -ll means medium and high severity only. -i means ignore standard warnings for tests.
bandit -r engines/ config/ scripts/ -ll -i

echo ""
echo "[2] Running pip-audit (Dependency Vulnerability Scanner)..."
# Scan the requirements.txt file against the PyPA advisory database
# Note: Ignoring specific upstream PyTorch CVEs that would require breaking changes to fix right now.
pip-audit -r requirements.txt --ignore-vuln PYSEC-2025-41 --ignore-vuln PYSEC-2024-259 --ignore-vuln CVE-2025-2953 --ignore-vuln CVE-2025-3730

echo ""
echo "✅ Security Scan Complete! Pipeline is green."
