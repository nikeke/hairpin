# Hairpin

## Project Overview

Hairpin is a dynamically-typed RPN (Reverse Polish Notation) stack-based language. The interpreter is a Python 3.13 prototype structured as a multi-module package.

## Commands

```bash
# Activate the venv (always do this first)
source venv/bin/activate

# Install the package and dev tooling in editable mode
python -m pip install -e '.[dev]'

# Run a Hairpin program
python -m hairpin program.hp

# Start the REPL
python -m hairpin

# Run all tests
pytest

# Run lint and formatting checks
ruff check src/hairpin tests benchmarks
ruff format --check src/hairpin tests benchmarks

# Run the self-interpreter parity coverage
pytest tests/test_integration.py -k selfinterp

# Run a single test file
pytest tests/test_tokenizer.py

# Run a single test by name
pytest tests/test_tokenizer.py -k test_integer_literal
```

## Architecture

The interpreter pipeline is: **source text → tokenizer → parser → interpreter**.

- `src/hairpin/tokenizer.py` — Lexes source into tokens (integers, floats, single-quoted strings, booleans, words, parens). Comment lines starting with `#` are stripped.
- `src/hairpin/parser.py` — Converts token stream into instruction sequences. `(...)` groups become code objects.
- `src/hairpin/types.py` — Runtime value types (`HInt`, `HFloat`, `HString`, `HBool`, `HCode`, `HNil`, `HCons`). `HCode` stores the parsed instruction list and can cache compiled bytecode for repeated execution.
- `src/hairpin/bytecode.py` — Compiles `HCode` instruction lists into compact opcode streams for the host interpreter’s cached bytecode path, including literal-name peepholes, specialized arithmetic/comparison, stack/list, conditional, and `self` opcodes, plus compact records for generic namespace loads.
- `src/hairpin/interpreter.py` — Executes instruction sequences against a data stack and a single namespace dictionary. Uses a trampoline in `execute_in_context` for tail-call optimization and runs cached bytecode for code objects by default, while preserving the tree-walk path as the semantic fallback. Tail-position `exec`, `if`, and `if-else` return the next `HCode` directly to the trampoline, the bytecode path keeps namespace rebinding dynamic, and common stack/list/control helpers are executed inline in `_execute_bytecode`.
- `src/hairpin/primitives.py` — All built-in words (`get`, `set`, `def`, `if`, `+`, `print`, `dup`, `type`, `chars`, `string`, etc.) registered into the interpreter.
- `src/hairpin/repl.py` — Interactive REPL with `/`-prefixed commands (`/stack`, `/words`, `/clear`, `/reset`, `/help`, `/builtins`). New commands are added via the `@repl_command` decorator.
- `src/hairpin/__main__.py` — CLI entry point dispatching to file execution or REPL.
- `examples/selfinterp.hp` — Self-interpreter: a Hairpin program that tokenizes, parses, and evaluates Hairpin source code. It uses cons lists for tokens, AST, meta-stack, and environment, plus a tagged representation for target-language code objects so `type`, `self`, and tail-position execution more closely mirror the host interpreter.
- `tests/test_integration.py` — End-to-end coverage for documented language examples and self-interpreter parity, including code-object typing, float/input support, parse/runtime error behavior, and deep TCO loops.

## Key Language Semantics

These are non-obvious design decisions to keep in mind:

- **Single namespace**: `set` (store value) and `def` (store executable code) share the same namespace. A `def`'d name can be overwritten with `set` and vice versa.
- **Same-type operators**: Arithmetic and comparison require identical types on both operands. The sole exception is integer-string multiplication, which works in both operand orders.
- **Boolean coercion**: Only conditional primitives (`if`, `if-else`, `not`) coerce to boolean. Falsy values: `0`, `0.0`, `''`, `()` (empty code object), `false`, `nil`.
- **Error handling**: All runtime errors halt execution immediately with a message. No exceptions or recovery.
- **TCO**: `exec`, `if`, and `if-else` perform tail-call optimization via trampoline when in tail position (last instruction in a code object). `_current_code` is pinned to the original `execute_in_context` entry so `self` always returns the correct code object through TCO iterations.
- **Bytecode caching**: Executed `HCode` objects are compiled to cached internal bytecode, but namespace lookups remain dynamic at runtime so `def` / `set` rebinding semantics stay intact.
- **Cons lists**: `nil` is the empty list (falsy singleton). `cons` creates a cell from head and tail. `head` and `tail` extract parts. Lists print as `(1 2 3)`, dotted pairs as `(1 . 2)`.

When changing semantics that affect `examples/selfinterp.hp`, update the self-interpreter and `tests/test_integration.py` together so the host interpreter and self-interpreter stay aligned.

When updating `README.md`, describe the current state directly. Avoid changelog-style phrasing like "now", "still", or comparisons against an older state unless the section is explicitly historical.

When refreshing benchmark numbers, check machine load first and wait for a low-load window long enough to make the results comparable before running `benchmarks/run_benchmarks.py`.
