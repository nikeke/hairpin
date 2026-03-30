# Hairpin

## Project Overview

Hairpin is a dynamically-typed RPN (Reverse Polish Notation) stack-based language. The interpreter is a Python 3.13 prototype structured as a multi-module package. The language spec is in `notes.md`.

## Commands

```bash
# Activate the venv (always do this first)
source venv/bin/activate

# Run a Hairpin program
python -m hairpin program.hp

# Start the REPL
python -m hairpin

# Run all tests
pytest

# Run the self-interpreter parity coverage
pytest tests/test_integration.py -k selfinterp

# Run a single test file
pytest tests/test_tokenizer.py

# Run a single test by name
pytest tests/test_tokenizer.py -k test_integer_literal
```

## Architecture

The interpreter pipeline is: **source text → tokenizer → parser → interpreter**.

- `hairpin/tokenizer.py` — Lexes source into tokens (integers, floats, single-quoted strings, booleans, words, parens). Comment lines starting with `#` are stripped.
- `hairpin/parser.py` — Converts token stream into instruction sequences. `(...)` groups become code objects.
- `hairpin/types.py` — Runtime value types (`HInt`, `HFloat`, `HString`, `HBool`, `HCode`, `HNil`, `HCons`). All Hairpin values are wrapped in these types.
- `hairpin/interpreter.py` — Executes instruction sequences against a data stack and a single namespace dictionary. Uses a trampoline in `execute_in_context` for tail-call optimization. `_TailCall` sentinels propagate through `exec`, `if`, and `if-else` in tail position.
- `hairpin/primitives.py` — All built-in words (`get`, `set`, `def`, `if`, `+`, `print`, `dup`, `type`, `chars`, `string`, etc.) registered into the interpreter.
- `hairpin/repl.py` — Interactive REPL with `/`-prefixed commands (`/stack`, `/words`, `/clear`, `/reset`, `/help`, `/builtins`). New commands are added via the `@repl_command` decorator.
- `hairpin/__main__.py` — CLI entry point dispatching to file execution or REPL.
- `examples/selfinterp.hp` — Self-interpreter: a Hairpin program that tokenizes, parses, and evaluates Hairpin source code. It uses cons lists for tokens, AST, meta-stack, and environment, plus a tagged representation for target-language code objects so `type`, `self`, and tail-position execution more closely mirror the host interpreter.
- `tests/test_integration.py` — End-to-end coverage for notes.md examples and self-interpreter parity, including code-object typing, float/input support, parse/runtime error behavior, and deep TCO loops.

## Key Language Semantics

These are non-obvious design decisions — refer to `notes.md` for the full spec:

- **Single namespace**: `set` (store value) and `def` (store executable code) share the same namespace. A `def`'d name can be overwritten with `set` and vice versa.
- **Same-type operators**: Arithmetic and comparison require identical types on both operands. The sole exception is integer-string multiplication, which works in both operand orders.
- **Boolean coercion**: Only conditional primitives (`if`, `if-else`, `not`) coerce to boolean. Falsy values: `0`, `0.0`, `''`, `()` (empty code object), `false`, `nil`.
- **Error handling**: All runtime errors halt execution immediately with a message. No exceptions or recovery.
- **TCO**: `exec`, `if`, and `if-else` perform tail-call optimization via trampoline when in tail position (last instruction in a code object). `_current_code` is pinned to the original `execute_in_context` entry so `self` always returns the correct code object through TCO iterations.
- **Cons lists**: `nil` is the empty list (falsy singleton). `cons` creates a cell from head and tail. `head` and `tail` extract parts. Lists print as `(1 2 3)`, dotted pairs as `(1 . 2)`.

When changing semantics that affect `examples/selfinterp.hp`, update the self-interpreter and `tests/test_integration.py` together so the host interpreter and self-interpreter stay aligned.

When updating `README.md`, describe the current state directly. Avoid changelog-style phrasing like "now", "still", or comparisons against an older state unless the section is explicitly historical.
