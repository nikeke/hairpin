# Hairpin

A minimalistic, dynamically-typed, stack-based language with RPN (Reverse Polish Notation) syntax.

## Quick Start

```bash
# Run a program
python -m hairpin program.hp

# Start the REPL
python -m hairpin
```

Requires Python 3.13+.

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

A Hairpin interpreter written in Hairpin itself — tokenizer, parser, and evaluator in a single self-contained source file. It supports typed code objects, preserves the original current code object for `self`, performs tail-call-aware `exec`/`if`/`if-else`, supports float literals plus `float`/`input`, and halts on parse or undefined-word errors with a message.

Internally it uses cons lists for tokens, AST, the meta-stack, and the environment, with a tagged representation for target-language code objects.

```
python -m hairpin examples/selfinterp.hp    # prints 49, then the first 1000 Fibonacci numbers
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
pytest

# Focus on the self-interpreter parity coverage
pytest tests/test_integration.py -k selfinterp
```

## License

MIT. See [`LICENSE`](LICENSE).
