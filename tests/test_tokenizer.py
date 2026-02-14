"""Tests for the Hairpin tokenizer."""

import pytest
from hairpin.tokenizer import tokenize, TokenType, TokenizerError


def types(tokens):
    """Extract token types, excluding EOF."""
    return [t.type for t in tokens if t.type != TokenType.EOF]


def values(tokens):
    """Extract token values, excluding EOF."""
    return [t.value for t in tokens if t.type != TokenType.EOF]


class TestIntegers:
    def test_single(self):
        assert values(tokenize("42")) == [42]

    def test_negative(self):
        assert values(tokenize("-7")) == [-7]

    def test_zero(self):
        assert values(tokenize("0")) == [0]

    def test_large(self):
        assert values(tokenize("99999999999999999999")) == [99999999999999999999]

    def test_type(self):
        assert types(tokenize("42")) == [TokenType.INTEGER]


class TestFloats:
    def test_simple(self):
        assert values(tokenize("3.14")) == [3.14]

    def test_negative(self):
        assert values(tokenize("-2.5")) == [-2.5]

    def test_scientific(self):
        assert values(tokenize("1e10")) == [1e10]

    def test_scientific_negative_exp(self):
        assert values(tokenize("1.5e-3")) == [1.5e-3]

    def test_type(self):
        assert types(tokenize("3.14")) == [TokenType.FLOAT]


class TestStrings:
    def test_simple(self):
        assert values(tokenize("'hello'")) == ["hello"]

    def test_empty(self):
        assert values(tokenize("''")) == [""]

    def test_escape_newline(self):
        assert values(tokenize(r"'hello\nworld'")) == ["hello\nworld"]

    def test_escape_tab(self):
        assert values(tokenize(r"'a\tb'")) == ["a\tb"]

    def test_escape_backslash(self):
        assert values(tokenize("'a\\\\b'")) == ["a\\b"]

    def test_escape_quote(self):
        assert values(tokenize("'it\\'s'")) == ["it's"]

    def test_unterminated(self):
        with pytest.raises(TokenizerError):
            tokenize("'hello")

    def test_type(self):
        assert types(tokenize("'x'")) == [TokenType.STRING]


class TestBooleans:
    def test_true(self):
        assert values(tokenize("true")) == [True]
        assert types(tokenize("true")) == [TokenType.BOOLEAN]

    def test_false(self):
        assert values(tokenize("false")) == [False]
        assert types(tokenize("false")) == [TokenType.BOOLEAN]


class TestParens:
    def test_lparen(self):
        assert types(tokenize("(")) == [TokenType.LPAREN]

    def test_rparen(self):
        assert types(tokenize(")")) == [TokenType.RPAREN]

    def test_nested(self):
        assert types(tokenize("(())")) == [
            TokenType.LPAREN, TokenType.LPAREN,
            TokenType.RPAREN, TokenType.RPAREN,
        ]


class TestWords:
    def test_simple(self):
        assert values(tokenize("print")) == ["print"]
        assert types(tokenize("print")) == [TokenType.WORD]

    def test_operator(self):
        assert values(tokenize("+")) == ["+"]

    def test_comparison(self):
        assert values(tokenize("<=")) == ["<="]

    def test_hyphenated(self):
        assert values(tokenize("if-else")) == ["if-else"]


class TestComments:
    def test_comment_line_ignored(self):
        assert values(tokenize("# this is a comment")) == []

    def test_comment_with_code(self):
        toks = tokenize("# comment\n42")
        assert values(toks) == [42]


class TestCombined:
    def test_hello_world(self):
        toks = tokenize("'hello, world' print")
        assert values(toks) == ["hello, world", "print"]
        assert types(toks) == [TokenType.STRING, TokenType.WORD]

    def test_code_object(self):
        toks = tokenize("(1 + )")
        assert types(toks) == [
            TokenType.LPAREN, TokenType.INTEGER, TokenType.WORD, TokenType.RPAREN,
        ]

    def test_conditional(self):
        toks = tokenize("input integer 0 ==\n    ('zero' print) if")
        assert values(toks) == [
            "input", "integer", 0, "==",
            "(", "zero", "print", ")", "if",
        ]

    def test_minus_as_operator(self):
        """After a number, - should be an operator word, not a negative sign."""
        toks = tokenize("3 -")
        assert values(toks) == [3, "-"]
        assert types(toks) == [TokenType.INTEGER, TokenType.WORD]

    def test_negative_in_code(self):
        toks = tokenize("(-1)")
        assert values(toks) == ["(", -1, ")"]


class TestPositionTracking:
    def test_line_numbers(self):
        toks = tokenize("1\n2\n3")
        assert [(t.line, t.value) for t in toks if t.type != TokenType.EOF] == [
            (1, 1), (2, 2), (3, 3),
        ]

    def test_column_numbers(self):
        toks = tokenize("42 'hi'")
        non_eof = [t for t in toks if t.type != TokenType.EOF]
        assert non_eof[0].col == 1
        assert non_eof[1].col == 4
