"""Hairpin runtime value types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hairpin.bytecode import BytecodeProgram


class HairpinError(Exception):
    """Base error for all Hairpin runtime errors."""
    pass


class HValue:
    """Base class for all Hairpin values."""

    def to_bool(self) -> bool:
        raise NotImplementedError

    def type_name(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class HInt(HValue):
    value: int

    def to_bool(self) -> bool:
        return self.value != 0

    def type_name(self) -> str:
        return "integer"

    def __repr__(self):
        return f"HInt({self.value})"


@dataclass(frozen=True)
class HFloat(HValue):
    value: float

    def to_bool(self) -> bool:
        return self.value != 0.0

    def type_name(self) -> str:
        return "float"

    def __repr__(self):
        return f"HFloat({self.value})"


@dataclass(frozen=True)
class HString(HValue):
    value: str

    def to_bool(self) -> bool:
        return self.value != ""

    def type_name(self) -> str:
        return "string"

    def __repr__(self):
        return f"HString({self.value!r})"


@dataclass(frozen=True)
class HBool(HValue):
    value: bool

    def to_bool(self) -> bool:
        return self.value

    def type_name(self) -> str:
        return "boolean"

    def __repr__(self):
        return f"HBool({self.value})"


@dataclass
class HCode(HValue):
    instructions: list
    source_line: int = 0
    bytecode: BytecodeProgram | None = None

    def to_bool(self) -> bool:
        return len(self.instructions) > 0

    def type_name(self) -> str:
        return "code"

    def __repr__(self):
        return f"HCode(<{len(self.instructions)} instructions>)"


class HNil(HValue):
    """The nil value — empty list, falsy."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def to_bool(self) -> bool:
        return False

    def type_name(self) -> str:
        return "nil"

    def __repr__(self):
        return "HNil()"

    def __eq__(self, other):
        return isinstance(other, HNil)

    def __hash__(self):
        return hash("nil")


# Singleton
NIL = HNil()


@dataclass(frozen=True)
class HCons(HValue):
    head: HValue
    tail: HValue

    def to_bool(self) -> bool:
        return True

    def type_name(self) -> str:
        return "cons"

    def __repr__(self):
        return f"HCons({self.head!r}, {self.tail!r})"
