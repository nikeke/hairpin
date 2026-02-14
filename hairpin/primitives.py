"""Hairpin primitive words."""

from hairpin.types import (
    HValue, HInt, HFloat, HString, HBool, HCode, HairpinError,
    HCons, HNil, NIL,
)
from hairpin.interpreter import TypeError_, StackUnderflow, _TailCall


def register_primitives(interp):
    """Register all primitive words with the interpreter."""

    def _pop_n(n):
        if len(interp.stack) < n:
            raise StackUnderflow(f"Stack underflow: need {n}, have {len(interp.stack)}")
        return [interp.pop() for _ in range(n)]

    # --- Stack operations ---

    def prim_dup(vm):
        val = vm.pop()
        vm.push(val)
        vm.push(val)

    def prim_drop(vm):
        vm.pop()

    def prim_swap(vm):
        b, a = vm.pop(), vm.pop()
        vm.push(b)
        vm.push(a)

    # --- Namespace ---

    def prim_get(vm):
        name = vm.pop()
        if not isinstance(name, HString):
            raise TypeError_(f"get expects a string, got {name.type_name()}")
        key = name.value
        if key not in vm.namespace:
            raise HairpinError(f"Undefined word '{key}'")
        kind, val = vm.namespace[key]
        vm.push(val)

    def prim_set(vm):
        name = vm.pop()
        value = vm.pop()
        if not isinstance(name, HString):
            raise TypeError_(f"set expects a string name, got {name.type_name()}")
        vm.namespace[name.value] = ('value', value)

    def prim_def(vm):
        name = vm.pop()
        code = vm.pop()
        if not isinstance(name, HString):
            raise TypeError_(f"def expects a string name, got {name.type_name()}")
        if not isinstance(code, HCode):
            raise TypeError_(f"def expects a code object, got {code.type_name()}")
        vm.namespace[name.value] = ('code', code)

    # --- Control flow ---

    def prim_self(vm):
        code = getattr(vm, '_current_code', None)
        if code is None:
            raise HairpinError("self used outside of a code object")
        vm.push(code)

    def prim_exec(vm):
        code = vm.pop()
        if not isinstance(code, HCode):
            raise TypeError_(f"exec expects a code object, got {code.type_name()}")
        vm.execute_in_context(code)

    def prim_if(vm):
        code = vm.pop()
        cond = vm.pop()
        if not isinstance(code, HCode):
            raise TypeError_(f"if expects a code object, got {code.type_name()}")
        if cond.to_bool():
            vm.execute_in_context(code)

    def prim_if_tco(vm):
        """TCO version: returns _TailCall instead of executing."""
        code = vm.pop()
        cond = vm.pop()
        if not isinstance(code, HCode):
            raise TypeError_(f"if expects a code object, got {code.type_name()}")
        if cond.to_bool():
            return _TailCall(code)
        return None

    def prim_if_else(vm):
        else_code = vm.pop()
        then_code = vm.pop()
        cond = vm.pop()
        if not isinstance(then_code, HCode):
            raise TypeError_(f"if-else expects code objects, got {then_code.type_name()}")
        if not isinstance(else_code, HCode):
            raise TypeError_(f"if-else expects code objects, got {else_code.type_name()}")
        if cond.to_bool():
            vm.execute_in_context(then_code)
        else:
            vm.execute_in_context(else_code)

    def prim_if_else_tco(vm):
        """TCO version: returns _TailCall instead of executing."""
        else_code = vm.pop()
        then_code = vm.pop()
        cond = vm.pop()
        if not isinstance(then_code, HCode):
            raise TypeError_(f"if-else expects code objects, got {then_code.type_name()}")
        if not isinstance(else_code, HCode):
            raise TypeError_(f"if-else expects code objects, got {else_code.type_name()}")
        if cond.to_bool():
            return _TailCall(then_code)
        else:
            return _TailCall(else_code)

    def prim_not(vm):
        val = vm.pop()
        vm.push(HBool(not val.to_bool()))

    # --- Arithmetic ---

    def _arith(vm, op):
        b, a = vm.pop(), vm.pop()
        # int-string multiplication (both orders)
        if op == '*':
            if isinstance(a, HInt) and isinstance(b, HString):
                vm.push(HString(b.value * a.value))
                return
            if isinstance(a, HString) and isinstance(b, HInt):
                vm.push(HString(a.value * b.value))
                return
        if type(a) != type(b):
            raise TypeError_(
                f"Cannot apply '{op}' to {a.type_name()} and {b.type_name()}"
            )
        if isinstance(a, HInt):
            if op == '/' and b.value == 0:
                raise HairpinError("Division by zero")
            if op == '%' and b.value == 0:
                raise HairpinError("Modulo by zero")
            ops = {'+': lambda: a.value + b.value, '-': lambda: a.value - b.value,
                   '*': lambda: a.value * b.value, '/': lambda: a.value // b.value,
                   '%': lambda: a.value % b.value}
            vm.push(HInt(ops[op]()))
        elif isinstance(a, HFloat):
            if op in ('/', '%') and b.value == 0.0:
                raise HairpinError(f"{'Division' if op == '/' else 'Modulo'} by zero")
            ops = {'+': lambda: a.value + b.value, '-': lambda: a.value - b.value,
                   '*': lambda: a.value * b.value, '/': lambda: a.value / b.value,
                   '%': lambda: a.value % b.value}
            vm.push(HFloat(ops[op]()))
        elif isinstance(a, HString) and op == '+':
            vm.push(HString(a.value + b.value))
        else:
            raise TypeError_(
                f"Cannot apply '{op}' to {a.type_name()} and {b.type_name()}"
            )

    # --- Comparison ---

    def _compare(vm, op):
        b, a = vm.pop(), vm.pop()
        if type(a) != type(b):
            raise TypeError_(
                f"Cannot compare {a.type_name()} and {b.type_name()}"
            )
        ops = {
            '==': lambda: a.value == b.value, '!=': lambda: a.value != b.value,
            '<': lambda: a.value < b.value, '<=': lambda: a.value <= b.value,
            '>': lambda: a.value > b.value, '>=': lambda: a.value >= b.value,
        }
        vm.push(HBool(ops[op]()))

    # --- Conversion ---

    def prim_integer(vm):
        val = vm.pop()
        if isinstance(val, HInt):
            vm.push(val)
        elif isinstance(val, HFloat):
            vm.push(HInt(int(val.value)))
        elif isinstance(val, HString):
            try:
                vm.push(HInt(int(val.value)))
            except ValueError:
                raise HairpinError(f"Cannot convert string '{val.value}' to integer")
        elif isinstance(val, HBool):
            vm.push(HInt(int(val.value)))
        else:
            raise TypeError_(f"Cannot convert {val.type_name()} to integer")

    def prim_float(vm):
        val = vm.pop()
        if isinstance(val, HFloat):
            vm.push(val)
        elif isinstance(val, HInt):
            vm.push(HFloat(float(val.value)))
        elif isinstance(val, HString):
            try:
                vm.push(HFloat(float(val.value)))
            except ValueError:
                raise HairpinError(f"Cannot convert string '{val.value}' to float")
        elif isinstance(val, HBool):
            vm.push(HFloat(float(val.value)))
        else:
            raise TypeError_(f"Cannot convert {val.type_name()} to float")

    # --- I/O ---

    def _format_list(val):
        """Format a cons list for printing."""
        parts = []
        cur = val
        while isinstance(cur, HCons):
            parts.append(_format_print(cur.head))
            cur = cur.tail
        result = "(" + " ".join(parts)
        if not isinstance(cur, HNil):
            result += " . " + _format_print(cur)
        return result + ")"

    def _format_print(val):
        """Format a value for the print primitive."""
        if isinstance(val, HString):
            return val.value
        elif isinstance(val, HInt):
            return str(val.value)
        elif isinstance(val, HFloat):
            return str(val.value)
        elif isinstance(val, HBool):
            return "true" if val.value else "false"
        elif isinstance(val, HCode):
            return "<code>"
        elif isinstance(val, HNil):
            return "nil"
        elif isinstance(val, HCons):
            return _format_list(val)
        return str(val)

    def prim_print(vm):
        val = vm.pop()
        print(_format_print(val), end="")

    def prim_input(vm):
        vm.push(HString(input()))

    # --- List operations ---

    def prim_cons(vm):
        tail = vm.pop()
        head = vm.pop()
        vm.push(HCons(head, tail))

    def prim_head(vm):
        val = vm.pop()
        if not isinstance(val, HCons):
            raise TypeError_(f"head expects a cons cell, got {val.type_name()}")
        vm.push(val.head)

    def prim_tail(vm):
        val = vm.pop()
        if not isinstance(val, HCons):
            raise TypeError_(f"tail expects a cons cell, got {val.type_name()}")
        vm.push(val.tail)

    def prim_chars(vm):
        val = vm.pop()
        if not isinstance(val, HString):
            raise TypeError_(f"chars expects a string, got {val.type_name()}")
        result = NIL
        for ch in reversed(val.value):
            result = HCons(HString(ch), result)
        vm.push(result)

    def prim_string(vm):
        val = vm.pop()
        parts = []
        cur = val
        while isinstance(cur, HCons):
            if not isinstance(cur.head, HString):
                raise TypeError_(f"string expects a list of strings, got {cur.head.type_name()}")
            parts.append(cur.head.value)
            cur = cur.tail
        if not isinstance(cur, HNil):
            raise TypeError_(f"string expects a proper list, got dotted pair")
        vm.push(HString("".join(parts)))

    def prim_type(vm):
        val = vm.pop()
        vm.push(HString(val.type_name()))

    # --- Register all ---

    interp.register_primitive('dup', prim_dup)
    interp.register_primitive('drop', prim_drop)
    interp.register_primitive('swap', prim_swap)
    interp.register_primitive('get', prim_get)
    interp.register_primitive('set', prim_set)
    interp.register_primitive('def', prim_def)
    interp.register_primitive('self', prim_self)
    interp.register_primitive('exec', prim_exec)
    interp.register_primitive('if', prim_if)
    interp.register_primitive('if-else', prim_if_else)
    interp.register_primitive_tco('if', prim_if_tco)
    interp.register_primitive_tco('if-else', prim_if_else_tco)
    interp.register_primitive('not', prim_not)
    interp.register_primitive('print', prim_print)
    interp.register_primitive('input', prim_input)
    interp.register_primitive('integer', prim_integer)
    interp.register_primitive('float', prim_float)
    interp.register_primitive('cons', prim_cons)
    interp.register_primitive('head', prim_head)
    interp.register_primitive('tail', prim_tail)
    interp.register_primitive('chars', prim_chars)
    interp.register_primitive('string', prim_string)
    interp.register_primitive('type', prim_type)

    for op in ('+', '-', '*', '/', '%'):
        interp.register_primitive(op, lambda vm, o=op: _arith(vm, o))

    for op in ('==', '!=', '<', '<=', '>', '>='):
        interp.register_primitive(op, lambda vm, o=op: _compare(vm, o))
