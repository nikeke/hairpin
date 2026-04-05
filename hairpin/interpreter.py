"""Hairpin interpreter — executes parsed instruction sequences."""

from hairpin.bytecode import (
    OP_ADD,
    OP_CALL_PRIMITIVE,
    OP_DIV,
    OP_DEF_LITERAL_NAME,
    OP_EQ,
    OP_GE,
    OP_GET_LITERAL_NAME,
    OP_GT,
    OP_LE,
    OP_LT,
    OP_LOAD_NAME,
    OP_LOAD_NAME_TAIL,
    OP_MOD,
    OP_MUL,
    OP_NE,
    OP_PUSH_LITERAL,
    OP_SET_LITERAL_NAME,
    OP_SUB,
    OP_TCO_EXEC,
    OP_TCO_IF,
    OP_TCO_IF_ELSE,
    BytecodeProgram,
    NameLoadOp,
    compile_hcode,
)
from hairpin.parser import parse, PushLiteral, WordRef
from hairpin.types import HBool, HCode, HFloat, HInt, HString, HValue, HairpinError


class RuntimeError_(HairpinError):
    pass


class StackUnderflow(RuntimeError_):
    pass


class UndefinedWord(RuntimeError_):
    pass


class TypeError_(RuntimeError_):
    pass


# Sentinel for tail-call optimization
class _TailCall:
    __slots__ = ('code',)

    def __init__(self, code: HCode):
        self.code = code


