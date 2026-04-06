import sys

from hairpin.interpreter import Interpreter
from hairpin.repl import repl
from hairpin.runtime_io import read_text_file
from hairpin.types import HairpinError


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        repl()
        return 0

    filename, *program_args = args
    try:
        source = read_text_file(filename)
        interp = Interpreter(program_args=program_args)
        interp.run(source)
    except HairpinError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
