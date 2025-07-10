"""ISF value types for shader inputs."""

from dataclasses import dataclass
from typing import Union, Tuple, List, Any
import numpy as np


@dataclass
class ISFValue:
    """Base class for ISF values."""
    pass


@dataclass
class ISFColor(ISFValue):
    """RGBA color value."""
    r: float
    g: float
    b: float
    a: float = 1.0
    
    def __post_init__(self):
        # Clamp values to [0, 1]
        self.r = max(0.0, min(1.0, float(self.r)))
        self.g = max(0.0, min(1.0, float(self.g)))
        self.b = max(0.0, min(1.0, float(self.b)))
        self.a = max(0.0, min(1.0, float(self.a)))
    
    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Convert to RGBA tuple."""
        return (self.r, self.g, self.b, self.a)
    
    def to_list(self) -> List[float]:
        """Convert to RGBA list."""
        return [self.r, self.g, self.b, self.a]
    
    @classmethod
    def from_rgb(cls, r: float, g: float, b: float, a: float = 1.0) -> 'ISFColor':
        """Create from RGB values."""
        return cls(r, g, b, a)
    
    @classmethod
    def from_tuple(cls, color_tuple: Union[Tuple[float, ...], List[float]]) -> 'ISFColor':
        """Create from tuple or list."""
        if len(color_tuple) == 3:
            return cls(color_tuple[0], color_tuple[1], color_tuple[2], 1.0)
        elif len(color_tuple) == 4:
            return cls(color_tuple[0], color_tuple[1], color_tuple[2], color_tuple[3])
        else:
            raise ValueError(f"Color tuple must have 3 or 4 values, got {len(color_tuple)}")


@dataclass
class ISFPoint2D(ISFValue):
    """2D point value."""
    x: float
    y: float
    
    def __post_init__(self):
        self.x = float(self.x)
        self.y = float(self.y)
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to (x, y) tuple."""
        return (self.x, self.y)
    
    def to_list(self) -> List[float]:
        """Convert to [x, y] list."""
        return [self.x, self.y]
    
    @classmethod
    def from_tuple(cls, point_tuple: Union[Tuple[float, float], List[float]]) -> 'ISFPoint2D':
        """Create from tuple or list."""
        if len(point_tuple) != 2:
            raise ValueError(f"Point tuple must have 2 values, got {len(point_tuple)}")
        return cls(point_tuple[0], point_tuple[1])


@dataclass
class ISFFloat(ISFValue):
    """Float value."""
    value: float
    
    def __post_init__(self):
        self.value = float(self.value)
    
    def __float__(self) -> float:
        return self.value
    
    def __int__(self) -> int:
        return int(self.value)


@dataclass
class ISFInt(ISFValue):
    """Integer value."""
    value: int
    
    def __post_init__(self):
        self.value = int(self.value)
    
    def __int__(self) -> int:
        return self.value
    
    def __float__(self) -> float:
        return float(self.value)


@dataclass
class ISFBool(ISFValue):
    """Boolean value."""
    value: bool
    
    def __post_init__(self):
        self.value = bool(self.value)
    
    def __bool__(self) -> bool:
        return self.value


# Type aliases for convenience
ISFColorVal = ISFColor
ISFPoint2DVal = ISFPoint2D
ISFFloatVal = ISFFloat
ISFLongVal = ISFInt
ISFBoolVal = ISFBool

# Union type for all ISF values
ISFValueType = Union[ISFColor, ISFPoint2D, ISFFloat, ISFInt, ISFBool, float, int, bool, Tuple[float, ...], List[float]]


def coerce_to_isf_value(value: Any, expected_type: str = "auto") -> ISFValue:
    """Coerce a Python value to an ISF value type."""
    
    # If it's already an ISF value, return it
    if isinstance(value, ISFValue):
        return value
    
    # Auto-coercion based on type and value
    if expected_type == "auto":
        if isinstance(value, (tuple, list)):
            if len(value) == 2:
                return ISFPoint2D.from_tuple(value)
            elif len(value) in (3, 4):
                return ISFColor.from_tuple(value)
            else:
                raise ValueError(f"Cannot auto-coerce {len(value)}-element sequence (got {value!r}). Primitives like int, float, bool, list, or tuple are allowed and will be coerced to the appropriate ISF type if possible.")
        elif isinstance(value, bool):
            return ISFBool(value)
        elif isinstance(value, int):
            return ISFInt(value)
        elif isinstance(value, float):
            return ISFFloat(value)
        else:
            raise ValueError(f"Cannot auto-coerce value of type {type(value)} (got {value!r}). Primitives like int, float, bool, list, or tuple are allowed and will be coerced to the appropriate ISF type if possible.")
    
    # Explicit type coercion
    elif expected_type == "color":
        if isinstance(value, (tuple, list)):
            return ISFColor.from_tuple(value)
        else:
            raise ValueError(f"Cannot coerce value of type {type(value)} (got {value!r}) to color. Primitives like list or tuple of 3 or 4 floats are allowed.")
    
    elif expected_type == "point2D":
        if isinstance(value, (tuple, list)):
            return ISFPoint2D.from_tuple(value)
        else:
            raise ValueError(f"Cannot coerce value of type {type(value)} (got {value!r}) to point2D. Primitives like list or tuple of 2 floats are allowed.")
    
    elif expected_type == "float":
        return ISFFloat(value)
    
    elif expected_type == "long":
        return ISFInt(value)
    
    elif expected_type == "bool":
        return ISFBool(value)
    
    else:
        raise ValueError(f"Unknown expected type: {expected_type}") 