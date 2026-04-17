"""
Strategy Archetype Pool — registry of promoted strategies for diversity tracking.

Persists to JSON. Feature vectors stored as plain lists, converted to numpy
for cosine similarity computation. The Supervisor queries get_exclusion_context()
before every Builder prompt to drive diversity in strategy generation.

Cosine similarity alarm > 0.70. The max_correlation_existing: 0.60 gate in
the Promotion Gate is the hard backstop — this pool drives exploration proactively.
"""
import json
import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any

import numpy as np

logger = logging.getLogger(__name__)


# Strategy categories for diversity tracking
STRATEGY_CATEGORIES = [
    "momentum",
    "mean-reversion",
    "trend-following",
    "pairs-trading",
    "event-driven",
    "earnings-driven",
    "sector-rotation",
    "volatility",
    "statistical-arbitrage",
    "fundamental-value",
]


@dataclass
class StrategyArchetype:
    """A promoted strategy archetype tracked for diversity."""
    name: str
    category: str
    feature_vector: List[float]   # stored as plain list, not numpy
    description: str
    config_template: Dict[str, Any] = field(default_factory=dict)
    promoted_at: str = ""         # ISO timestamp
    mandate_profile_id: str = ""  # which mandate spawned this

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StrategyArchetype":
        return cls(**{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        })


class StrategyArchetypePool:
    """
    Registry of promoted strategy archetypes.

    JSON persistence. Feature vectors as plain lists.
    Cosine similarity for near-duplicate detection.
    Exclusion context generation for Builder prompt injection.
    """

    def __init__(self, persist_path: str = "data/archetype_pool.json"):
        self.persist_path = persist_path
        self._archetypes: List[StrategyArchetype] = []
        self.load()

    def clear(self) -> None:
        """Clear all archetypes and reset persistence."""
        self._archetypes = []
        self.save()
        logger.info("Archetype pool cleared.")

    # ── CRUD ──────────────────────────────────────────────────────────────

    def register(self, archetype: StrategyArchetype) -> None:
        """Add a new archetype and persist to disk."""
        if not archetype.promoted_at:
            archetype.promoted_at = datetime.utcnow().isoformat()

        self._archetypes.append(archetype)
        self.save()
        logger.info(f"Registered archetype: {archetype.name} ({archetype.category})")

    def list_all(self) -> List[StrategyArchetype]:
        """Return all registered archetypes."""
        return list(self._archetypes)

    def get_by_name(self, name: str) -> Optional[StrategyArchetype]:
        """Look up an archetype by name."""
        for a in self._archetypes:
            if a.name == name:
                return a
        return None

    def count(self) -> int:
        return len(self._archetypes)

    # ── Similarity ────────────────────────────────────────────────────────

    @staticmethod
    def compute_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Cosine similarity via numpy dot product."""
        a = np.array(vec_a, dtype=np.float64)
        b = np.array(vec_b, dtype=np.float64)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a, b) / (norm_a * norm_b))

    def is_too_similar(
        self,
        new_vector: List[float],
        threshold: float = 0.70,
    ) -> bool:
        """Check if a new vector is too similar to any existing archetype."""
        for a in self._archetypes:
            if self.compute_similarity(new_vector, a.feature_vector) > threshold:
                return True
        return False

    def find_most_similar(
        self,
        new_vector: List[float],
    ) -> Optional[tuple]:
        """Find the most similar existing archetype. Returns (archetype, similarity)."""
        if not self._archetypes:
            return None

        best = None
        best_sim = -1.0
        for a in self._archetypes:
            sim = self.compute_similarity(new_vector, a.feature_vector)
            if sim > best_sim:
                best_sim = sim
                best = a

        return (best, best_sim) if best else None

    # ── Builder Prompt Injection ──────────────────────────────────────────

    def get_exclusion_context(self) -> str:
        """
        Generate the prompt context for the Builder.
        Lists existing strategies and identifies underrepresented categories.
        """
        if not self._archetypes:
            return (
                "=== STRATEGY DIVERSITY CONTEXT ===\n"
                "No strategies have been promoted yet. "
                "You have full freedom to explore any strategy type.\n"
                "Available categories: " + ", ".join(STRATEGY_CATEGORIES) + "\n"
            )

        # Count by category
        category_counts: Dict[str, int] = {c: 0 for c in STRATEGY_CATEGORIES}
        existing_descriptions = []

        for a in self._archetypes:
            cat = a.category
            if cat in category_counts:
                category_counts[cat] += 1
            existing_descriptions.append(f"  - {a.name} ({a.category}): {a.description}")

        # Find underrepresented categories
        total = len(self._archetypes)
        underrepresented = [
            cat for cat, count in category_counts.items()
            if count == 0
        ]
        overrepresented = [
            f"{cat} ({count})" for cat, count in category_counts.items()
            if count >= 2
        ]

        lines = [
            "=== STRATEGY DIVERSITY CONTEXT ===",
            f"Existing promoted strategies ({total}):",
        ]
        lines.extend(existing_descriptions)
        lines.append("")

        if underrepresented:
            lines.append(
                f"Underrepresented categories (explore these): "
                f"{', '.join(underrepresented)}"
            )

        if overrepresented:
            lines.append(
                f"Overrepresented categories (avoid unless compelling): "
                f"{', '.join(overrepresented)}"
            )

        lines.append("")
        lines.append(
            "Generate a strategy in a meaningfully different regime or sub-sector "
            "from the existing pool. Diversity drives robustness."
        )

        return "\n".join(lines)

    # ── Persistence ───────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist to JSON. Feature vectors stored as plain lists."""
        os.makedirs(os.path.dirname(self.persist_path) or ".", exist_ok=True)
        data = [a.to_dict() for a in self._archetypes]
        with open(self.persist_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        """Load from JSON if file exists."""
        if not os.path.exists(self.persist_path):
            return
        try:
            with open(self.persist_path, "r") as f:
                data = json.load(f)
            self._archetypes = [StrategyArchetype.from_dict(d) for d in data]
            logger.info(f"Loaded {len(self._archetypes)} archetypes from {self.persist_path}")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to load archetype pool: {e}")
            self._archetypes = []
