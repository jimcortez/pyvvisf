"""ISF shader parser using json5 for robust JSON parsing."""

import re
import json5
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from pydantic import BaseModel, Field, field_validator

from .errors import ISFParseError, ShaderCompilationError
from .types import ISFValue, ISFFloat, ISFInt, coerce_to_isf_value


class ISFInput(BaseModel):
    """ISF input parameter definition."""
    name: Optional[str] = None
    type: Optional[str] = None
    label: Optional[str] = None
    default: Optional[Any] = None
    min: Optional[Any] = None  # PATCH: allow float or list for point2D
    max: Optional[Any] = None  # PATCH: allow float or list for point2D
    values: Optional[List[Any]] = None
    identity: Optional[bool] = None

    @field_validator('type')
    @classmethod
    def validate_type(cls, v, info):
        valid_types = ['bool', 'long', 'float', 'point2D', 'color', 'image', 'audio', 'audioFFT']
        if v not in valid_types:
            raise ValueError(f"Invalid input type: {v}. Must be one of {valid_types}")
        return v

    @field_validator('default')
    @classmethod
    def validate_default(cls, v, info):
        type_value = info.data.get('type') if hasattr(info, 'data') else None
        if v is not None:
            expected_type = type_value if type_value is not None else 'float'
            try:
                coerce_to_isf_value(v, expected_type)
            except ValueError as e:
                raise ValueError(f"Invalid default value for type {expected_type}: {e}")
        return v

    @field_validator('min')
    @classmethod
    def validate_min(cls, v, info):
        type_value = info.data.get('type') if hasattr(info, 'data') else None
        if v is not None:
            if type_value == 'point2D':
                if not (isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)):
                    raise ValueError(f"min for point2D must be a list or tuple of two numbers, got {v}")
            else:
                if not isinstance(v, (int, float)):
                    raise ValueError(f"min for type {type_value} must be a number, got {v}")
        return v

    @field_validator('max')
    @classmethod
    def validate_max(cls, v, info):
        type_value = info.data.get('type') if hasattr(info, 'data') else None
        if v is not None:
            if type_value == 'point2D':
                if not (isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)):
                    raise ValueError(f"max for point2D must be a list or tuple of two numbers, got {v}")
            else:
                if not isinstance(v, (int, float)):
                    raise ValueError(f"max for type {type_value} must be a number, got {v}")
        return v


class ISFPass(BaseModel):
    """ISF render pass definition."""
    target: Optional[str] = None
    persistent: Optional[bool] = None
    float_buffer: Optional[bool] = None  # Renamed from 'float' to avoid shadowing built-in
    width: Optional[int] = None
    height: Optional[int] = None
    scaleX: Optional[float] = None
    scaleY: Optional[float] = None
    scaleToFit: Optional[bool] = None
    scaleToFill: Optional[bool] = None
    scaleToFitX: Optional[bool] = None
    scaleToFitY: Optional[bool] = None
    scaleToFillX: Optional[bool] = None
    scaleToFillY: Optional[bool] = None
    scaleToFitAspectRatio: Optional[bool] = None
    scaleToFillAspectRatio: Optional[bool] = None
    filter: Optional[str] = None