class Interpreter:
    def __init__(self, use_bytecode: bool = True):
        self.stack: list[HValue] = []
        self.namespace: dict[str, tuple[str, object]] = {}
        self.repl_commands: dict[str, callable] = {}
        self.use_bytecode = use_bytecode
        self._current_code: HCode | None = None
        from hairpin.primitives import register_primitives
        register_primitives(self)

    def run(self, source: str):
        """Parse and execute source code."""
        instructions = parse(source)
        self._run_instructions(instructions)

    def _run_instructions(self, instructions: list):
        """Execute top-level instructions (no TCO at top level)."""
        for instr in instructions:
            if isinstance(instr, PushLiteral):
                self.stack.append(instr.value)
            elif isinstance(instr, WordRef):
                self._dispatch_word(instr, is_last=False)

    def execute_in_context(self, code: HCode):
        """Execute a code object with trampoline for TCO.
        
        _current_code always refers to the original code object passed in,
        so that `self` returns the right code even through TCO trampolining.
        """
        old_code = self._current_code
        self._current_code = code
        current = code
        while True:
            result = self._execute_code(current)
            if isinstance(result, _TailCall):
                current = result.code
            else:
                break
        self._current_code = old_code

    def compile_code(self, code: HCode) -> BytecodeProgram:
        return compile_hcode(code, self._primitives)

    def set_namespace_entry(self, name: str, kind: str, value: object):
        self.namespace[name] = (kind, value)

    def clear_namespace(self):
        self.namespace.clear()

    def _execute_code(self, code: HCode):
        if self.use_bytecode:
            return self._execute_bytecode(self.compile_code(code))
        return self._execute_body(code.instructions)

    def _execute_body(self, instructions: list):
        """Execute instructions. Returns _TailCall if tail position is a tail call."""
        for i, instr in enumerate(instructions):
            is_last = (i == len(instructions) - 1)
            if isinstance(instr, PushLiteral):
                self.stack.append(instr.value)
            elif isinstance(instr, WordRef):
                result = self._dispatch_word(instr, is_last)
                if isinstance(result, _TailCall):
                    return result
        return None

    def _dispatch_word(self, instr: WordRef, is_last: bool):
        """Dispatch a word. Returns _TailCall for TCO, else None."""
        if instr.name in self.repl_commands:
            self.repl_commands[instr.name](self)
        elif instr.name in self._primitives:
            if is_last and instr.name == 'exec':
                return self._tco_exec()
            if is_last and instr.name in ('if', 'if-else'):
                return self._primitives_tco[instr.name](self)
            self._primitives[instr.name](self)
        elif instr.name in self.namespace:
            kind, val = self.namespace[instr.name]
            if kind == 'value':
                self.stack.append(val)
            elif kind == 'code':
                if is_last:
                    return _TailCall(val)
                self.execute_in_context(val)
        else:
            raise UndefinedWord(
                f"Undefined word '{instr.name}' at {instr.line}:{instr.col}"
            )
        return None

    def _execute_bytecode(self, program: BytecodeProgram):
        """Execute compiled bytecode for a code object."""
        ops = program.ops
        stack = self.stack
        namespace = self.namespace
        primitives = self._primitives
        repl_commands = self.repl_commands
        append = stack.append
        stack_pop = stack.pop
        execute_in_context = self.execute_in_context
        compile_code = self.compile_code
        set_namespace_entry = self.set_namespace_entry
        use_bytecode = self.use_bytecode
        pop = self.pop
        repl_get = repl_commands.get
        namespace_get = namespace.get
        tco_exec = self._tco_exec
        if_tco = self._primitives_tco['if']
        if_else_tco = self._primitives_tco['if-else']
        pc = 0

        while pc < len(ops):
            op = ops[pc]
            pc += 1

            if op == OP_PUSH_LITERAL:
                append(ops[pc])
                pc += 1
                continue

            if op == OP_CALL_PRIMITIVE:
                ops[pc](self)
                pc += 1
                continue

            if op == OP_TCO_EXEC:
                return tco_exec()

            if op == OP_TCO_IF:
                result = if_tco(self)
                if isinstance(result, _TailCall):
                    return result
                continue

            if op == OP_TCO_IF_ELSE:
                return if_else_tco(self)

            if OP_ADD <= op <= OP_GE:
                try:
                    b = stack_pop()
                    a = stack_pop()
                except IndexError:
                    raise StackUnderflow("Stack underflow") from None
                a_type = type(a)
                b_type = type(b)

                if op == OP_ADD:
                    if a_type is HInt and b_type is HInt:
                        append(HInt(a.value + b.value))
                        continue
                    if a_type is HFloat and b_type is HFloat:
                        append(HFloat(a.value + b.value))
                        continue
                    if a_type is HString and b_type is HString:
                        append(HString(a.value + b.value))
                        continue
                    append(a)
                    append(b)
                    primitives['+'](self)
                    continue

                if op == OP_SUB:
                    if a_type is HInt and b_type is HInt:
                        append(HInt(a.value - b.value))
                        continue
                    if a_type is HFloat and b_type is HFloat:
                        append(HFloat(a.value - b.value))
                        continue
                    append(a)
                    append(b)
                    primitives['-'](self)
                    continue

                if op == OP_MUL:
                    if a_type is HInt and b_type is HInt:
                        append(HInt(a.value * b.value))
                        continue
                    if a_type is HFloat and b_type is HFloat:
                        append(HFloat(a.value * b.value))
                        continue
                    if a_type is HInt and b_type is HString:
                        append(HString(b.value * a.value))
                        continue
                    if a_type is HString and b_type is HInt:
                        append(HString(a.value * b.value))
                        continue
                    append(a)
                    append(b)
                    primitives['*'](self)
                    continue

                if op == OP_DIV:
                    if a_type is HInt and b_type is HInt:
                        if b.value == 0:
                            raise HairpinError("Division by zero")
                        append(HInt(a.value // b.value))
                        continue
                    if a_type is HFloat and b_type is HFloat:
                        if b.value == 0.0:
                            raise HairpinError("Division by zero")
                        append(HFloat(a.value / b.value))
                        continue
                    append(a)
                    append(b)
                    primitives['/'](self)
                    continue

                if op == OP_MOD:
                    if a_type is HInt and b_type is HInt:
                        if b.value == 0:
                            raise HairpinError("Modulo by zero")
                        append(HInt(a.value % b.value))
                        continue
                    if a_type is HFloat and b_type is HFloat:
                        if b.value == 0.0:
                            raise HairpinError("Modulo by zero")
                        append(HFloat(a.value % b.value))
                        continue
                    append(a)
                    append(b)
                    primitives['%'](self)
                    continue

                if a_type is not b_type or a_type not in (HInt, HFloat, HString, HBool):
                    append(a)
                    append(b)
                    if op == OP_EQ:
                        primitives['=='](self)
                    elif op == OP_NE:
                        primitives['!='](self)
                    elif op == OP_LT:
                        primitives['<'](self)
                    elif op == OP_LE:
                        primitives['<='](self)
                    elif op == OP_GT:
                        primitives['>'](self)
                    else:
                        primitives['>='](self)
                    continue

                a_val = a.value
                b_val = b.value
                if op == OP_EQ:
                    append(HBool(a_val == b_val))
                elif op == OP_NE:
                    append(HBool(a_val != b_val))
                elif op == OP_LT:
                    append(HBool(a_val < b_val))
                elif op == OP_LE:
                    append(HBool(a_val <= b_val))
                elif op == OP_GT:
                    append(HBool(a_val > b_val))
                else:
                    append(HBool(a_val >= b_val))
                continue

            if op == OP_SET_LITERAL_NAME:
                name = ops[pc]
                set_namespace_entry(name, 'value', pop())
                pc += 1
                continue

            if op == OP_DEF_LITERAL_NAME:
                name = ops[pc]
                code = pop()
                if not isinstance(code, HCode):
                    raise TypeError_(f"def expects a code object, got {code.type_name()}")
                if use_bytecode:
                    compile_code(code)
                set_namespace_entry(name, 'code', code)
                pc += 1
                continue

            if op == OP_GET_LITERAL_NAME:
                name = ops[pc]
                entry = namespace_get(name)
                if entry is None:
                    raise HairpinError(f"Undefined word '{name}'")
                append(entry[1])
                pc += 1
                continue

            load_op: NameLoadOp = ops[pc]
            pc += 1

            repl_command = repl_get(load_op.name)
            if repl_command is not None:
                repl_command(self)
                continue

            entry = namespace_get(load_op.name)
            if entry is None:
                raise UndefinedWord(
                    f"Undefined word '{load_op.name}' at {load_op.line}:{load_op.col}"
                )

            kind, val = entry
            if kind == 'value':
                append(val)
                continue
            if kind == 'code':
                if op == OP_LOAD_NAME_TAIL:
                    return _TailCall(val)
                execute_in_context(val)
                continue

            raise RuntimeError_(
                f"Unknown namespace entry kind {kind!r} for '{load_op.name}'"
            )

    def _tco_exec(self) -> _TailCall:
        """Handle exec as a tail call."""
        code = self.pop()
        if not isinstance(code, HCode):
            raise TypeError_(f"exec expects a code object, got {code.type_name()}")
        return _TailCall(code)

    def push(self, value: HValue):
        self.stack.append(value)

    def pop(self) -> HValue:
        if not self.stack:
            raise StackUnderflow("Stack underflow")
        return self.stack.pop()

    def peek(self) -> HValue:
        if not self.stack:
            raise StackUnderflow("Stack underflow")
        return self.stack[-1]

    def register_primitive(self, name: str, func):
        """Register a primitive word."""
        if not hasattr(self, '_primitives'):
            self._primitives = {}
        self._primitives[name] = func

    def register_primitive_tco(self, name: str, func):
        """Register a TCO-aware version of a primitive."""
        if not hasattr(self, '_primitives_tco'):
            self._primitives_tco = {}
        self._primitives_tco[name] = func
