import hashlib
import json
from uuid import uuid4
from pydantic import ValidationError

from config.schema import AegisConfig

class ConfigValidationError(Exception):
    """Raised when config JSON fails Pydantic validation."""
    pass


class ConfigManager:
    """Manages parsing, validating, and fingerprinting JSON experiment configs."""
    
    @staticmethod
    def _generate_fingerprint(data: dict) -> str:
        """Deterministic SHA256 of the dictionary."""
        # Sort keys to ensure determinism
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    @classmethod
    def load(cls, file_path: str) -> AegisConfig:
        """Load from a JSON file, validate, and return the Config object."""
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.load_dict(data)
        
    @classmethod
    def load_dict(cls, data: dict) -> AegisConfig:
        """Load from a dictionary, validate, and return the Config object."""
        fingerprint = cls._generate_fingerprint(data)
        
        # FIX 3: Deprecation check for finbert_above
        signal_gate = data.get("signal_gate", {})
        if isinstance(signal_gate, dict) and "finbert_above" in signal_gate:
            import warnings
            warnings.warn(
                "'finbert_above' is deprecated in SignalGateConfig. "
                "Please migrate to the 'finbert_sentiment_gate' VCL component in the signal_pipeline.",
                DeprecationWarning,
                stacklevel=2
            )
            # Remove from data to allow Pydantic validation to pass against the new schema
            del signal_gate["finbert_above"]

        try:

            config = AegisConfig(**data)
            config.fingerprint = fingerprint
            config.run_id = str(uuid4())
            return config
        except ValidationError as e:
            # Flatten pydantic errors into a readable string showing the missing fields
            errors = []
            for err in e.errors():
                loc = ".".join([str(loc) for loc in err["loc"]])
                msg = err["msg"]
                errors.append(f"{loc}: {msg}")
            
            raise ConfigValidationError(f"Invalid Config:\n" + "\n".join(errors))
