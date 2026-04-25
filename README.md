# Hairpin

A dynamically-typed, stack-based toy programming language with RPN (Reverse Polish Notation) syntax.

## Quick Start

```bash
# Install the package in editable mode
python -m pip install -e .

# Run a program
python -m hairpin program.hp [arg ...]

# Start the REPL
python -m hairpin
```

Requires Python 3.13+.

Hairpin is meant for experimentation and learning rather than production use.

## Language Overview

Hairpin programs are sequences of words evaluated left to right. Values are pushed onto a stack; words operate on the stack.

```
# Hello world
'hello, world' print

# Arithmetic: 3 + 4 = 7
3 4 + print

# Define a function
(dup *) 'square' def
7 square print          # 49
```

### Types

- **Integers** — arbitrary precision: `42`, `-7`, `0`
- **Floats** — IEEE 754: `3.14`, `-0.5`
- **Strings** — single-quoted with C-like escapes such as `\n`, `\t`, `\r`, `\\`, `\'`, `\0`, `\a`, `\b`, `\f`, `\v`: `'hello'`
- **Booleans** — `true`, `false`
- **Code objects** — parenthesized code: `(1 2 +)`
- **Cons cells** — pairs built with `cons`, inspected with `head`/`tail`
- **Nil** — `nil`, the empty list

### Boolean Coercion

Only conditional words (`if`, `if-else`, `not`) coerce to boolean. Falsy values: `0`, `0.0`, `''`, `()`, `false`, `nil`. Everything else is truthy.

### Words and Definitions

All names live in a single namespace. `set` stores a value; `def` stores executable code:

```
42 'x' set              # x is a value — using x pushes 42
(1 +) 'increment' def   # increment is code — using it runs (1 +)
```

### Control Flow

```
# Conditional
x 0 > ('positive' print) if

# If-else
x 0 > ('positive' print) ('non-positive' print) if-else

# Loop via self/exec
1 (self 'loop' set
   dup print
   1 + dup 10 <=
     (loop exec) () if-else
) exec drop
```

`exec`, `if`, and `if-else` perform tail-call optimization in tail position.

### Cons Lists

```
1 2 cons             # (1 . 2) — a dotted pair
1 2 cons head        # 1
1 2 cons tail        # 2

# Build a proper list: (1 2 3)
1 2 nil cons cons cons
```

`nil` is falsy; cons cells are truthy — use this for recursion base cases.

### String Processing

```
'hello' chars        # ('h' 'e' 'l' 'l' 'o') — list of single-char strings
'h' 'i' nil cons cons string  # 'hi' — concatenate list of strings
```

## Primitives

| Word | Stack Effect | Description |
|------|-------------|-------------|
| `set` | `VALUE NAME --` | Store a value |
| `get` | `NAME -- VALUE` | Retrieve a value by name |
| `def` | `CODE NAME --` | Define an executable word |
| `self` | `-- CODE` | Push the current code object |
| `exec` | `CODE --` | Execute a code object |
| `if` | `COND CODE --` | Execute code if condition is truthy |
| `if-else` | `COND THEN ELSE --` | Execute one of two code objects |
| `not` | `VALUE -- BOOL` | Logical negation |
| `dup` | `A -- A A` | Duplicate top of stack |
| `drop` | `A --` | Discard top of stack |
| `swap` | `A B -- B A` | Swap top two values |
| `+` `-` `*` `/` `%` | `A B -- C` | Arithmetic (same-type operands) |
| `==` `!=` `<` `<=` `>` `>=` | `A B -- BOOL` | Comparison |
| `integer` `float` | `VAL -- NUM` | Type conversion |
| `type` | `VAL -- STRING` | Type name as string |
| `print` | `VAL --` | Print a value |
| `input` | `-- STRING` | Read a line from stdin |
| `program-args` | `-- LIST` | Current program arguments as a list of strings |
| `read-file` | `PATH -- STRING` | Read a UTF-8 text file into a string |
| `cons` | `H T -- CONS` | Create a cons cell |
| `head` `tail` | `CONS -- VAL` | Decompose a cons cell |
| `chars` | `STRING -- LIST` | String to list of characters |
| `string` | `LIST -- STRING` | List of strings to string |

