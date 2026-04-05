"""Hairpin REPL — interactive read-eval-print loop."""

import readline

from hairpin.interpreter import Interpreter
from hairpin.types import HairpinError, HInt, HFloat, HString, HBool, HCode, HCons, HNil


def _format_value(val):
    """Format a Hairpin value for display."""
    if isinstance(val, HInt):
        return str(val.value)
    elif isinstance(val, HFloat):
        return str(val.value)
    elif isinstance(val, HString):
        return repr(val.value)
    elif isinstance(val, HBool):
        return "true" if val.value else "false"
    elif isinstance(val, HCode):
        return f"<code: {len(val.instructions)} instructions>"
    elif isinstance(val, HNil):
        return "nil"
    elif isinstance(val, HCons):
        parts = []
        cur = val
        while isinstance(cur, HCons):
            parts.append(_format_value(cur.head))
            cur = cur.tail
        result = "(" + " ".join(parts)
        if not isinstance(cur, HNil):
            result += " . " + _format_value(cur)
        return result + ")"
    return str(val)


REPL_COMMANDS = {}


def repl_command(name, help_text):
    """Decorator to register a REPL command."""
    def decorator(func):
        REPL_COMMANDS[name] = (func, help_text)
        return func
    return decorator


@repl_command("/stack", "Print the stack (top on the right)")
def cmd_stack(interp):
    if not interp.stack:
        print("(empty)")
    else:
        print(" ".join(_format_value(v) for v in interp.stack))


@repl_command("/words", "List defined words")
def cmd_words(interp):
    if not interp.namespace:
        print("(none)")
    else:
        for name, (kind, val) in sorted(interp.namespace.items()):
            if kind == 'value':
                print(f"  {name} = {_format_value(val)}")
            else:
                print(f"  {name} : <code>")


@repl_command("/clear", "Clear the stack")
def cmd_clear(interp):
    interp.stack.clear()
    print("Stack cleared.")


@repl_command("/reset", "Reset the interpreter (stack and namespace)")
def cmd_reset(interp):
    interp.stack.clear()
    interp.clear_namespace()
    print("Interpreter reset.")


@repl_command("/builtins", "List built-in primitives")
def cmd_builtins(interp):
    names = sorted(interp._primitives.keys())
    print(" ".join(names))


@repl_command("/help", "List REPL commands")
def cmd_help(interp):
    for name, (_, help_text) in sorted(REPL_COMMANDS.items()):
        print(f"  {name:10s} {help_text}")


def repl():
    """Start the Hairpin interactive REPL."""
    interp = Interpreter()

    # Register REPL commands on the interpreter so they work anywhere in code
    for name, (func, _) in REPL_COMMANDS.items():
        interp.repl_commands[name] = func

    def completer(text, state):
        candidates = list(REPL_COMMANDS.keys())
        candidates.extend(interp._primitives.keys())
        candidates.extend(interp.namespace.keys())
        matches = [c for c in candidates if c.startswith(text)]
        return matches[state] if state < len(matches) else None

    readline.set_completer(completer)
    readline.set_completer_delims(" \t\n()")
    readline.parse_and_bind("tab: complete")

    print("Hairpin REPL. Type /help for commands, Ctrl+D to exit.")
    while True:
        try:
            line = input("hp> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line.strip():
            continue
        try:
            interp.run(line)
        except HairpinError as e:
            print(f"Error: {e}")
