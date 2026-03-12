import os
import json
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime

# Path constants
CONFIG_DIR = "config/saved_strategies"
LINEAGE_PATH = "config/lineage.json"

def _load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def _save_json(path: str, data: Dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def _get_lineage() -> Dict[str, List[Dict[str, Any]]]:
    return _load_json(LINEAGE_PATH)

def _save_lineage(lineage: Dict[str, List[Dict[str, Any]]]):
    _save_json(LINEAGE_PATH, lineage)

def _get_strategy_dir(strategy_name: str) -> str:
    return os.path.join(CONFIG_DIR, strategy_name)

def _get_config_path(strategy_name: str, version: str) -> str:
    return os.path.join(_get_strategy_dir(strategy_name), f"v{version}.json")

def init_strategy(strategy_name: str, base_config_path: str) -> str:
    """Initializes a new strategy from a base template as v1.0."""
    base_config = _load_json(base_config_path)
    if not base_config:
        raise FileNotFoundError(f"Base config not found: {base_config_path}")

    # Initialize at v1.0
    version = "1.0"
    base_config["version"] = version
    base_config["config_id"] = strategy_name

    target_path = _get_config_path(strategy_name, version)
    _save_json(target_path, base_config)

    # Initialize lineage
    lineage = _get_lineage()
    if strategy_name not in lineage:
        lineage[strategy_name] = []
    
    # Don't overwrite existing v1.0 lineage if it exists
    if not any(entry["version"] == version for entry in lineage[strategy_name]):
        lineage[strategy_name].append({
            "version": version,
            "parent_version": None,
            "timestamp": datetime.utcnow().isoformat(),
            "mutation_summary": "Initial creation from template.",
            "promoted_to_sentinel": False
        })
        _save_lineage(lineage)

    return target_path

def increment_version(strategy_name: str, current_version: str, is_major: bool = False) -> str:
    """Calculates the next semantic version string."""
    major, minor = map(int, current_version.split("."))
    if is_major:
        major += 1
        minor = 0
    else:
        minor += 1
    return f"{major}.{minor}"

def save_new_version(
    strategy_name: str, 
    current_version: str, 
    new_config: Dict[str, Any], 
    mutation_summary: str,
    is_major: bool = False,
    audit_session_ref: Optional[str] = None
) -> str:
    """Saves a new config version and updates the lineage."""
    lineage = _get_lineage()
    if strategy_name not in lineage:
        raise ValueError(f"Strategy {strategy_name} not found in lineage. Call init_strategy first.")

    # Check if current version is frozen
    for entry in lineage[strategy_name]:
        if entry["version"] == current_version and entry.get("promoted_to_sentinel", False):
            print(f"⚠️ Warning: Branching from a frozen Sentinel version (v{current_version}). The frozen version remains unchanged.")

    new_version = increment_version(strategy_name, current_version, is_major)
    new_config["version"] = new_version
    new_config["config_id"] = strategy_name

    # Save the file
    target_path = _get_config_path(strategy_name, new_version)
    _save_json(target_path, new_config)

    # Update lineage
    entry = {
        "version": new_version,
        "parent_version": current_version,
        "timestamp": datetime.utcnow().isoformat(),
        "mutation_summary": mutation_summary,
        "promoted_to_sentinel": False
    }
    if audit_session_ref:
        entry["audit_session_ref"] = audit_session_ref

    lineage[strategy_name].append(entry)
    _save_lineage(lineage)

    return target_path

def rollback(strategy_name: str, target_version: str, audit_session_ref: Optional[str] = None):
    """Rolls back to a target version by creating a new major version."""
    lineage = _get_lineage()
    if strategy_name not in lineage:
        print(f"Error: Strategy {strategy_name} not found.")
        return

    # Find the latest version to increment from
    latest_entry = lineage[strategy_name][-1]
    latest_version = latest_entry["version"]

    # Verify target exists
    target_path = _get_config_path(strategy_name, target_version)
    if not os.path.exists(target_path):
        print(f"Error: Config path for v{target_version} not found at {target_path}")
        return

    # Load target config
    target_config = _load_json(target_path)

    # Save as new major version
    summary = f"Human rollback to v{target_version}."
    new_path = save_new_version(
        strategy_name=strategy_name,
        current_version=latest_version,
        new_config=target_config,
        mutation_summary=summary,
        is_major=True,
        audit_session_ref=audit_session_ref
    )

    print(f"✅ Successfully rolled back {strategy_name} to v{target_version}.")
    print(f"📝 New active version created: {new_path}")

def diff_configs(strategy_name: str, v1: str, v2: str):
    """Prints a simple diff between two config versions."""
    path1 = _get_config_path(strategy_name, v1)
    path2 = _get_config_path(strategy_name, v2)

    if not os.path.exists(path1):
        print(f"Error: {path1} not found.")
        return
    if not os.path.exists(path2):
        print(f"Error: {path2} not found.")
        return

    cfg1 = _load_json(path1)
    cfg2 = _load_json(path2)

    # Simple dictionary diff (recursive)
    def _diff_dicts(d1: Dict, d2: Dict, path=""):
        changes = []
        for k in d1:
            if k not in d2:
                changes.append(f"[-] {path}{k}: {d1[k]}")
            elif isinstance(d1[k], dict) and isinstance(d2[k], dict):
                changes.extend(_diff_dicts(d1[k], d2[k], path + k + "."))
            elif d1[k] != d2[k]:
                changes.append(f"[M] {path}{k}: {d1[k]} -> {d2[k]}")
        
        for k in d2:
            if k not in d1:
                changes.append(f"[+] {path}{k}: {d2[k]}")
        return changes

    changes = _diff_dicts(cfg1, cfg2)
    
    print(f"Diff for {strategy_name} (v{v1} -> v{v2}):")
    if not changes:
        print("  No changes found.")
    else:
        for c in changes:
            print(f"  {c}")

def promote_to_sentinel(strategy_name: str, version: str):
    """Freezes a config version for live trading."""
    lineage = _get_lineage()
    if strategy_name not in lineage:
        print(f"Error: Strategy {strategy_name} not found.")
        return

    found = False
    for entry in lineage[strategy_name]:
        if entry["version"] == version:
            entry["promoted_to_sentinel"] = True
            found = True
            break
            
    if found:
        _save_lineage(lineage)
        print(f"🚀 Version {version} of {strategy_name} promoted to Sentinel. It is now FROZEN.")
    else:
        print(f"Error: Version {version} not found in lineage.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aegis AI Strategy Configuration Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    parser_init = subparsers.add_parser("init", help="Initialize a new strategy from a template")
    parser_init.add_argument("strategy_name", help="Name of the strategy (e.g., aapl_optimization)")
    parser_init.add_argument("template_path", help="Path to the base config JSON")

    # rollback
    parser_rb = subparsers.add_parser("rollback", help="Rollback to a specific version")
    parser_rb.add_argument("strategy_name", help="Name of the strategy")
    parser_rb.add_argument("target_version", help="Version to roll back to (e.g., 1.2)")
    parser_rb.add_argument("--audit-ref", help="Optional reference to the audit session that informed this rollback", default=None)

    # diff
    parser_diff = subparsers.add_parser("diff", help="Diff two versions of a strategy")
    parser_diff.add_argument("strategy_name", help="Name of the strategy")
    parser_diff.add_argument("v1", help="First version (e.g., 1.0)")
    parser_diff.add_argument("v2", help="Second version (e.g., 1.4)")

    # promote
    parser_promote = subparsers.add_parser("promote", help="Freeze and promote a version to Sentinel")
    parser_promote.add_argument("strategy_name", help="Name of the strategy")
    parser_promote.add_argument("version", help="Version to promote (e.g., 1.5)")

    args = parser.parse_args()

    if args.command == "init":
        try:
            path = init_strategy(args.strategy_name, args.template_path)
            print(f"✅ Initialized {args.strategy_name} at v1.0 -> {path}")
        except Exception as e:
            print(f"Error: {e}")
            
    elif args.command == "rollback":
        rollback(args.strategy_name, args.target_version, args.audit_ref)
        
    elif args.command == "diff":
        diff_configs(args.strategy_name, args.v1, args.v2)
        
    elif args.command == "promote":
        promote_to_sentinel(args.strategy_name, args.version)
