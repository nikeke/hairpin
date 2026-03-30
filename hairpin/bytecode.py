"""Hairpin bytecode compiler for cached HCode execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from hairpin.parser import PushLiteral, WordRef
from hairpin.types import HCode

OP_PUSH_LITERAL = 0
OP_CALL_PRIMITIVE = 1
OP_LOAD_NAME = 2
OP_LOAD_NAME_TAIL = 3
OP_TCO_EXEC = 4
OP_TCO_IF = 5
OP_TCO_IF_ELSE = 6


@dataclass(frozen=True)
class BytecodeProgram:
    code: HCode
    ops: tuple[object, ...]


def compile_hcode(code: HCode, primitives: dict[str, Callable]) -> BytecodeProgram:
    """Compile an HCode instruction list into a compact bytecode stream."""
    if code.bytecode is not None:
        return code.bytecode

    ops: list[object] = []
    last_index = len(code.instructions) - 1

    for index, instr in enumerate(code.instructions):
        is_last = index == last_index
        if isinstance(instr, PushLiteral):
            value = instr.value
            if isinstance(value, HCode):
                compile_hcode(value, primitives)
            ops.append(OP_PUSH_LITERAL)
            ops.append(value)
            continue

        name = instr.name
        if is_last:
            if name == "exec":
                ops.append(OP_TCO_EXEC)
                continue
            if name == "if":
                ops.append(OP_TCO_IF)
                continue
            if name == "if-else":
                ops.append(OP_TCO_IF_ELSE)
                continue

        primitive = primitives.get(name)
        if primitive is not None:
            ops.append(OP_CALL_PRIMITIVE)
            ops.append(primitive)
            continue

        ops.append(OP_LOAD_NAME_TAIL if is_last else OP_LOAD_NAME)
        ops.extend((name, instr.line, instr.col))

    program = BytecodeProgram(code=code, ops=tuple(ops))
    code.bytecode = program
    return program
