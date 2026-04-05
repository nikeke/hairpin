import sys

from hairpin.interpreter import Interpreter
from hairpin.repl import repl


def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        with open(filename) as f:
            source = f.read()
        interp = Interpreter()
        interp.run(source)
    else:
        repl()


if __name__ == "__main__":
    main()
