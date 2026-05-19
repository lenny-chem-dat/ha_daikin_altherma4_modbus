"""Register definition dataclasses for type-safe Modbus register handling."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Union

from homeassistant.const import EntityCategory

__all__ = [
    "RegisterDefinition",
    "RegisterDataType",
    "SensorRegister",
    "SwitchRegister",
    "NumberRegister",
    "SelectRegister",
    "CalculatedRegister",
    "TEMP16",
    "INT16",
    "INT16S100",
    "TEXT16",
    "POW16",
    "BIT",
    "TIMESTAMP16",
]


@dataclass
class RegisterDataType:
    """Data type definition for Modbus registers with scaling and range information."""

    name: str
    signed: bool
    bits: int
    scaling: Union[int, float]
    range: Optional[Tuple[Union[int, float], Union[int, float]]] = None


# Predefined register data types
TEMP16 = RegisterDataType(
    name="Temp16", signed=True, bits=16, scaling=0.01, range=(-327.68, 327.67)
)

INT16 = RegisterDataType(
    name="Int16", signed=True, bits=16, scaling=1, range=(-32768, 32767)
)

INT16S100 = RegisterDataType(
    name="Int16", signed=True, bits=16, scaling=0.01, range=(-32768, 32767)
)

TEXT16 = RegisterDataType(name="Text16", signed=False, bits=16, scaling=1, range=None)

POW16 = RegisterDataType(
    name="Pow16", signed=True, bits=16, scaling=0.01, range=(-327.68, 327.67)
)

BIT = RegisterDataType(name="Bit", signed=False, bits=1, scaling=1, range=(0, 1))

TIMESTAMP16 = RegisterDataType(
    name="Timestamp16", signed=False, bits=16, scaling=1, range=(0, 65535)
)


@dataclass
class RegisterDefinition:
    """Base class for all register definitions."""

    name: str
    address: int
    input_type: str
    register_name: str
    data_type: RegisterDataType
    calc_type: Optional[str] = None  # For calculated registers
    trigger_register_name: Optional[str] = None  # For calculated registers

    # Optional fields with defaults
    unit: Optional[str] = None
    device_class: Optional[str] = None
    icon: Optional[str] = None
    translation_key: Optional[str] = None
    entity_category: Optional[EntityCategory] = None
    step: Optional[Union[int, float]] = None


@dataclass
class SensorRegister(RegisterDefinition):
    """Register definition for sensor entities."""

    count: int = 1
    enum_map: Optional[Dict[int, str]] = None
    unique_id: Optional[str] = None


@dataclass
class SwitchRegister(RegisterDefinition):
    """Register definition for switch entities."""

    enum_map: Optional[Dict[int, str]] = None


@dataclass
class NumberRegister(RegisterDefinition):
    """Register definition for number entities."""

    min_value: Union[int, float] = 0
    max_value: Union[int, float] = 100
    step: Union[int, float] = 1
    enum_map: Optional[Dict[int, str]] = None


@dataclass
class SelectRegister(RegisterDefinition):
    """Register definition for select entities."""

    enum_map: Dict[int, str] = field(default_factory=dict)
    min_value: Union[int, float] = 0
    max_value: Union[int, float] = 100
    step: Union[int, float] = 1


@dataclass
class CalculatedRegister(RegisterDefinition):
    """Register definition for calculated sensors."""

    pass  # All fields are in base class
