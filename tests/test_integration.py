"""Integration tests for the documented example programs."""

import os

from hairpin.interpreter import Interpreter
from hairpin.types import NIL, HCons, HString

# Load the self-interpreter source.
_selfinterp_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'selfinterp.hp')
with open(_selfinterp_path, encoding="utf-8") as f:
    _SELFINTERP_SOURCE = f.read()
_fib_example_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'fib.hp')


def _string_list(values: list[str]):
    result = NIL
    for value in reversed(values):
        result = HCons(HString(value), result)
    return result


def run_with_io(source: str, input_lines: list[str] | None = None, capsys=None):
    """Run source, optionally providing input, return (interp, stdout)."""
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


class TestLanguageExamples:
    """Test the documented language examples."""

    def test_hello_world(self, capsys):
        run_with_io("'hello, world' print")
        assert capsys.readouterr().out == "hello, world"

    def test_conditional_zero(self, capsys):
        run_with_io(
            "input integer 0 ==\n    ('zero' print) if",
            input_lines=["0"],
        )
        assert capsys.readouterr().out == "zero"

    def test_conditional_nonzero(self, capsys):
        run_with_io(
            "input integer 0 ==\n    ('zero' print) if",
            input_lines=["5"],
        )
        assert capsys.readouterr().out == ""

    def test_negative(self, capsys):
        run_with_io(
            """input integer dup 0 <
                (drop 'negative' print)
                (0 >
                    ('positive' print) if) if-else""",
            input_lines=["-3"],
        )
        assert capsys.readouterr().out == "negative"

    def test_positive(self, capsys):
        run_with_io(
            """input integer dup 0 <
                (drop 'negative' print)
                (0 >
                    ('positive' print) if) if-else""",
            input_lines=["5"],
        )
        assert capsys.readouterr().out == "positive"

    def test_zero_neither(self, capsys):
        run_with_io(
            """input integer dup 0 <
                (drop 'negative' print)
                (0 >
                    ('positive' print) if) if-else""",
            input_lines=["0"],
        )
        assert capsys.readouterr().out == ""

    def test_loop_example(self, capsys):
        run_with_io("""
            (1 + ) 'increment' def
            1 'i' set
            (self
             i 10 <=
                (i print i increment 'i' set exec) if)
            exec drop
        """)
        expected = "".join(f"{i}" for i in range(1, 11))
        assert capsys.readouterr().out == expected


class TestTCO:
    """Verify tail-call optimization doesn't blow the stack."""

    def test_large_loop(self):
        """Loop 10000 times without stack overflow."""
        interp = Interpreter()
        interp.run("""
            (1 +) 'increment' def
            1 'i' set
            (self
             i 10000 <=
                (i increment 'i' set exec) if)
            exec drop
        """)
        # If we get here without RecursionError, TCO works
        kind, val = interp.namespace['i']
        assert val.value == 10001


def _run_in_selfinterp(
    prog,
    capsys,
    input_lines: list[str] | None = None,
    program_args: list[str] | None = None,
):
    """Run a Hairpin program through the self-interpreter."""
    interp = Interpreter()
    interp.run(_SELFINTERP_SOURCE)
    interp.stack.append(HString(prog))
    command = 'run-hairpin'
    if program_args is not None:
        interp.stack.append(_string_list(program_args))
        command = 'run-hairpin-with-args'
    if input_lines is not None:
        import builtins

        orig = builtins.input
        it = iter(input_lines)
        builtins.input = lambda *a: next(it)
        try:
            interp.run(command)
        finally:
            builtins.input = orig
    else:
        interp.run(command)
    return capsys.readouterr().out


def _run_selfinterp_entrypoint(
    program_path: str,
    capsys,
    program_args: list[str] | None = None,
    input_lines: list[str] | None = None,
):
    """Run examples/selfinterp.hp as a host program that loads another Hairpin file."""
    interp = Interpreter(program_args=[program_path, *(program_args or [])])
    if input_lines is not None:
        import builtins

        orig = builtins.input
        it = iter(input_lines)
        builtins.input = lambda *a: next(it)
        try:
            interp.run(_SELFINTERP_SOURCE)
        finally:
            builtins.input = orig
    else:
        interp.run(_SELFINTERP_SOURCE)
    return capsys.readouterr().out


