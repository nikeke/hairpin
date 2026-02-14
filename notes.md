# Hairpin

Let's design and implement Hairpin, a dynamically-typed RPN language. It should be minimalistic and have a highly consistent syntax and semantics. We'll first design the language syntax and semantics, and then implement a prototype in Python. Later, we'll make it faster either by compiling with LLVM or recoding the interpreter in Rust.

## Types

The supported types are:

* arbitrary-length integers, with usual syntax
* floating-point numbers, with usual syntax
* immutable strings, single-quoted, with C-like backslash quoting
* code objects, syntactically represented as code inside parentheses
* Boolean values true and false

The only composite type is the cons list, built from cons cells. `nil` is the empty list (falsy). Cons cells are truthy.

## Coercion Rules

Conditional-execution primitives coerce the condition value to a Boolean. Zeros, empty strings, empty code objects and nil are coerced to false. All other values, including cons cells, are coerced to true.

Arithmetic and comparison operators support only operands of the identical type. The only exception is Python-style integer-string multiplication.

## Comments

Lines starting with # are comments that are ignored by the parser.

## Error Handling

All runtime errors (type errors, stack underflow, undefined words, etc.) stop the execution of all code with a message.

## Primitives

Some primitive words are:

* `get` - Gets the value of a word named by a string. [NAME -- VALUE]
* `set` - Sets the value of a word named by a string. [VALUE NAME --]
* `def` - Defines an executable word. [CODE NAME --]
* `self` - Gets the current code object. [-- CODE]
* `exec` - Executes a code object, performing tail-call optimization when possible. [CODE --]
* `if` - Conditionally executes a code object. [VALUE CODE --]
* `if-else` - Conditionally executes one of two code objects. [VALUE THEN ELSE --]
* `not` - Logically negates a value coerced to a Boolean. [VALUE -- BOOLEAN]
* `+` `-` `*` `/` `%` - Perform usual operations on values. [VALUE1 VALUE2 -- VALUE3]
* `==` `!=` `<` `<=` `>` `>=` - Compare values. [VALUE1 VALUE2 -- BOOLEAN]
* `integer` `float` - Convert to a specified type. [VALUE -- NUMBER]
* `type` - Returns the type name as a string ("integer", "float", "string", "boolean", "code", "cons", "nil"). [VALUE -- STRING]
* `print` - Prints a value to the standard output. [VALUE --]
* `input` - Reads a string from the standard input. [-- STRING]
* `dup` - Duplicates the TOS. [VALUE -- VALUE VALUE]
* `drop` - Drop the TOS. [VALUE --]
* `swap` - Swaps the TOS and the NOS. [VALUE1 VALUE2 -- VALUE2 VALUE1]
* `cons` - Creates a cons cell. [HEAD TAIL -- CONS]
* `head` - Gets the head of a cons cell. [CONS -- VALUE]
* `tail` - Gets the tail of a cons cell. [CONS -- VALUE]
* `chars` - Converts a string to a list of single-character strings. [STRING -- LIST]
* `string` - Converts a list of strings to a concatenated string. [LIST -- STRING]

## Other Words

The value of words set using the `set` primitive are fetched when the word itself is used in the code.

The code of executable words defined using the `def` primitive is executed when the word itself is used in the code.

## Examples

```
# just say hello
'hello, world' print
```

```
# the first conditional
input integer 0 ==
    ('zero' print) if
```

```
input integer dup 0 <
    (drop 'negative' print)
    (0 >
        ('positive' print) if) if-else
```

```
# define a function
(1 + ) 'increment' def

# print the first ten integers
1 'i' set
(self
 i 10 <=
    (i print i increment 'i' set exec) if)
exec drop
```
