"""Tests for cons list support."""

import pytest

from hairpin.interpreter import Interpreter, TypeError_
from hairpin.types import HCons, HInt, HNil


def run(source: str) -> Interpreter:
    interp = Interpreter()
    interp.run(source)
    return interp


def stack(interp: Interpreter) -> list:
    return [v.value if hasattr(v, 'value') else v for v in interp.stack]


class TestNil:
    def test_nil_pushes(self):
        interp = run("nil")
        assert len(interp.stack) == 1
        assert isinstance(interp.stack[0], HNil)

    def test_nil_is_falsy(self):
        interp = run("nil (1) (2) if-else")
        assert stack(interp) == [2]

    def test_nil_singleton(self):
        interp = run("nil nil")
        assert interp.stack[0] is interp.stack[1]


class TestCons:
    def test_cons_creates_pair(self):
        interp = run("1 nil cons")
        assert len(interp.stack) == 1
        cell = interp.stack[0]
        assert isinstance(cell, HCons)
        assert cell.head == HInt(1)
        assert isinstance(cell.tail, HNil)

    def test_cons_is_truthy(self):
        interp = run("1 nil cons (1) (2) if-else")
        assert stack(interp) == [1]

    def test_build_list(self):
        interp = run("1 2 nil cons cons")
        cell = interp.stack[0]
        assert cell.head == HInt(1)
        assert cell.tail.head == HInt(2)
        assert isinstance(cell.tail.tail, HNil)


class TestHeadTail:
    def test_head(self):
        interp = run("1 nil cons head")
        assert stack(interp) == [1]

    def test_tail(self):
        interp = run("1 2 nil cons cons tail head")
        assert stack(interp) == [2]

    def test_tail_of_singleton(self):
        interp = run("1 nil cons tail")
        assert isinstance(interp.stack[0], HNil)

    def test_head_type_error(self):
        with pytest.raises(TypeError_):
            run("42 head")

    def test_tail_type_error(self):
        with pytest.raises(TypeError_):
            run("42 tail")

    def test_head_nil_error(self):
        with pytest.raises(TypeError_):
            run("nil head")


class TestListPrint:
    def test_print_nil(self, capsys):
        run("nil print")
        assert capsys.readouterr().out == "nil"

    def test_print_list(self, capsys):
        run("1 2 3 nil cons cons cons print")
        assert capsys.readouterr().out == "(1 2 3)"

    def test_print_dotted_pair(self, capsys):
        run("1 2 cons print")
        assert capsys.readouterr().out == "(1 . 2)"


class TestListRecursion:
    def test_list_length(self):
        """Compute length of a list using recursion."""
        interp = run("""
            1 2 3 4 5 nil cons cons cons cons cons
            'lst' set
            0 'len' set
            (self lst
                (lst tail 'lst' set len 1 + 'len' set exec)
                (drop) if-else)
            exec
            len
        """)
        assert stack(interp) == [5]

    def test_list_sum(self):
        """Sum elements of a list."""
        interp = run("""
            1 2 3 nil cons cons cons
            'lst' set
            0 'total' set
            (self lst
                (lst head total + 'total' set lst tail 'lst' set exec)
                (drop) if-else)
            exec
            total
        """)
        assert stack(interp) == [6]


class TestChars:
    def test_chars_basic(self):
        interp = run("'abc' chars")
        v = interp.stack[0]
        assert isinstance(v, HCons)
        assert v.head.value == "a"
        assert v.tail.head.value == "b"
        assert v.tail.tail.head.value == "c"
        assert isinstance(v.tail.tail.tail, HNil)

    def test_chars_empty(self):
        interp = run("'' chars")
        assert isinstance(interp.stack[0], HNil)

    def test_chars_single(self):
        interp = run("'x' chars")
        v = interp.stack[0]
        assert v.head.value == "x"
        assert isinstance(v.tail, HNil)

    def test_chars_type_error(self):
        with pytest.raises(TypeError_):
            run("42 chars")


class TestString:
    def test_string_basic(self):
        interp = run("'a' 'b' 'c' nil cons cons cons string")
        assert interp.stack[0].value == "abc"

    def test_string_empty(self):
        interp = run("nil string")
        assert interp.stack[0].value == ""

    def test_string_single(self):
        interp = run("'x' nil cons string")
        assert interp.stack[0].value == "x"

    def test_string_type_error_non_string_element(self):
        with pytest.raises(TypeError_):
            run("1 nil cons string")

    def test_string_type_error_dotted(self):
        with pytest.raises(TypeError_):
            run("'a' 'b' cons string")

    def test_roundtrip(self):
        interp = run("'hello' chars string")
        assert interp.stack[0].value == "hello"
