# scripts/verify/01c_archetype_pool.py
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
from engines.intake.archetype_pool import StrategyArchetypePool, StrategyArchetype

print("=== PHASE 1C: StrategyArchetypePool ===\n")

pool = StrategyArchetypePool()
pool.clear()  # Start fresh for testing

# Register some archetypes to simulate existing promoted strategies
archetypes = [
    StrategyArchetype(
        name="momentum_large_cap_tech",
        category="momentum",
        feature_vector=[1.0, 0.0, 0.0, 0.8, 0.2],
        description="SMA crossover on large-cap tech",
        config_template={}
    ),
    StrategyArchetype(
        name="mean_reversion_energy",
        category="mean_reversion",
        feature_vector=[0.0, 1.0, 0.0, 0.1, 0.9],
        description="RSI-based mean reversion on energy sector",
        config_template={}
    ),
]

for arch in archetypes:
    pool.register(arch)

print(f"Registered {len(pool.list_all())} archetypes")

# Test similarity detection
similar_vector = [0.95, 0.05, 0.0, 0.75, 0.25]  # very similar to momentum_large_cap_tech
dissimilar_vector = [0.0, 0.0, 1.0, 0.5, 0.5]    # different

print(f"\nSimilarity tests:")
print(f"  Similar vector (should be >0.70): {pool.compute_similarity(np.array(similar_vector), np.array([1.0, 0.0, 0.0, 0.8, 0.2])):.3f}")
print(f"  Dissimilar vector (should be <0.70): {pool.compute_similarity(np.array(dissimilar_vector), np.array([1.0, 0.0, 0.0, 0.8, 0.2])):.3f}")

is_too_similar = pool.is_too_similar(np.array(similar_vector))
is_too_dissimilar = pool.is_too_similar(np.array(dissimilar_vector))
print(f"\n  Is similar vector too similar? {is_too_similar} (expected: True)")
print(f"  Is dissimilar vector too similar? {is_too_dissimilar} (expected: False)")

assert is_too_similar, "Similarity detection failed"
assert not is_too_dissimilar, "False positive similarity detection"

# Test exclusion context
context = pool.get_exclusion_context()
print(f"\nExclusion context for Builder prompt:")
print(f"{context}")
assert "momentum_large_cap_tech" in context, "Existing strategy not in exclusion context"
assert len(context) > 50, "Exclusion context too short"

# Test persistence
pool.save()
pool2 = StrategyArchetypePool()
pool2.load()
assert len(pool2.list_all()) == 2, f"Persistence failed: expected 2, got {len(pool2.list_all())}"
print("\n✅ Persistence roundtrip verified")

print("\n✅ PHASE 1C PASSED\n")
