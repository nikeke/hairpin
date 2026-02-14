"""Tests for the Hairpin parser."""

import pytest
from hairpin.parser import parse, PushLiteral, WordRef, ParseError
from hairpin.types import HInt, HFloat, HString, HBool, HCode


class TestLiterals:
    def test_integer(self):
        result = parse("42")
        assert len(result) == 1
        assert isinstance(result[0], PushLiteral)
        assert result[0].value == HInt(42)

    def test_float(self):
        result = parse("3.14")
        assert result[0].value == HFloat(3.14)

    def test_string(self):
        result = parse("'hello'")
        assert result[0].value == HString("hello")

    def test_true(self):
        result = parse("true")
        assert result[0].value == HBool(True)

    def test_false(self):
        result = parse("false")
        assert result[0].value == HBool(False)


class TestWords:
    def test_simple_word(self):
        result = parse("print")
        assert len(result) == 1
        assert isinstance(result[0], WordRef)
        assert result[0].name == "print"

    def test_operator(self):
        result = parse("+")
        assert result[0].name == "+"


class TestCodeObjects:
    def test_simple(self):
        result = parse("(1 +)")
        assert len(result) == 1
        assert isinstance(result[0], PushLiteral)
        code = result[0].value
        assert isinstance(code, HCode)
        assert len(code.instructions) == 2
        assert code.instructions[0].value == HInt(1)
        assert code.instructions[1].name == "+"

    def test_empty(self):
        result = parse("()")
        code = result[0].value
        assert isinstance(code, HCode)
        assert len(code.instructions) == 0

    def test_nested(self):
        result = parse("((1))")
        outer = result[0].value
        assert isinstance(outer, HCode)
        assert len(outer.instructions) == 1
        inner = outer.instructions[0].value
        assert isinstance(inner, HCode)
        assert inner.instructions[0].value == HInt(1)

    def test_unmatched_rparen(self):
        with pytest.raises(ParseError):
            parse(")")

    def test_unmatched_lparen(self):
        with pytest.raises(ParseError):
            parse("(1 +")


class TestCombined:
    def test_hello_world(self):
        result = parse("'hello, world' print")
        assert len(result) == 2
        assert result[0].value == HString("hello, world")
        assert result[1].name == "print"

    def test_increment_def(self):
        result = parse("(1 + ) 'increment' def")
        assert len(result) == 3
        code = result[0].value
        assert isinstance(code, HCode)
        assert result[1].value == HString("increment")
        assert result[2].name == "def"

    def test_conditional(self):
        result = parse("input integer 0 ==\n    ('zero' print) if")
        assert len(result) == 6
        assert result[0].name == "input"
        assert result[1].name == "integer"
        assert result[2].value == HInt(0)
        assert result[3].name == "=="
        code = result[4].value
        assert isinstance(code, HCode)
        assert result[5].name == "if"
