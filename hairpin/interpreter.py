"""Hairpin interpreter — executes parsed instruction sequences."""

from hairpin.parser import parse, PushLiteral, WordRef
from hairpin.types import HValue, HCode, HairpinError


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
    def __init__(self):
        self.stack: list[HValue] = []
        self.namespace: dict[str, tuple[str, object]] = {}
        self.repl_commands: dict[str, callable] = {}
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
            result = self._execute_body(current.instructions)
            if isinstance(result, _TailCall):
                current = result.code
            else:
                break
        self._current_code = old_code

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