class ISFMetadata(BaseModel):
    """ISF shader metadata."""
    name: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    license: Optional[str] = None
    homepage: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    # ISF-specific fields
    inputs: Any = None
    passes: Any = None
    imports: Optional[Dict[str, Any]] = None
    # Render settings
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[float] = None
    # Shader info
    vertex_shader: Optional[str] = None
    fragment_shader: Optional[str] = None
    
    @field_validator('inputs')
    @classmethod
    def validate_inputs(cls, v, info):
        if v is not None:
            names = [input_.name for input_ in v]
            if len(names) != len(set(names)):
                raise ValueError("Input names must be unique")
        return v

    @field_validator('passes')
    @classmethod
    def validate_passes(cls, v, info):
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("PASSES must be a list of pass objects.")
        allowed_fields = {
            'target', 'persistent', 'float_buffer', 'width', 'height', 'scaleX', 'scaleY',
            'scaleToFit', 'scaleToFill', 'scaleToFitX', 'scaleToFitY', 'scaleToFillX',
            'scaleToFillY', 'scaleToFitAspectRatio', 'scaleToFillAspectRatio', 'filter'
        }
        target_names = set()
        for i, p in enumerate(v):
            if not isinstance(p, ISFPass):
                raise ValueError(f"Each pass must be an ISFPass object (got {type(p)} at index {i}).")
            # Runtime check: get all fields present in the ISFPass instance
            for field in p.__dict__.keys():
                if field not in allowed_fields:
                    raise ValueError(f"Invalid field '{field}' in PASSES[{i}]. Allowed fields: {sorted(allowed_fields)}")
            # TARGET validation
            if p.target is not None:
                if not isinstance(p.target, str):
                    raise ValueError(f"PASSES[{i}]: TARGET must be a string if present.")
                if p.target in target_names:
                    raise ValueError(f"Duplicate TARGET name '{p.target}' in PASSES.")
                target_names.add(p.target)
            # WIDTH/HEIGHT validation
            for dim in ('width', 'height'):
                val = getattr(p, dim)
                if val is not None:
                    if isinstance(val, (int, float)):
                        if val <= 0:
                            raise ValueError(f"PASSES[{i}]: {dim.upper()} must be positive if specified.")
                    elif isinstance(val, str):
                        # Accept ISF expressions like "$WIDTH/2.0"
                        if not val.startswith('$'):
                            raise ValueError(f"PASSES[{i}]: {dim.upper()} string must start with '$' for ISF expressions.")
                    else:
                        raise ValueError(f"PASSES[{i}]: {dim.upper()} must be a number or ISF expression string.")
            # PERSISTENT/FLOAT_BUFFER validation
            for bfield in ('persistent', 'float_buffer'):
                bval = getattr(p, bfield)
                if bval is not None and not isinstance(bval, bool):
                    raise ValueError(f"PASSES[{i}]: {bfield.upper()} must be a boolean if specified.")
            # FILTER validation
            if p.filter is not None and not isinstance(p.filter, str):
                raise ValueError(f"PASSES[{i}]: FILTER must be a string if specified.")
        if len(v) == 0:
            raise ValueError("PASSES must contain at least one pass object.")
        return v


