from __future__ import annotations
from typing_extensions import Any
from dataclasses import dataclass
from typing import List
import sys
import enum

class SymbolTable:
    symbols = {}
    curr_addr = 0

    @staticmethod
    def find(key):
        if key not in SymbolTable.symbols:
            print(f"couldn't find {key} in symbol table")
            exit(1)

        return SymbolTable.symbols[key]

    @staticmethod
    def push(key, value):
        if key not in SymbolTable.symbols:
            addr = SymbolTable.get_next_addr(value)
            SymbolTable.symbols[key] = (addr, value)
            return SymbolTable.symbols[key][0]

        print(f"symbol {key} already in symbol table, can't push to table")
        exit(1)

    @staticmethod
    def get_next_addr(typeinfo: TypeInfo):
        v = SymbolTable.curr_addr + (typeinfo.alignment - 1)
        SymbolTable.curr_addr = (v & ~(typeinfo.alignment - 1)) + typeinfo.size
        return SymbolTable.curr_addr - typeinfo.size

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
    Print    = enum.auto()
    EoF      = enum.auto()
    Newline  = enum.auto()
    Let      = enum.auto()
    If       = enum.auto()
    Else     = enum.auto()
    End      = enum.auto()
    Ident    = enum.auto()
    Equal    = enum.auto()
    Dot      = enum.auto()
    I128     = enum.auto()
    U128     = enum.auto()
    B128     = enum.auto()
    true     = enum.auto()
    false    = enum.auto()
    Undef    = enum.auto()

@dataclass
class Token:
    typ: TokenType
    value: Any

    @staticmethod
    def get_token(buf: str):
        if buf.isdigit():
            return Token(TokenType.Number, buf)

        match buf:
            case "return":
                return Token(TokenType.Return, buf)
            case "print":
                return Token(TokenType.Print, buf)
            case "let":
                return Token(TokenType.Let, buf)
            case "i128":
                return Token(TokenType.I128, buf)
            case "u128":
                return Token(TokenType.U128, buf)
            case "b128":
                return Token(TokenType.B128, buf)
            case "undef":
                return Token(TokenType.Undef, buf)
            case "true":
                return Token(TokenType.true, buf)
            case "false":
                return Token(TokenType.false, buf)
            case "if":
                return Token(TokenType.If, buf)
            case "else":
                return Token(TokenType.Else, buf)
            case "end":
                return Token(TokenType.End, buf)
            case _:
                return Token(TokenType.Ident, buf)
                

class StmntType(enum.Enum):
    Return  = enum.auto()
    VarDecl = enum.auto()
    Print   = enum.auto()
    If      = enum.auto()

@dataclass
class Stmnt:
    typ: StmntType
    typeinfo: TypeInfo
    children: List

    def pretty(self, indent):
        leader = ' ' * (indent * 4)

        print(f"{leader}{self.typ}")
        print(f"{leader}{self.typ}.children: ")
        for child in self.children:
            child.pretty(indent + 1)

class ExprType(enum.Enum):
    Plus     = enum.auto()
    Minus    = enum.auto()
    Mulitply = enum.auto()
    Divide   = enum.auto()
    IntLit   = enum.auto()
    BoolLit  = enum.auto()
    Ident    = enum.auto()

@dataclass
class Expr:
    typ: ExprType
    typeinfo: TypeInfo|None
    value: Any
    children: List[Expr]

    def pretty(self, indent):
        leader = ' ' * (indent) * 4

        print(f"{leader}{self.typ}")
        print(f"{leader}{self.typ}.children: ")
        for child in self.children:
            child.pretty(indent + 1)

class Type(enum.Enum):
    I128 = enum.auto()
    U128 = enum.auto()
    B128 = enum.auto()

@dataclass
class TypeInfo:
    size: int
    alignment: int
    typ: Type

def lexer(file: str) -> List[Token]:
    def try_push_token(tokens, buf, extra_token):
        if len(buf) > 0:
            tokens.append(Token.get_token(buf))

        if extra_token != None:
            tokens.append(extra_token)

        return ""

    tokens = []
    buf: str = ""
    is_comment = False

    for ch in file:
        if is_comment:
            if ch == '\n':
                is_comment = False
            elif ch == '#':
                is_comment = False
            continue

        match ch:
            case ' ':
                buf = try_push_token(tokens, buf, None)
            case '\n':
                buf = try_push_token(tokens, buf, Token(TokenType.Newline, '\n'))
            case '+':
                buf = try_push_token(tokens, buf, Token(TokenType.Plus, '+'))
            case '-':
                buf = try_push_token(tokens, buf, Token(TokenType.Minus, '-'))
            case '*':
                buf = try_push_token(tokens, buf, Token(TokenType.Multiply, '*'))
            case '/':
                buf = try_push_token(tokens, buf, Token(TokenType.Divide, '/'))
            case '=':
                buf = try_push_token(tokens, buf, Token(TokenType.Equal, '='))
            case '.':
                buf = try_push_token(tokens, buf, Token(TokenType.Dot, '.'))
            case '#':
                is_comment = True
            case _:
                buf += ch

    try_push_token(tokens, buf, None)
    return tokens

