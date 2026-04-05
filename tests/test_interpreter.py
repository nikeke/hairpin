"""Tests for the Hairpin interpreter and primitives."""

import pytest
from hairpin.bytecode import (
    NameLoadOp,
    OP_ADD,
    OP_CONS,
    OP_DROP,
    OP_DUP,
    OP_EQ,
    OP_HEAD,
    OP_MUL,
    OP_SWAP,
    OP_TAIL,
)
from hairpin.interpreter import Interpreter, StackUnderflow, UndefinedWord, TypeError_
from hairpin.types import HInt, HFloat, HString, HBool, HCode, HairpinError


def run(source: str, input_lines: list[str] | None = None) -> Interpreter:
    """Helper: run source and return the interpreter."""
    interp = Interpreter()
    if input_lines is not None:
        import builtins
        orig = builtins.input
        it = iter(input_lines)
        builtins.input = lambda *a: next(it)
        try:
            interp.run(source)
        finally:
            builtins.input = orig
    else:
        interp.run(source)
    return interp


def stack(interp: Interpreter) -> list:
    """Extract raw values from the stack."""
    return [v.value if hasattr(v, 'value') else v for v in interp.stack]


class TestStackOps:
    def test_dup(self):
        interp = run("42 dup")
        assert stack(interp) == [42, 42]

    def test_drop(self):
        interp = run("1 2 drop")
        assert stack(interp) == [1]

    def test_swap(self):
        interp = run("1 2 swap")
        assert stack(interp) == [2, 1]

    def test_underflow(self):
        with pytest.raises(StackUnderflow):
            run("drop")

    def test_compiled_stack_opcodes(self):
        interp = run("(1 dup swap drop) 'prog' def")
        kind, code = interp.namespace['prog']
        assert kind == 'code'
        assert OP_DUP in code.bytecode.ops
        assert OP_SWAP in code.bytecode.ops
        assert OP_DROP in code.bytecode.ops

    def test_compiled_stack_opcode_semantics(self):
        interp = run("(1 dup swap drop) 'prog' def prog")
        assert stack(interp) == [1]

    def test_compiled_stack_opcode_underflow(self):
        with pytest.raises(StackUnderflow):
            run("(swap) 'prog' def prog")

    def test_compiled_list_opcodes(self):
        interp = run("(1 2 nil cons cons tail head) 'prog' def")
        kind, code = interp.namespace['prog']
        assert kind == 'code'
        assert OP_CONS in code.bytecode.ops
        assert OP_TAIL in code.bytecode.ops
        assert OP_HEAD in code.bytecode.ops

    def test_compiled_list_opcode_semantics(self):
        interp = run("(1 2 nil cons cons tail head) 'prog' def prog")
        assert stack(interp) == [2]

    def test_compiled_list_opcode_type_error(self):
        with pytest.raises(TypeError_):
            run("(nil head) 'prog' def prog")


class TestArithmetic:
    def test_add_int(self):
        interp = run("3 4 +")
        assert stack(interp) == [7]

    def test_sub_int(self):
        interp = run("10 3 -")
        assert stack(interp) == [7]

    def test_mul_int(self):
        interp = run("6 7 *")
        assert stack(interp) == [42]

    def test_div_int(self):
        interp = run("10 3 /")
        assert stack(interp) == [3]  # integer division

    def test_mod_int(self):
        interp = run("10 3 %")
        assert stack(interp) == [1]

    def test_add_float(self):
        interp = run("1.5 2.5 +")
        assert stack(interp) == [4.0]

    def test_string_concat(self):
        interp = run("'hello' ' world' +")
        assert stack(interp) == ["hello world"]

    def test_int_string_mul(self):
        interp = run("3 'ab' *")
        assert stack(interp) == ["ababab"]

    def test_string_int_mul(self):
        interp = run("'ab' 3 *")
        assert stack(interp) == ["ababab"]

    def test_type_error(self):
        with pytest.raises(TypeError_):
            run("3 2.5 +")

    def test_div_zero(self):
        with pytest.raises(HairpinError):
            run("1 0 /")


