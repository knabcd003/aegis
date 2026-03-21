from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel
from hashlib import sha256
import json
from typing import Type, Optional


class HealthStatus:
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"


@dataclass
class HealthResult:
    status: str
    reason: Optional[str] = None
    latency_ms: Optional[float] = None


class ComponentRole(str, Enum):
    DATA_SOURCE = "data_source"
    SIGNAL_GENERATOR = "signal_generator"
    GATE_CONDITION = "gate_condition"
    CONTEXT_MODIFIER = "context_modifier"
    RISK_OVERRIDE = "risk_override"
    AUDITOR = "auditor"
    SCENARIO_GENERATOR = "scenario_generator"
    EXECUTOR = "executor"


class VCLComponent(ABC):
    @property
    @abstractmethod
    def component_id(self) -> str:
        """Unique identifier for the component."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version of the component."""
        pass

    @property
    @abstractmethod
    def role(self) -> ComponentRole:
        """The role this component plays in the pipeline."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Type[BaseModel]:
        """Pydantic model defining the expected input structure."""
        pass

    @property
    @abstractmethod
    def output_schema(self) -> Type[BaseModel]:
        """Pydantic model defining the guaranteed output structure."""
        pass

    @abstractmethod
    def execute(self, input_data: BaseModel) -> BaseModel:
        """Execute the component's core logic."""
        pass

    @abstractmethod
    def health(self) -> HealthResult:
        """Check the component's health. Must complete within 5 seconds."""
        pass

    @property
    def compatibility_fingerprint(self) -> str:
        """
        Generates a deterministic footprint of the input and output schemas.
        Allows for drag-and-drop compatibility checking in the visual interface.
        """
        combined = (
            json.dumps(self.input_schema.model_json_schema(), sort_keys=True) +
            json.dumps(self.output_schema.model_json_schema(), sort_keys=True)
        )
        return sha256(combined.encode()).hexdigest()[:16]

    def describe(self) -> str:
        return f"{self.component_id} v{self.version} ({self.role})"
