"""Hairpin parser — converts tokens into instruction sequences."""

from dataclasses import dataclass

from hairpin.tokenizer import Token, TokenType, tokenize
from hairpin.types import HInt, HFloat, HString, HBool, HCode, HairpinError, NIL


class ParseError(HairpinError):
    def __init__(self, message, line=0, col=0):
        super().__init__(f"Parse error at {line}:{col}: {message}")
        self.line = line
        self.col = col


@dataclass
class PushLiteral:
    """Instruction to push a literal value onto the stack."""
    value: object


@dataclass
class WordRef:
    """Instruction to look up and execute/fetch a word."""
    name: str
    line: int = 0
    col: int = 0


def parse(source: str) -> list:
    """Parse source code into a list of instructions."""
    tokens = tokenize(source)
    instructions, pos = _parse_body(tokens, 0, top_level=True)
    return instructions


def _parse_body(tokens: list[Token], pos: int, top_level: bool = False) -> tuple[list, int]:
    """Parse a sequence of instructions until RPAREN or EOF."""
    instructions = []
    while pos < len(tokens):
        tok = tokens[pos]

        if tok.type == TokenType.EOF:
            if not top_level:
                raise ParseError("Unexpected end of input inside code object", tok.line, tok.col)
            break

        if tok.type == TokenType.RPAREN:
            if top_level:
                raise ParseError("Unexpected ')'", tok.line, tok.col)
            return instructions, pos + 1

        if tok.type == TokenType.LPAREN:
            body, pos = _parse_body(tokens, pos + 1, top_level=False)
            instructions.append(PushLiteral(HCode(body, source_line=tok.line)))
        elif tok.type == TokenType.INTEGER:
            instructions.append(PushLiteral(HInt(tok.value)))
            pos += 1
        elif tok.type == TokenType.FLOAT:
            instructions.append(PushLiteral(HFloat(tok.value)))
            pos += 1
        elif tok.type == TokenType.STRING:
            instructions.append(PushLiteral(HString(tok.value)))
            pos += 1
        elif tok.type == TokenType.BOOLEAN:
            instructions.append(PushLiteral(HBool(tok.value)))
            pos += 1
        elif tok.type == TokenType.NIL:
            instructions.append(PushLiteral(NIL))
            pos += 1
        elif tok.type == TokenType.WORD:
            instructions.append(WordRef(tok.value, line=tok.line, col=tok.col))
            pos += 1
        else:
            raise ParseError(f"Unexpected token: {tok}", tok.line, tok.col)

    return instructions, pos