class ISFParser:
    """Parser for ISF shader files using json5."""
    
    def __init__(self):
        self.json_pattern = re.compile(r'/\*\{([\s\S]*?)\}\*/?')  # non-greedy, match first only
    
    def parse_file(self, file_path: str) -> Tuple[str, ISFMetadata]:
        """Parse an ISF shader file and return GLSL code and metadata."""
        path = Path(file_path)
        if not path.exists():
            raise ISFParseError(f"Shader file not found: {file_path}")
        
        content = path.read_text(encoding='utf-8')
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> Tuple[str, ISFMetadata]:
        """Parse ISF shader content and return GLSL code and metadata."""
        # Extract JSON metadata blocks
        json_blocks = self.json_pattern.findall(content)

        if not json_blocks:
            # No metadata found, raise ISFParseError
            raise ISFParseError(
                "No ISF JSON metadata block found in shader content.",
                json_block=""
            )

        # Parse the first JSON block (ISF uses the first one)
        # Add braces back since the regex captures content without them
        json_content = "{" + json_blocks[0] + "}"
        try:
            metadata_dict = json5.loads(json_content)
        except (ValueError, TypeError) as e:
            raise ISFParseError(
                f"Failed to parse ISF JSON metadata: {e}",
                json_block=json_blocks[0],
                line_info={'line': self._find_json_line(content, json_blocks[0])}
            )

        # Remove JSON blocks from GLSL content
        glsl_content = self.json_pattern.sub('', content)

        # Parse metadata
        try:
            metadata = self._parse_metadata(metadata_dict)
        except Exception as e:
            raise ShaderCompilationError(f"Failed to compile shader due to invalid ISF metadata: {e}") from e

        return glsl_content, metadata
    
    def _parse_metadata(self, metadata_dict) -> ISFMetadata:
        """Parse metadata dictionary into ISFMetadata object."""
        try:
            # Handle inputs
            inputs = None
            if 'INPUTS' in metadata_dict:
                inputs = []
                for input_data in metadata_dict['INPUTS']:
                    if isinstance(input_data, dict):
                        # Convert ISF uppercase field names to lowercase
                        converted_input = {
                            'name': input_data.get('NAME', None),
                            'type': input_data.get('TYPE', None),
                            'default': input_data.get('DEFAULT', None),
                            'min': input_data.get('MIN', None),
                            'max': input_data.get('MAX', None),
                            'label': input_data.get('LABEL', None),
                            'values': input_data.get('VALUES', None),
                            'identity': input_data.get('IDENTITY', None)
                        }
                        # Only pass fields that are in ISFInput
                        input_fields = {k: v for k, v in converted_input.items() if k in ISFInput.__annotations__}
                        inputs.append(ISFInput(**input_fields))
                    else:
                        # Handle string-only input definitions
                        inputs.append(ISFInput(name=input_data, type='float'))
            
            # Handle passes
            passes = None
            if 'PASSES' in metadata_dict:
                passes = []
                for pass_data in metadata_dict['PASSES']:
                    if isinstance(pass_data, dict):
                        # Convert ISF uppercase field names to lowercase
                        converted_pass = {
                            'target': pass_data.get('TARGET'),
                            'width': pass_data.get('WIDTH'),
                            'height': pass_data.get('HEIGHT'),
                            'persistent': pass_data.get('PERSISTENT'),
                            'float_buffer': pass_data.get('FLOAT') or pass_data.get('FLOAT_BUFFER'),
                            'filter': pass_data.get('FILTER')
                        }
                        # Remove None values
                        converted_pass = {k: v for k, v in converted_pass.items() if v is not None}
                        isf_pass = ISFPass(**converted_pass)
                        passes.append(isf_pass)
                    else:
                        # Handle string-only pass definitions
                        isf_pass = ISFPass(target=pass_data)
                        passes.append(isf_pass)
            
            # Handle imports - convert list to dict if needed
            imports = metadata_dict.get('IMPORTED')
            if isinstance(imports, list):
                # Convert list of import objects to dict
                imports_dict = {}
                for import_item in imports:
                    if isinstance(import_item, dict):
                        name = import_item.get('NAME')
                        if name:
                            imports_dict[name] = import_item
                    elif isinstance(import_item, str):
                        imports_dict[import_item] = {'NAME': import_item}
                imports = imports_dict
            
            # Create metadata object
            metadata = ISFMetadata(
                name=metadata_dict.get('NAME'),
                description=metadata_dict.get('DESCRIPTION'),
                author=metadata_dict.get('AUTHOR'),
                version=metadata_dict.get('VERSION'),
                license=metadata_dict.get('LICENSE'),
                homepage=metadata_dict.get('HOMEPAGE'),
                category=metadata_dict.get('CATEGORY'),
                tags=metadata_dict.get('TAGS'),
                inputs=inputs,
                passes=passes,
                imports=imports,
                width=metadata_dict.get('WIDTH'),
                height=metadata_dict.get('HEIGHT'),
                aspect_ratio=metadata_dict.get('ASPECT_RATIO'),
                vertex_shader=metadata_dict.get('VERTEX_SHADER'),
                fragment_shader=metadata_dict.get('FRAGMENT_SHADER'),
            )
            
            return metadata
            
        except Exception as e:
            raise ShaderCompilationError(f"Failed to compile shader due to invalid ISF metadata: {e}") from e
    
    def _find_json_line(self, content: str, json_block: str) -> Optional[int]:
        """Find the line number where JSON block starts."""
        try:
            start_pos = content.find(f'/*{{{json_block}}}*/')
            if start_pos == -1:
                return None
            
            return content.count('\n', 0, start_pos) + 1
        except:
            return None
    
    def validate_inputs(self, metadata: ISFMetadata, input_values: Dict[str, Any]) -> Dict[str, ISFValue]:
        """Validate and coerce input values according to metadata."""
        if not metadata.inputs:
            return {}
        
        validated_inputs = {}
        
        for input_def in metadata.inputs:
            input_name = input_def.name
            
            if input_name in input_values:
                value = input_values[input_name]
                try:
                    # Coerce to proper type
                    expected_type = input_def.type if input_def.type is not None else 'float'
                    validated_value = coerce_to_isf_value(value, expected_type)
                    # Validate ranges for numeric types
                    if isinstance(validated_value, (ISFFloat, ISFInt)):
                        if input_def.min is not None and validated_value.value < input_def.min:
                            raise ShaderCompilationError(
                                f"Value {validated_value.value} is below minimum {input_def.min} for input '{input_name}'"
                            )
                        if input_def.max is not None and validated_value.value > input_def.max:
                            raise ShaderCompilationError(
                                f"Value {validated_value.value} is above maximum {input_def.max} for input '{input_name}'"
                            )
                    validated_inputs[input_name] = validated_value
                except ValueError as e:
                    raise ShaderCompilationError(
                        f"Invalid value for input '{input_name}': {e}"
                    )
            elif input_def.default is not None:
                # Use default value
                expected_type = input_def.type if input_def.type is not None else 'float'
                validated_inputs[input_name] = coerce_to_isf_value(input_def.default, expected_type)
        
        return validated_inputs 