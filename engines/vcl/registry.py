import time
from typing import Dict, Any, get_origin, get_args
from pydantic import BaseModel, ValidationError

from engines.vcl.component import VCLComponent, HealthStatus, ComponentRole

class GateResult:
    def __init__(self, passed: bool, reason: str = None):
        self.passed = passed
        self.reason = reason


class RegistrationResult:
    def __init__(self, success: bool, failed_gate: str = None, reason: str = None):
        self.success = success
        self.failed_gate = failed_gate
        self.reason = reason


class VCLRegistry:
    def __init__(self):
        self._components: Dict[str, VCLComponent] = {}
        
    def register(self, component: VCLComponent) -> RegistrationResult:
        gates = [
            self._gate_schema_compilation,
            self._gate_health_check,
            self._gate_contract_tests,
            self._gate_security_scan,
            self._gate_canary_test,
        ]
        
        for gate in gates:
            result = gate(component)
            if not result.passed:
                return RegistrationResult(
                    success=False,
                    failed_gate=gate.__name__,
                    reason=result.reason
                )
                
        self._persist(component)
        return RegistrationResult(success=True)

    def _persist(self, component: VCLComponent) -> None:
        requires_human_signoff = component.role in (ComponentRole.RISK_OVERRIDE, ComponentRole.EXECUTOR)
        self._components[component.component_id] = component
        # In a real system, this might write to a DB or manifest file.
        # Here we just store it in memory for the session.
        component.__dict__['_vcl_requires_human_signoff'] = requires_human_signoff

    def _gate_schema_compilation(self, component: VCLComponent) -> GateResult:
        """Verify schemas are valid Pydantic models."""
        try:
            if not issubclass(component.input_schema, BaseModel):
                return GateResult(False, "input_schema is not a subclass of pydantic.BaseModel")
            if not issubclass(component.output_schema, BaseModel):
                return GateResult(False, "output_schema is not a subclass of pydantic.BaseModel")
        except TypeError:
            return GateResult(False, "Schemas must be classes, not instances")
            
        return GateResult(True)

    def _gate_health_check(self, component: VCLComponent) -> GateResult:
        """Verify health() executes within 5 seconds and returns a valid status."""
        start_time = time.time()
        try:
            health = component.health()
        except Exception as e:
            return GateResult(False, f"health() raised exception: {str(e)}")
            
        duration = time.time() - start_time
        if duration > 5.0:
            return GateResult(False, f"health() exceeded 5 second timeout ({duration:.2f}s)")
            
        if not hasattr(health, 'status') or health.status not in (HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.OFFLINE):
            return GateResult(False, f"health() returned invalid status: {getattr(health, 'status', None)}")
            
        return GateResult(True)

    def _generate_minimal_valid_dict(self, schema: type[BaseModel]) -> Dict[str, Any]:
        """Recursively generates a valid minimal dictionary for a Pydantic model."""
        data = {}
        for name, field in schema.model_fields.items():
            if not field.is_required():
                continue
                
            # Basic type handling
            annotation = field.annotation
            origin = get_origin(annotation)
            
            if origin is list or origin is set:
                data[name] = []
            elif origin is dict:
                data[name] = {}
            elif origin is tuple:
                args = get_args(annotation)
                # Just filling with defaults for the tuple size
                data[name] = tuple(self._get_default_for_type(t) for t in args)
            else:
                data[name] = self._get_default_for_type(annotation)
                
        return data

    def _get_default_for_type(self, t: Any) -> Any:
        try:
            if issubclass(t, BaseModel):
                return self._generate_minimal_valid_dict(t)
        except TypeError:
            pass
            
        import datetime
        if t is str:
            return "a"
        if t is int:
            return 1
        if t is float:
            return 1.0
        if t is bool:
            return False
        if t is datetime.datetime:
            return datetime.datetime.utcnow().isoformat()
        if t is datetime.date:
            return datetime.date.today().isoformat()
        return None

    def _generate_minimal_valid_dict(self, schema: type[BaseModel]) -> Dict[str, Any]:
        """Recursively generates a valid minimal dictionary for a Pydantic model."""
        data = {}
        for name, field in schema.model_fields.items():
            if not field.is_required() and field.default is not None:
                # If there's a default, maybe just use it or skip. The instruction says minimal valid payload.
                pass
                
            annotation = field.annotation
            origin = get_origin(annotation)
            
            if origin is list or origin is set:
                args = get_args(annotation)
                elem_type = args[0] if args else str
                val = [self._get_default_for_type(elem_type)]
                data[name] = val if origin is list else set(val)
            elif origin is dict:
                data[name] = {}
            elif origin is tuple:
                args = get_args(annotation)
                data[name] = tuple(self._get_default_for_type(t) for t in args)
            else:
                data[name] = self._get_default_for_type(annotation)
                
        return data

    def _gate_contract_tests(self, component: VCLComponent) -> GateResult:
        """
        Dynamically generate an input payload using annotations, validate it with 
        input_schema.model_validate(), run execute(), and validate the output.
        """
        try:
            raw_input = self._generate_minimal_valid_dict(component.input_schema)
            # Use model_validate instead of model_construct to actually run validators
            validated_input = component.input_schema.model_validate(raw_input)
        except Exception as e:
            return GateResult(False, f"Failed to construct valid input for contract test: {str(e)}")
            
        try:
            result = component.execute(validated_input)
        except Exception as e:
            return GateResult(False, f"execute() crashed on minimal valid input: {str(e)}")
            
        try:
            # Re-serialize and validate to ensure it strictly matches output_schema
            if not isinstance(result, component.output_schema):
                return GateResult(False, f"execute() returned type {type(result)}, expected {component.output_schema}")
            # Ensure it passes all validators
            component.output_schema.model_validate(result.model_dump())
        except Exception as e:
            return GateResult(False, f"Output failed schema validation: {str(e)}")
            
        return GateResult(True)

    def _gate_security_scan(self, component: VCLComponent) -> GateResult:
        # TODO: implement SCA, dependency scan, secrets detection
        return GateResult(True)

    def _gate_canary_test(self, component: VCLComponent) -> GateResult:
        """
        Pass a dictionary with one wrong type and one missing required field.
        Verify that input_schema.model_validate() raises ValidationError.
        """
        if not component.input_schema.model_fields:
            # If there's no fields, we can't do a missing field test easily. Skip or just test wrong type.
            return GateResult(True)
            
        bad_input = {}
        fields = list(component.input_schema.model_fields.items())
        
        # Missing required field (we just omit the first required field we find)
        required_fields = [k for k, v in fields if v.is_required()]
        
        # Wrong type for one field
        for name, field in fields:
            if field.annotation is str:
                bad_input[name] = 12345
            elif field.annotation is int or field.annotation is float:
                bad_input[name] = "not_a_number"
            else:
                bad_input[name] = 12345  # Just shove a number in there
                
        # If there's a required field, explicitly remove one
        if required_fields:
            bad_input.pop(required_fields[0], None)
            
        try:
            # This SHOULD raise a ValidationError
            component.input_schema.model_validate(bad_input)
            return GateResult(False, "Canary test failed: Component input_schema accepted malformed data without raising ValidationError.")
        except ValidationError:
            return GateResult(True)
        except Exception as e:
            return GateResult(False, f"Canary test raised unexpected exception instead of ValidationError: type={type(e).__name__}, msg={str(e)}")