def peek(tokens: List[Token], index = 0):
    if index >= len(tokens):
        return Token(TokenType.EoF, "EoF")

    return tokens[index]

def next(tokens: List[Token]):
    if len(tokens) == 0:
        return Token(TokenType.EoF, "EoF")

    return tokens.pop(0)

def expect(tokens: List[Token], expected: TokenType) -> Token:
    token = next(tokens)
    if expected != token.typ:
        print(f"expected {expected}, got {token}")
        exit(1)

    return token

def parse_type(tokens: List[Token]) -> TypeInfo:
    token = next(tokens)
    match token.typ:
        case TokenType.I128:
            return TypeInfo(16, 16, Type.I128)
        case TokenType.U128:
            return TypeInfo(16, 16, Type.U128)
        case TokenType.B128:
            return TypeInfo(16, 16, Type.B128)
        case _:
            print(f"expected a type, found {token}")
            exit(1)

def parse_expr_until(tokens: List[Token], delimiter: TokenType):
    token = peek(tokens)

    stack = []

    while (sym := peek(tokens)):
        if sym.typ == TokenType.EoF or sym.typ == delimiter:
            next(tokens)
            break

        token = next(tokens)
        match token.typ:
            case TokenType.Plus:
                right = stack.pop()
                left = stack.pop()
                assert left.typeinfo == right.typeinfo

                stack.append(Expr(ExprType.Plus, left.typeinfo, '+', [left, right]))
            case TokenType.Minus:
                right = stack.pop()
                left = stack.pop()
                assert left.typeinfo == right.typeinfo

                stack.append(Expr(ExprType.Minus, left.typeinfo, '-', [left, right]))
            case TokenType.Multiply:
                right = stack.pop()
                left = stack.pop()
                assert left.typeinfo == right.typeinfo

                stack.append(Expr(ExprType.Mulitply, left.typeinfo, '*', [left, right]))
            case TokenType.Divide:
                right = stack.pop()
                left = stack.pop()
                assert left.typeinfo == right.typeinfo

                stack.append(Expr(ExprType.Divide, left.typeinfo, '/', [left, right]))
            case TokenType.Number:
                expect(tokens, TokenType.Dot)
                vartype = parse_type(tokens)
                stack.append(Expr(ExprType.IntLit, vartype, token.value, []))
            case TokenType.Ident:
                addr, typeinfo = SymbolTable.find(token.value)
                stack.append(Expr(ExprType.Ident, typeinfo, addr, []))
            case TokenType.true | TokenType.false:
                stack.append(Expr(ExprType.BoolLit, TypeInfo(16, 16, Type.B128), 0 if token.value == "false" else 1, []))
            case _:
                break

    return stack[0]

def parse_return(tokens: List[Token]):
    expect(tokens, TokenType.Return)
    expr = parse_expr_until(tokens, TokenType.Newline)
    assert expr != None
    assert expr.typeinfo != None
    return Stmnt(StmntType.Return, expr.typeinfo, [expr])

def parse_print(tokens: List[Token]):
    expect(tokens, TokenType.Print)
    expr = parse_expr_until(tokens, TokenType.Newline)
    assert expr != None
    assert expr.typeinfo != None
    return Stmnt(StmntType.Print, expr.typeinfo, [expr])

def parse_vardecl(tokens: List[Token]):
    expect(tokens, TokenType.Let)
    varname = expect(tokens, TokenType.Ident)
    expect(tokens, TokenType.Equal)

    value = parse_expr_until(tokens, TokenType.Newline)
    assert value != None
    assert value.typeinfo != None

    addr = SymbolTable.push(varname.value, value.typeinfo)
    
    return Stmnt(StmntType.VarDecl, value.typeinfo, [addr, value])

def parse_block(tokens: List[Token]) -> List[Stmnt]:
    body = []
    while (stmnt := parse(tokens)) is not None:
        body.append(stmnt)

    return body

def parse_if(tokens: List[Token]):
    expect(tokens, TokenType.If)
    condition = parse_expr_until(tokens, TokenType.Newline)
    assert condition.typeinfo == TypeInfo(16, 16, Type.B128)

    if_body = parse_block(tokens)

    else_body = []
    if peek(tokens).typ == TokenType.Else:
        next(tokens)
        else_body = parse_block(tokens)

    expect(tokens, TokenType.End)

    return Stmnt(StmntType.If, condition.typeinfo, [condition, if_body, else_body])