## Examples

### Fibonacci Numbers (`examples/fib.hp`)

Computes Fibonacci numbers up to F(10000) using arbitrary-precision integers:

```
python -m hairpin examples/fib.hp
```

### Prime Counting (`examples/primes.hp`)

Counts primes up to 10,000 with a cons-list Sieve of Eratosthenes:

```
python -m hairpin examples/primes.hp
```

### Self-Interpreter (`examples/selfinterp.hp`)

A Hairpin interpreter written in Hairpin itself as a self-interpreter demo — tokenizer, parser, and evaluator in a single self-contained source file. It supports typed code objects, preserves the original current code object for `self`, performs tail-call-aware `exec`/`if`/`if-else`, supports float literals plus `float`/`input`, can access `program-args` and `read-file`, and halts on parse or undefined-word errors with a message.

Internally it uses cons lists for tokens, AST, the meta-stack, and the environment, with a tagged representation for target-language code objects.

Use it as a file runner for another Hairpin program. The first argument is the child program path; any remaining arguments are forwarded to that interpreted program.

```
python -m hairpin examples/selfinterp.hp examples/fib.hp
```

## REPL

The interactive REPL supports readline with tab completion and the following commands:

| Command | Description |
|---------|-------------|
| `/stack` | Print the current stack |
| `/words` | List all defined words |
| `/builtins` | List all built-in primitives |
| `/clear` | Clear the stack |
| `/reset` | Reset the entire interpreter |
| `/help` | Show help |

## Tests

```bash
python -m pip install -e '.[dev]'
pytest

# Lint and formatting checks
ruff check src/hairpin tests benchmarks
ruff format --check src/hairpin tests benchmarks

# Focus on the self-interpreter parity coverage
pytest tests/test_integration.py -k selfinterp
```

## Benchmarks

`benchmarks/run_benchmarks.py` runs a baseline suite aimed at interpreter hot paths that are useful when tinkering with the implementation. It performs 1 warmup run and 5 timed runs per program, and it verifies each benchmark's stdout before reporting timings.

```bash
python benchmarks/run_benchmarks.py
python benchmarks/run_benchmarks.py --markdown
```

The timings below were measured on an AMD Ryzen 5 PRO 5650U machine running Linux after waiting for a low-load window. They reflect the current interpreter, including cached internal bytecode for executed code objects, specialized arithmetic/stack/list/control-flow paths, and tightened tail-call and namespace fast paths in the bytecode engine.

| Benchmark | Description | Median of 5 runs | Individual runs |
|-----------|-------------|------------------|-----------------|
| `countdown` | tail-recursive integer/control-flow loop | 3.576s | 3.569s, 3.580s, 3.576s, 3.600s, 3.575s |
| `fib-mod` | large integer arithmetic with TCO loop | 0.288s | 0.288s, 0.287s, 0.288s, 0.289s, 0.287s |
| `primes-sieve` | cons-list sieve and modulo-heavy filtering | 3.787s | 3.796s, 3.787s, 3.782s, 3.787s, 3.800s |
| `string-roundtrip` | repeated `chars`/`string` round-trips on a large string | 0.607s | 0.607s, 0.608s, 0.606s, 0.607s, 0.607s |
| `list-reverse` | tail-recursive list construction and repeated reversal | 1.990s | 1.987s, 1.990s, 1.985s, 2.010s, 1.997s |

Treat these as comparative baselines rather than fixed targets; they are most useful for measuring changes against the same workload mix on the same machine.

## License

MIT. See [`LICENSE`](LICENSE).