class TestSelfInterpreter:
    """Test the Hairpin self-interpreter."""

    def test_arithmetic(self, capsys):
        assert _run_in_selfinterp('1 2 + print', capsys) == '3'

    def test_subtraction(self, capsys):
        assert _run_in_selfinterp('10 3 - print', capsys) == '7'

    def test_multiplication(self, capsys):
        assert _run_in_selfinterp('6 7 * print', capsys) == '42'

    def test_division(self, capsys):
        assert _run_in_selfinterp('100 4 / print', capsys) == '25'

    def test_modulo(self, capsys):
        assert _run_in_selfinterp('17 5 % print', capsys) == '2'

    def test_comparison(self, capsys):
        assert _run_in_selfinterp('3 5 < print', capsys) == 'true'
        assert _run_in_selfinterp('5 3 < print', capsys) == 'false'

    def test_equality(self, capsys):
        assert _run_in_selfinterp('42 42 == print', capsys) == 'true'
        assert _run_in_selfinterp('1 2 == print', capsys) == 'false'

    def test_dup_swap_drop(self, capsys):
        assert _run_in_selfinterp('5 dup * print', capsys) == '25'
        assert _run_in_selfinterp('1 2 swap - print', capsys) == '1'

    def test_not(self, capsys):
        assert _run_in_selfinterp('true not print', capsys) == 'false'

    def test_if_else(self, capsys):
        assert _run_in_selfinterp('true (1) (2) if-else print', capsys) == '1'
        assert _run_in_selfinterp('false (1) (2) if-else print', capsys) == '2'

    def test_if(self, capsys):
        assert _run_in_selfinterp('true (42 print) if', capsys) == '42'

    def test_exec(self, capsys):
        assert _run_in_selfinterp('(1 2 +) exec print', capsys) == '3'

    def test_string(self, capsys):
        out = _run_in_selfinterp("'hello' print", capsys)
        assert out == 'hello'

    def test_set_get(self, capsys):
        out = _run_in_selfinterp("42 'x' set x print", capsys)
        assert out == '42'

    def test_def(self, capsys):
        out = _run_in_selfinterp("(dup *) 'square' def 5 square print", capsys)
        assert out == '25'

    def test_def_with_args(self, capsys):
        out = _run_in_selfinterp("(1 +) 'inc' def 10 inc inc inc print", capsys)
        assert out == '13'

    def test_negative_number(self, capsys):
        assert _run_in_selfinterp('-5 3 + print', capsys) == '-2'

    def test_cons_head_tail(self, capsys):
        assert _run_in_selfinterp('1 2 cons head print', capsys) == '1'
        assert _run_in_selfinterp('1 2 cons tail print', capsys) == '2'

    def test_comment(self, capsys):
        out = _run_in_selfinterp('# a comment\n42 print', capsys)
        assert out == '42'

    def test_nested_code(self, capsys):
        out = _run_in_selfinterp('(1 2 +) exec (3 *) exec print', capsys)
        assert out == '9'

    def test_sequential_runs(self, capsys):
        """Multiple programs through the same self-interpreter instance."""
        interp = Interpreter()
        interp.run(_SELFINTERP_SOURCE)
        for prog in ['1 2 + print', '10 3 * print', '5 5 == print']:
            interp.stack.append(HString(prog))
            interp.run('run-hairpin')
        out = capsys.readouterr().out
        assert out == '330true'

    def test_self_exec_loop(self, capsys):
        prog = "5 (self 'loop' set dup print 1 - dup 0 > (loop exec) () if-else) exec"
        assert _run_in_selfinterp(prog, capsys) == '54321'

    def test_nested_code_in_exec(self, capsys):
        out = _run_in_selfinterp('(true (42 print) if) exec', capsys)
        assert out == '42'

    def test_code_literal_type(self, capsys):
        assert _run_in_selfinterp('(1 2 +) type print', capsys) == 'code'

    def test_code_truthiness(self, capsys):
        assert _run_in_selfinterp('() not print', capsys) == 'true'
        assert _run_in_selfinterp('(1) not print', capsys) == 'false'

    def test_self_returns_original_code_object(self, capsys):
        prog = (
            "0 'count' set "
            "(count 1 + 'count' set self 'loop' set count 2 < (loop exec) if) "
            "exec count print"
        )
        assert _run_in_selfinterp(prog, capsys) == '2'

    def test_self_interpreter_tco(self, capsys):
        prog = "1 'i' set (self i 3000 <= (i 1 + 'i' set exec) if) exec i print"
        assert _run_in_selfinterp(prog, capsys) == '3001'

    def test_float_literals(self, capsys):
        assert _run_in_selfinterp('3.14 print', capsys) == '3.14'
        assert _run_in_selfinterp('1e2 print', capsys) == '100.0'

    def test_float_primitive(self, capsys):
        assert _run_in_selfinterp("'3.25' float print", capsys) == '3.25'
        assert _run_in_selfinterp('42 float print', capsys) == '42.0'

    def test_input_primitive(self, capsys):
        assert _run_in_selfinterp('input print', capsys, input_lines=['hello']) == 'hello'

    def test_program_args_primitive(self, capsys):
        assert (
            _run_in_selfinterp(
                'program-args print',
                capsys,
                program_args=['alpha', 'beta'],
            )
            == '(alpha beta)'
        )

    def test_read_file_primitive(self, capsys, tmp_path):
        data_path = tmp_path / 'data.txt'
        data_path.write_text('hello from file', encoding='utf-8')
        assert (
            _run_in_selfinterp(
                'program-args head read-file print',
                capsys,
                program_args=[str(data_path)],
            )
            == 'hello from file'
        )

    def test_non_tail_if_continues_execution(self, capsys):
        prog = (
            "0 'i' set "
            "(self i 3 <= "
            "  (i 2 == ('T' print) if "
            "   i print "
            "   i 1 + 'i' set "
            "   exec) if) "
            "exec drop "
            "'|' print i print"
        )
        assert _run_in_selfinterp(prog, capsys) == '01T23|4'

    def test_source_load_is_quiet_without_program_args(self, capsys):
        interp = Interpreter()
        interp.run(_SELFINTERP_SOURCE)
        assert capsys.readouterr().out == ''

    def test_file_runner_forwards_program_args(self, capsys, tmp_path):
        child_path = tmp_path / 'child.hp'
        child_path.write_text('program-args print', encoding='utf-8')
        assert (
            _run_selfinterp_entrypoint(
                str(child_path),
                capsys,
                program_args=['alpha', 'beta'],
            )
            == '(alpha beta)'
        )

    def test_file_runner_executes_fib_example(self, capsys):
        out = _run_selfinterp_entrypoint(_fib_example_path, capsys)
        assert out.count('\n') == 10
        assert 'F(1000) =' in out
        assert 'F(10000) =' in out

    def test_parse_error_unmatched_rparen(self, capsys):
        out = _run_in_selfinterp(')', capsys)
        assert 'Parse error' in out

    def test_parse_error_unclosed_code(self, capsys):
        out = _run_in_selfinterp('(1 2', capsys)
        assert 'Parse error' in out

    def test_undefined_word_halts(self, capsys):
        out = _run_in_selfinterp('1 nosuch 2 print', capsys)
        assert "Undefined word 'nosuch'" in out
        assert not out.endswith('2')

    def test_extended_string_escapes(self, capsys):
        prog = "'\\r\\\\\\'\\0\\a\\b\\f\\v' print"
        assert _run_in_selfinterp(prog, capsys) == "\r\\'\0\a\b\f\v"

    def test_fibonacci(self, capsys):
        """Compute first 10 Fibonacci numbers via the self-interpreter."""
        prog = (
            "0 'a' set 1 'b' set 1 'i' set "
            "(self i 10 <= "
            "  (a print '\\n' print "
            "   b 'temp' set a b + 'b' set temp 'a' set "
            "   i 1 + 'i' set exec) if) exec drop"
        )
        out = _run_in_selfinterp(prog, capsys)
        assert out == '0\n1\n1\n2\n3\n5\n8\n13\n21\n34\n'