class TestComparison:
    def test_eq(self):
        interp = run("3 3 ==")
        assert stack(interp) == [True]

    def test_ne(self):
        interp = run("3 4 !=")
        assert stack(interp) == [True]

    def test_lt(self):
        interp = run("3 4 <")
        assert stack(interp) == [True]

    def test_ge(self):
        interp = run("4 3 >=")
        assert stack(interp) == [True]

    def test_type_error(self):
        with pytest.raises(TypeError_):
            run("3 'hello' ==")


class TestConversion:
    def test_string_to_int(self):
        interp = run("'42' integer")
        assert stack(interp) == [42]

    def test_float_to_int(self):
        interp = run("3.7 integer")
        assert stack(interp) == [3]

    def test_string_to_float(self):
        interp = run("'3.14' float")
        assert stack(interp) == [3.14]

    def test_int_to_float(self):
        interp = run("42 float")
        assert stack(interp) == [42.0]

    def test_invalid_conversion(self):
        with pytest.raises(HairpinError):
            run("'abc' integer")


class TestNamespace:
    def test_set_and_use(self):
        interp = run("42 'x' set x")
        assert stack(interp) == [42]

    def test_get(self):
        interp = run("42 'x' set 'x' get")
        assert stack(interp) == [42]

    def test_def_and_call(self):
        interp = run("(1 +) 'inc' def 5 inc")
        assert stack(interp) == [6]

    def test_undefined_word(self):
        with pytest.raises(UndefinedWord):
            run("nosuchword")

    def test_set_overwrites_def(self):
        interp = run("(1 +) 'x' def 99 'x' set x")
        assert stack(interp) == [99]

    def test_set_invalidates_cached_def(self):
        interp = run("(1 +) 'x' def 5 x 99 'x' set x")
        assert stack(interp) == [6, 99]

    def test_def_invalidates_cached_value(self):
        interp = run("99 'x' set x drop (1 +) 'x' def 41 x")
        assert stack(interp) == [42]

    def test_def_caches_bytecode(self):
        interp = run("(1 +) 'inc' def")
        kind, code = interp.namespace['inc']
        assert kind == 'code'
        assert code.bytecode is not None

    def test_exec_lazily_compiles_code_value(self):
        interp = run("1 (1 +) 'snippet' set snippet exec")
        kind, code = interp.namespace['snippet']
        assert kind == 'value'
        assert code.bytecode is not None
        assert stack(interp) == [2]

    def test_compiled_code_preserves_dynamic_rebinding(self):
        interp = run("(x 1 +) 'bump-x' def 5 'x' set bump-x 7 'x' set bump-x")
        assert stack(interp) == [6, 8]

    def test_compiled_literal_set_and_get(self):
        interp = run("(41 'x' set 'x' get) 'prog' def prog")
        assert stack(interp) == [41]

    def test_compiled_literal_def(self):
        interp = run("((1 +) 'inc' def 5 inc) 'prog' def prog")
        assert stack(interp) == [6]

    def test_compiled_dynamic_name_falls_back(self):
        interp = run("('x' 'name' set 41 name set name get) 'prog' def prog")
        assert stack(interp) == [41]

    def test_compiled_name_load_uses_compact_record(self):
        interp = run("(x x +) 'prog' def")
        kind, code = interp.namespace['prog']
        assert kind == 'code'
        assert any(isinstance(op, NameLoadOp) for op in code.bytecode.ops)

    def test_compiled_name_load_record_tracks_rebinding(self):
        interp = run("(x) 'prog' def 1 'x' set prog 2 'x' set prog")
        assert stack(interp) == [1, 2]

    def test_compiled_name_load_record_rebinds_per_interpreter(self):
        first = run("(x) 'prog' def 1 'x' set prog")
        _, code = first.namespace['prog']
        second = Interpreter()
        second.set_namespace_entry('prog', 'code', code)
        second.set_namespace_entry('x', 'value', HInt(2))
        second.run("prog")
        assert stack(second) == [2]

    def test_compiled_name_load_record_handles_namespace_clear(self):
        interp = run("(x) 'prog' def 1 'x' set")
        _, code = interp.namespace['prog']
        interp.execute_in_context(code)
        interp.clear_namespace()
        with pytest.raises(UndefinedWord, match="Undefined word 'x'"):
            interp.execute_in_context(code)

    def test_compiled_arithmetic_and_comparison_opcodes(self):
        interp = run("(1 2 + 3 ==) 'prog' def")
        kind, code = interp.namespace['prog']
        assert kind == 'code'
        assert OP_ADD in code.bytecode.ops
        assert OP_EQ in code.bytecode.ops

    def test_compiled_specialized_multiply_semantics(self):
        interp = run("(3 'ab' * 'ababab' ==) 'prog' def prog")
        assert stack(interp) == [True]

    def test_compiled_specialized_division_error(self):
        with pytest.raises(HairpinError, match="Division by zero"):
            run("(1 0 /) 'prog' def prog")


