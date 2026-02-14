"""Hairpin tokenizer — lexes source text into tokens."""

from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    BOOLEAN = auto()
    WORD = auto()
    LPAREN = auto()
    NIL = auto()
    RPAREN = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: object
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"


class TokenizerError(Exception):
    def __init__(self, message, line, col):
        super().__init__(f"Tokenizer error at {line}:{col}: {message}")
        self.line = line
        self.col = col


ESCAPE_MAP = {
    'n': '\n',
    't': '\t',
    'r': '\r',
    '\\': '\\',
    "'": "'",
    '0': '\0',
    'a': '\a',
    'b': '\b',
    'f': '\f',
    'v': '\v',
}


def tokenize(source: str) -> list[Token]:
    """Tokenize Hairpin source code into a list of tokens."""
    tokens = []
    lines = source.split('\n')

    for line_num, line_text in enumerate(lines, 1):
        stripped = line_text.lstrip()
        if stripped.startswith('#'):
            continue

        col = 0
        while col < len(line_text):
            ch = line_text[col]

            if ch in ' \t\r':
                col += 1
                continue

            start_col = col + 1  # 1-based

            if ch == '(':
                tokens.append(Token(TokenType.LPAREN, '(', line_num, start_col))
                col += 1
            elif ch == ')':
                tokens.append(Token(TokenType.RPAREN, ')', line_num, start_col))
                col += 1
            elif ch == "'":
                string_val, col = _read_string(line_text, col, line_num)
                tokens.append(Token(TokenType.STRING, string_val, line_num, start_col))
            elif _is_number_start(line_text, col):
                num_token, col = _read_number(line_text, col, line_num)
                tokens.append(num_token)
            else:
                word, col = _read_word(line_text, col)
                if word == 'true':
                    tokens.append(Token(TokenType.BOOLEAN, True, line_num, start_col))
                elif word == 'false':
                    tokens.append(Token(TokenType.BOOLEAN, False, line_num, start_col))
                elif word == 'nil':
                    tokens.append(Token(TokenType.NIL, None, line_num, start_col))
                else:
                    tokens.append(Token(TokenType.WORD, word, line_num, start_col))

    tokens.append(Token(TokenType.EOF, None, len(lines), 0))
    return tokens


def _read_string(line: str, pos: int, line_num: int) -> tuple[str, int]:
    """Read a single-quoted string with C-like backslash escapes."""
    start_col = pos + 1
    pos += 1  # skip opening quote
    chars = []
    while pos < len(line):
        ch = line[pos]
        if ch == '\\':
            pos += 1
            if pos >= len(line):
                raise TokenizerError("Unterminated escape sequence", line_num, start_col)
            esc = line[pos]
            if esc in ESCAPE_MAP:
                chars.append(ESCAPE_MAP[esc])
            else:
                raise TokenizerError(f"Unknown escape sequence: \\{esc}", line_num, pos + 1)
            pos += 1
        elif ch == "'":
            pos += 1  # skip closing quote
            return ''.join(chars), pos
        else:
            chars.append(ch)
            pos += 1
    raise TokenizerError("Unterminated string literal", line_num, start_col)


def _is_number_start(line: str, pos: int) -> bool:
    """Check if current position starts a numeric literal."""
    ch = line[pos]
    if ch.isdigit():
        return True
    if ch == '-' and pos + 1 < len(line) and line[pos + 1].isdigit():
        # Negative number — but only if not preceded by a non-whitespace char
        # (to avoid treating e.g. `3 -` as `3` followed by `-3`)
        # Actually in RPN, `-` as a word is separate. We treat `-` followed by
        # digit as negative number only at start of line or after whitespace/paren.
        if pos == 0:
            return True
        prev = line[pos - 1]
        if prev in ' \t(':
            return True
    return False


def _read_number(line: str, pos: int, line_num: int) -> tuple[Token, int]:
    """Read an integer or float literal."""
    start_col = pos + 1
    start = pos
    if line[pos] == '-':
        pos += 1
    while pos < len(line) and line[pos].isdigit():
        pos += 1
    is_float = False
    if pos < len(line) and line[pos] == '.':
        # Check it's not just a trailing dot
        if pos + 1 < len(line) and line[pos + 1].isdigit():
            is_float = True
            pos += 1  # skip dot
            while pos < len(line) and line[pos].isdigit():
                pos += 1
    # Check for scientific notation
    if pos < len(line) and line[pos] in ('e', 'E'):
        is_float = True
        pos += 1
        if pos < len(line) and line[pos] in ('+', '-'):
            pos += 1
        if pos >= len(line) or not line[pos].isdigit():
            raise TokenizerError("Invalid number literal", line_num, start_col)
        while pos < len(line) and line[pos].isdigit():
            pos += 1

    text = line[start:pos]
    if is_float:
        return Token(TokenType.FLOAT, float(text), line_num, start_col), pos
    else:
        return Token(TokenType.INTEGER, int(text), line_num, start_col), pos


def _read_word(line: str, pos: int) -> tuple[str, int]:
    """Read a word (any non-whitespace, non-paren sequence)."""
    start = pos
    while pos < len(line) and line[pos] not in ' \t\r()':
        pos += 1
    return line[start:pos], pos
