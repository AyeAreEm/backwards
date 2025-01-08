# backwards virtual machine

from __future__ import annotations
from dataclasses import dataclass
import enum
import sys
from typing import Any, List

VM_STACK = []

def usage():
    print("USAGE:")
    print("    python bwvm.py <file.bw.bc>")
    exit(1)

class OpcodeTyp(enum.Enum):
    Return = enum.auto()
    Push = enum.auto()
    Add = enum.auto()
    Sub = enum.auto()
    Mul = enum.auto()
    Div = enum.auto()
    Int = enum.auto()

@dataclass
class Opcode:
    typ: OpcodeTyp
    value: Any

    @staticmethod
    def get_op(buf: str):
        if buf.isdigit():
            return Opcode(OpcodeTyp.Int, int(buf))

        match buf:
            case "add":
                return Opcode(OpcodeTyp.Add, buf)
            case "sub":
                return Opcode(OpcodeTyp.Sub, buf)
            case "mul":
                return Opcode(OpcodeTyp.Mul, buf)
            case "div":
                return Opcode(OpcodeTyp.Div, buf)
            case "ret":
                return Opcode(OpcodeTyp.Return, buf)
            case "push":
                return Opcode(OpcodeTyp.Push, buf)

def get_opcodes(line: str) -> List[Opcode]:
    opcodes = []

    buf = ""
    for ch in line:
        if ch == ' ':
            opcodes.append(Opcode.get_op(buf.lower()))
            buf = ""
        elif ch == '\n':
            opcodes.append(Opcode.get_op(buf.lower()))
            buf = ""
        else:
            buf += ch

    return opcodes

def peek(opcodes: List[Opcode]):
    if len(opcodes) < 1:
        return None

    return opcodes[0]

def next(opcodes: List[Opcode]):
    if len(opcodes) == 0:
        print("unexpected, called next when nothing left")
        exit(1)

    return opcodes.pop(0)

def expect(opcodes: List[Opcode], expected: OpcodeTyp):
    opcode = next(opcodes)
    if expected != opcode.typ:
        print(f"expected {expected}, found {opcode.typ}... exiting")
        exit(1)

    return opcode

def interpret(line: str):
    opcodes = get_opcodes(line)

    while (_ := peek(opcodes)):
        opcode = next(opcodes)

        match opcode.typ:
            case OpcodeTyp.Add:
                right = VM_STACK.pop()
                assert right.typ == OpcodeTyp.Int
                left = VM_STACK.pop()
                assert left.typ == OpcodeTyp.Int
                VM_STACK.append(Opcode(OpcodeTyp.Int, left.value + right.value))

            case OpcodeTyp.Sub:
                right = VM_STACK.pop()
                assert right.typ == OpcodeTyp.Int
                left = VM_STACK.pop()
                assert left.typ == OpcodeTyp.Int
                VM_STACK.append(Opcode(OpcodeTyp.Int, left.value - right.value))

            case OpcodeTyp.Mul:
                right = VM_STACK.pop()
                assert right.typ == OpcodeTyp.Int
                left = VM_STACK.pop()
                assert left.typ == OpcodeTyp.Int
                VM_STACK.append(Opcode(OpcodeTyp.Int, left.value * right.value))

            case OpcodeTyp.Div:
                right = VM_STACK.pop()
                assert right.typ == OpcodeTyp.Int
                left = VM_STACK.pop()
                assert left.typ == OpcodeTyp.Int
                VM_STACK.append(Opcode(OpcodeTyp.Int, left.value / right.value))

            case OpcodeTyp.Return:
                value = VM_STACK.pop()
                exit(value.value)

            case OpcodeTyp.Push:
                value = expect(opcodes, OpcodeTyp.Int)
                VM_STACK.append(value)


def main():
    args = sys.argv[1:]

    if len(args) == 0:
        usage()

    with open(args[0]) as file:
        content = file.readlines()

        for line in content:
            interpret(line)

if __name__ == "__main__":
    main()