class TestControlFlow:
    def test_if_true(self):
        interp = run("1 (42) if")
        assert stack(interp) == [42]

    def test_if_false(self):
        interp = run("0 (42) if")
        assert stack(interp) == []

    def test_if_else_true(self):
        interp = run("1 ('yes') ('no') if-else")
        assert stack(interp) == ["yes"]

    def test_if_else_false(self):
        interp = run("0 ('yes') ('no') if-else")
        assert stack(interp) == ["no"]

    def test_not_true(self):
        interp = run("true not")
        assert stack(interp) == [False]

    def test_not_false(self):
        interp = run("false not")
        assert stack(interp) == [True]

    def test_not_zero(self):
        interp = run("0 not")
        assert stack(interp) == [True]

    def test_not_nonempty_string(self):
        interp = run("'hi' not")
        assert stack(interp) == [False]


class TestSelfExec:
    def test_self_exec_loop(self, capsys):
        """Test a counting loop using self/exec pattern (matches notes.md)."""
        interp = run("""
            (1 +) 'increment' def
            1 'i' set
            (self
             i 5 <=
                (i print i increment 'i' set exec) if)
            exec drop
        """)
        output = capsys.readouterr().out
        assert output == "12345"

    def test_compiled_def_tco_loop(self):
        interp = run("""
            1 'i' set
            (self
             i 10000 <=
                (i 1 + 'i' set exec) if)
            'loop' def
            loop drop
        """)
        kind, val = interp.namespace['i']
        assert kind == 'value'
        assert val.value == 10001


class TestIO:
    def test_print(self, capsys):
        run("42 print")
        assert capsys.readouterr().out == "42"

    def test_print_string(self, capsys):
        run("'hello' print")
        assert capsys.readouterr().out == "hello"

    def test_print_bool(self, capsys):
        run("true print")
        assert capsys.readouterr().out == "true"

    def test_input(self):
        interp = run("input", input_lines=["hello"])
        assert stack(interp) == ["hello"]


class TestBooleanCoercion:
    def test_zero_is_false(self):
        interp = run("0 (1) (2) if-else")
        assert stack(interp) == [2]

    def test_empty_string_is_false(self):
        interp = run("'' (1) (2) if-else")
        assert stack(interp) == [2]

    def test_empty_code_is_false(self):
        interp = run("() (1) (2) if-else")
        assert stack(interp) == [2]

    def test_nonzero_is_true(self):
        interp = run("42 (1) (2) if-else")
        assert stack(interp) == [1]

    def test_nonempty_string_is_true(self):
        interp = run("'x' (1) (2) if-else")
        assert stack(interp) == [1]