def parse(tokens: List[Token]):
    token = peek(tokens)
    if token == None:
        return

    # TODO: numbers or strings without any "statement" should just be pushed
    match token.typ:
        case TokenType.Return:
            return parse_return(tokens)
        case TokenType.Print:
            return parse_print(tokens)
        case TokenType.Let:
            return parse_vardecl(tokens)
        case TokenType.If:
            return parse_if(tokens)
        case TokenType.EoF:
            return
        case TokenType.Newline:
            next(tokens)
            return parse(tokens)

def typ_to_string(typ: Type) -> str:
    match typ:
        case Type.I128:
            return "i128"
        case Type.U128:
            return "u128"
        case Type.B128:
            return "b128"

def emit_expr(expr: Expr):
    match expr.typ:
        case ExprType.Ident:
            return [f"GET {expr.value}"]
        case ExprType.IntLit:
            return [f"PUSH {hex(int(expr.value))}; {expr.value}"]
        case ExprType.BoolLit:
            return [f"PUSH {hex(int(expr.value))}; {"false" if expr.value == 0 else "true"}"]
        case ExprType.Plus:
            assert expr.typeinfo != None
            str_typ = typ_to_string(expr.typeinfo.typ)
            res = []
            for child in expr.children:
                res.extend(emit_expr(child))

            return res + [f"ADD.{str_typ}"]
        case ExprType.Mulitply:
            assert expr.typeinfo != None
            str_typ = typ_to_string(expr.typeinfo.typ)
            res = []
            for child in expr.children:
                res.extend(emit_expr(child))

            return res + [f"MUL.{str_typ}"]
        case ExprType.Minus:
            assert expr.typeinfo != None
            str_typ = typ_to_string(expr.typeinfo.typ)
            res = []
            for child in expr.children:
                res.extend(emit_expr(child))

            return res + [f"SUB.{str_typ}"]
        case ExprType.Divide:
            assert expr.typeinfo != None
            str_typ = typ_to_string(expr.typeinfo.typ)
            res = []
            for child in expr.children:
                res.extend(emit_expr(child))

            return res + [f"DIV.{str_typ}"]

def emit_return(stmnt: Stmnt):
    assert stmnt.typeinfo != None
    str_typ = typ_to_string(stmnt.typeinfo.typ)
    return emit_expr(stmnt.children[0]) + [f"RET.{str_typ}"]

def emit_print(stmnt: Stmnt):
    assert stmnt.typeinfo != None
    str_typ = typ_to_string(stmnt.typeinfo.typ)
    return emit_expr(stmnt.children[0]) + [f"PRINT.{str_typ}"]

def emit_vardecl(stmnt: Stmnt):
    addr, expr, *_ = stmnt.children
    return [*emit_expr(expr)] + [f"SET {addr}"]

def emit_block(stmnts: List[Stmnt]):
    body = []
    for stmnt in stmnts:
        body += emit(stmnt)

    return body

def emit_cmp():
    return [f"CMP"]

def emit_jeq(offset):
    return [f"JEQ {offset}"]

def emit_jmp(offset):
    return [f"JMP {offset}"]

def emit_if(stmnt: Stmnt):
    cond, if_body, else_body = stmnt.children

    cond_bc = emit_expr(cond)
    false_bc = emit_expr(Expr(ExprType.BoolLit, TypeInfo(16, 16, Type.B128), 0, []))
    cmp_bc = emit_cmp()

    if_bbc = emit_block(if_body)
    jmp_if_bc = emit_jmp(len(if_bbc))
    else_bbc = emit_block(else_body)
    jeq_else_bc = emit_jeq(len(if_bbc) + 1)

    return cond_bc + false_bc + cmp_bc + jeq_else_bc + if_bbc + jmp_if_bc + else_bbc

def emit(stmnt: Stmnt):
    match stmnt.typ:
        case StmntType.Return:
            return emit_return(stmnt)
        case StmntType.Print:
            return emit_print(stmnt)
        case StmntType.VarDecl:
            return emit_vardecl(stmnt)
        case StmntType.If:
            return emit_if(stmnt)
        
def main():
    args = sys.argv[1:]
    
    if len(args) == 0:
        usage()

    with open(args[0]) as file:
        content = file.read()[::-1]
        tokens = lexer(content)

        instructs = []
        with open(file.name + ".bc", "w+") as bc_file:
            while (stmnt := parse(tokens)) is not None:
                instructs += emit(stmnt)

            instructs = [f"PREALLOC {SymbolTable.curr_addr}"] + instructs
            bc_file_content = '\n'.join(instructs)
            bc_file.write(bc_file_content)

if __name__ == "__main__":
    main()
