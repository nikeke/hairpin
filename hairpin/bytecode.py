"""Hairpin bytecode compiler for cached HCode execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from hairpin.parser import PushLiteral, WordRef
from hairpin.types import HCode, HString

OP_PUSH_LITERAL = 0
OP_CALL_PRIMITIVE = 1
OP_LOAD_NAME = 2
OP_LOAD_NAME_TAIL = 3
OP_TCO_EXEC = 4
OP_TCO_IF = 5
OP_TCO_IF_ELSE = 6
OP_SET_LITERAL_NAME = 7
OP_DEF_LITERAL_NAME = 8
OP_GET_LITERAL_NAME = 9
OP_ADD = 10
OP_SUB = 11
OP_MUL = 12
OP_DIV = 13
OP_MOD = 14
OP_EQ = 15
OP_NE = 16
OP_LT = 17
OP_LE = 18
OP_GT = 19
OP_GE = 20
OP_DUP = 21
OP_DROP = 22
OP_SWAP = 23
OP_CONS = 24
OP_HEAD = 25
OP_TAIL = 26

SPECIALIZED_PRIMITIVES = {
    "+": OP_ADD,
    "-": OP_SUB,
    "*": OP_MUL,
    "/": OP_DIV,
    "%": OP_MOD,
    "==": OP_EQ,
    "!=": OP_NE,
    "<": OP_LT,
    "<=": OP_LE,
    ">": OP_GT,
    ">=": OP_GE,
    "dup": OP_DUP,
    "drop": OP_DROP,
    "swap": OP_SWAP,
    "cons": OP_CONS,
    "head": OP_HEAD,
    "tail": OP_TAIL,
}

@dataclass(frozen=True)
class BytecodeProgram:
    code: HCode
    ops: tuple[object, ...]


@dataclass(slots=True)
class NameLoadOp:
    name: str
    line: int
    col: int


def compile_hcode(code: HCode, primitives: dict[str, Callable]) -> BytecodeProgram:
    """Compile an HCode instruction list into a compact bytecode stream."""
    if code.bytecode is not None:
        return code.bytecode

    ops: list[object] = []
    instructions = code.instructions
    last_index = len(instructions) - 1
    index = 0

    while index <= last_index:
        instr = instructions[index]
        is_last = index == last_index
        if isinstance(instr, PushLiteral):
            value = instr.value
            if isinstance(value, HCode):
                compile_hcode(value, primitives)

            if isinstance(value, HString) and index < last_index:
                next_instr = instructions[index + 1]
                if isinstance(next_instr, WordRef):
                    if next_instr.name == "set":
                        ops.extend((OP_SET_LITERAL_NAME, value.value))
                        index += 2
                        continue
                    if next_instr.name == "def":
                        ops.extend((OP_DEF_LITERAL_NAME, value.value))
                        index += 2
                        continue
                    if next_instr.name == "get":
                        ops.extend((OP_GET_LITERAL_NAME, value.value))
                        index += 2
                        continue

            ops.append(OP_PUSH_LITERAL)
            ops.append(value)
            index += 1
            continue

        name = instr.name
        if is_last:
            if name == "exec":
                ops.append(OP_TCO_EXEC)
                index += 1
                continue
            if name == "if":
                ops.append(OP_TCO_IF)
                index += 1
                continue
            if name == "if-else":
                ops.append(OP_TCO_IF_ELSE)
                index += 1
                continue

        specialized = SPECIALIZED_PRIMITIVES.get(name)
        if specialized is not None:
            ops.append(specialized)
            index += 1
            continue

        primitive = primitives.get(name)
        if primitive is not None:
            ops.append(OP_CALL_PRIMITIVE)
            ops.append(primitive)
            index += 1
            continue

        ops.append(OP_LOAD_NAME_TAIL if is_last else OP_LOAD_NAME)
        ops.append(NameLoadOp(name, instr.line, instr.col))
        index += 1

    program = BytecodeProgram(code=code, ops=tuple(ops))
    code.bytecode = program
    return program
