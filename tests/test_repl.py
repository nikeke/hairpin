"""Tests for REPL commands."""

import pytest
from hairpin.interpreter import Interpreter
from hairpin.repl import REPL_COMMANDS
from hairpin.types import HInt, HString, HCode


@pytest.fixture
def interp():
    """Interpreter with REPL commands registered."""
    vm = Interpreter()
    for name, (func, _) in REPL_COMMANDS.items():
        vm.repl_commands[name] = func
    return vm


class TestStackCommand:
    def test_empty(self, interp, capsys):
        REPL_COMMANDS["/stack"][0](interp)
        assert capsys.readouterr().out == "(empty)\n"

    def test_with_values(self, interp, capsys):
        interp.run("1 2 3")
        REPL_COMMANDS["/stack"][0](interp)
        assert capsys.readouterr().out == "1 2 3\n"

    def test_mixed_types(self, interp, capsys):
        interp.run("42 'hello' true")
        REPL_COMMANDS["/stack"][0](interp)
        assert capsys.readouterr().out == "42 'hello' true\n"

    def test_inline(self, interp, capsys):
        """REPL commands work inline with other code."""
        interp.run("1 2 3 /stack 4")
        assert capsys.readouterr().out == "1 2 3\n"
        assert len(interp.stack) == 4


class TestWordsCommand:
    def test_empty(self, interp, capsys):
        REPL_COMMANDS["/words"][0](interp)
        assert capsys.readouterr().out == "(none)\n"

    def test_with_values(self, interp, capsys):
        interp.run("42 'x' set")
        REPL_COMMANDS["/words"][0](interp)
        out = capsys.readouterr().out
        assert "x = 42" in out

    def test_with_code(self, interp, capsys):
        interp.run("(1 +) 'inc' def")
        REPL_COMMANDS["/words"][0](interp)
        out = capsys.readouterr().out
        assert "inc : <code>" in out


class TestClearCommand:
    def test_clear(self, interp, capsys):
        interp.run("1 2 3")
        assert len(interp.stack) == 3
        REPL_COMMANDS["/clear"][0](interp)
        assert len(interp.stack) == 0
        assert "cleared" in capsys.readouterr().out.lower()


class TestResetCommand:
    def test_reset(self, interp, capsys):
        interp.run("42 'x' set 1 2 3")
        REPL_COMMANDS["/reset"][0](interp)
        assert len(interp.stack) == 0
        assert len(interp.namespace) == 0
        assert "reset" in capsys.readouterr().out.lower()


class TestHelpCommand:
    def test_lists_all_commands(self, interp, capsys):
        REPL_COMMANDS["/help"][0](interp)
        out = capsys.readouterr().out
        for cmd in REPL_COMMANDS:
            assert cmd in out


class TestBuiltinsCommand:
    def test_lists_primitives(self, interp, capsys):
        REPL_COMMANDS["/builtins"][0](interp)
        out = capsys.readouterr().out
        for word in ("dup", "drop", "swap", "print", "cons", "head", "tail", "+", "if-else"):
            assert word in out

    def test_sorted(self, interp, capsys):
        REPL_COMMANDS["/builtins"][0](interp)
        words = capsys.readouterr().out.strip().split()
        assert words == sorted(words)


class TestInlineUsage:
    def test_inside_code_object(self, interp, capsys):
        """REPL commands work inside code objects."""
        interp.run("(1 2 /stack 3) exec")
        assert capsys.readouterr().out == "1 2\n"
        assert len(interp.stack) == 3

    def test_not_available_without_registration(self, capsys):
        """Without REPL registration, /commands are undefined words."""
        vm = Interpreter()
        from hairpin.interpreter import UndefinedWord
        with pytest.raises(UndefinedWord):
            vm.run("/stack")
