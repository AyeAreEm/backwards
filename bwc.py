from __future__ import annotations
from typing_extensions import Any
from dataclasses import dataclass
from typing import List
import sys
import enum

def usage():
    print("USAGE:")
    print("    bwc.py <file.bw>")
    sys.exit(1)

class TokenType(enum.Enum):
    Plus     = enum.auto()
    Minus    = enum.auto()
    Multiply = enum.auto()
    Divide   = enum.auto()
    Number   = enum.auto()
    Return   = enum.auto()
    EoF      = enum.auto()
    Newline  = enum.auto()

@dataclass
class Token:
    typ: TokenType
    value: Any # union

    @staticmethod
    def get_token(buf: str):
        if buf.isdigit():
            return Token(TokenType.Number, buf)
        elif buf == '+':
            return Token(TokenType.Plus, buf)
        elif buf == '-':
            return Token(TokenType.Minus, buf)
        elif buf == '*':
            return Token(TokenType.Multiply, buf)
        elif buf == '/':
            return Token(TokenType.Divide, buf)
        elif buf == "return":
            return Token(TokenType.Return, buf)
        else:
            return Token(TokenType.EoF, "EoF")

class StmntType(enum.Enum):
    Return = 0

@dataclass
class Stmnt:
    typ: StmntType
    children: List

    def pretty(self, indent):
        leader = ' ' * (indent * 4)

        print(f"{leader}{self.typ}")
        print(f"{leader}{self.typ}.children: ")
        for child in self.children:
            child.pretty(indent + 1)

class ExprType(enum.Enum):
    Plus = 0
    Minus = 1
    Mulitply = 2
    Divide = 3
    IntLit = 4

@dataclass
class Expr:
    typ: ExprType
    value: Any
    children: List[Expr]

    def pretty(self, indent):
        leader = ' ' * (indent) * 4

        print(f"{leader}{self.typ}")
        print(f"{leader}{self.typ}.children: ")
        for child in self.children:
            child.pretty(indent + 1)

def lexer(file: str) -> List[Token]:
    tokens = []
    buf: str = ""

    for ch in file:
        if ch == ' ':
            token = Token.get_token(buf)
            tokens.append(token)
            buf = ""
        elif ch == '\n':
            print(f"lexer buf: {buf}")
            token = Token.get_token(buf)
            tokens.append(token)
            tokens.append(Token(TokenType.Newline, '\n'))
            buf = ""
        else:
            buf += ch

    tokens.append(Token.get_token(buf))

    token, tokentyp = expect(tokens, TokenType.EoF)
    if tokentyp != TokenType.EoF:
        print(f"unexpected token '{token.value}' of type: {tokentyp}")
        exit(1)
    tokens.append(token)

    token, tokentyp = expect(tokens, TokenType.Newline)
    if tokentyp != TokenType.Newline:
        print(f"unexpected token '{token.value}' of type: {tokentyp}")
        exit(1)

    return tokens

def peek(tokens: List[Token], index = 0):
    if index >= len(tokens):
        return Token(TokenType.EoF, "EoF")

    return tokens[index]

def next(tokens: List[Token]):
    if len(tokens) == 0:
        return Token(TokenType.EoF, "EoF")

    return tokens.pop(0)

def expect(tokens: List[Token], expected: TokenType) -> tuple[Token, TokenType]:
    token = next(tokens)
    if expected != token.typ:
        return token, token.typ

    return token, token.typ

def parse_math_expr(tokens: List[Token]) -> Expr:
    stack = []

    while (sym := peek(tokens)):
        if sym.typ == TokenType.EoF or sym.typ == TokenType.Newline:
            next(tokens)
            break

        token = next(tokens)
        match token.typ:
            case TokenType.Plus:
                right = stack.pop()
                left = stack.pop()
                stack.append(Expr(ExprType.Plus, '+', [left, right]))
            case TokenType.Minus:
                right = stack.pop()
                left = stack.pop()
                stack.append(Expr(ExprType.Minus, '-', [left, right]))
            case TokenType.Multiply:
                right = stack.pop()
                left = stack.pop()
                stack.append(Expr(ExprType.Mulitply, '*', [left, right]))
            case TokenType.Divide:
                right = stack.pop()
                left = stack.pop()
                stack.append(Expr(ExprType.Divide, '/', [left, right]))
            case TokenType.Number:
                stack.append(Expr(ExprType.IntLit, token.value, []))
            case _:
                break

    return stack[0]

def parse_expr(tokens: List[Token]):
    if peek(tokens).typ == TokenType.Number:
        return parse_math_expr(tokens)

def parse_return(tokens: List[Token]):
    expect(tokens, TokenType.Return)
    return Stmnt(StmntType.Return, [parse_expr(tokens)])

def parse(tokens: List[Token]):
    if peek(tokens).typ == TokenType.Return:
        return parse_return(tokens)

def emit_exprs(file, exprs: List[Expr]):
    if len(exprs) == 0:
        return

    for expr in exprs:
        match expr.typ:
            case ExprType.IntLit:
                file.write(f"PUSH {expr.value}\n")
            case ExprType.Plus:
                emit_exprs(file, expr.children)
                file.write("ADD\n")
            case ExprType.Mulitply:
                emit_exprs(file, expr.children)
                file.write("MUL\n")

def emit_return(file, stmnt: Stmnt):
    emit_exprs(file, stmnt.children)
    file.write("RET\n")

def emit(file, stmnt: Stmnt):
    match stmnt.typ:
        case StmntType.Return:
            emit_return(file, stmnt)
        
def main():
    args = sys.argv[1:]
    
    if len(args) == 0:
        usage()

    with open(args[0]) as file:
        content = file.read()[::-1]
        tokens = lexer(content)

        print(tokens)

        with open(file.name + ".bc", "w+") as bc_file:
            while (stmnt := parse(tokens)):
                # stmnt.pretty(0)
                emit(bc_file, stmnt)

if __name__ == "__main__":
    main()
