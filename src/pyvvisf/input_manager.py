"""Input validation and management utilities."""

from typing import Dict, Any, Optional
import logging

from .parser import ISFParser, ISFMetadata
from .types import ISFValue
from .errors import RenderingError

logger = logging.getLogger(__name__)


class InputManager:
    """Manages shader input validation, coercion, and storage."""
    
    def __init__(self, parser: ISFParser):
        self.parser = parser
        self.input_values: Dict[str, Any] = {}
    
    def set_input(self, name: str, value: Any, metadata: ISFMetadata):
        """Set and validate a single shader input."""
        if not metadata or not metadata.inputs:
            raise RenderingError("No shader loaded or shader has no inputs.")
            
        # Find input definition
        input_def = next((inp for inp in metadata.inputs if inp.name == name), None)
        if input_def is None:
            raise RenderingError(f"Input '{name}' not found in shader inputs.")
            
        try:
            # Validate and coerce value
            validated = self.parser.validate_inputs(metadata, {name: value})
            coerced_value = validated[name]
        except Exception as e:
            raise RenderingError(f"Failed to set input '{name}': {e}")
            
        # Store the validated value
        self.input_values[name] = coerced_value
    
    def set_inputs(self, inputs: Dict[str, Any], metadata: ISFMetadata):
        """Set multiple shader inputs at once."""
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary of input names to values")
            
        for name, value in inputs.items():
            self.set_input(name, value, metadata)
    
    def get_merged_inputs(self, user_inputs: Optional[Dict[str, Any]], metadata: ISFMetadata) -> Dict[str, ISFValue]:
        """Get merged inputs combining user inputs with defaults."""
        # Start with stored input values
        merged_inputs = dict(self.input_values)
        
        # Add user inputs
        if user_inputs:
            merged_inputs.update(user_inputs)
            
        # Add defaults from metadata for missing inputs
        if metadata and metadata.inputs:
            for input_def in metadata.inputs:
                if input_def.name not in merged_inputs and input_def.default is not None:
                    merged_inputs[input_def.name] = input_def.default
        
        # Validate all inputs
        if metadata and merged_inputs:
            return self.parser.validate_inputs(metadata, merged_inputs)
        else:
            return {}
    
    def clear_inputs(self):
        """Clear all stored input values."""
        self.input_values.clear()
    
    def get_stored_inputs(self) -> Dict[str, Any]:
        """Get a copy of currently stored input values."""
        return dict(self.input_values)