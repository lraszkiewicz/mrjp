#!/usr/bin/env python3

import antlr4
import sys

from antlr_generated.InstantLexer import InstantLexer
from antlr_generated.InstantParser import InstantParser

from JVMListener import JVMListener
from LLVMListener import LLVMListener


def main(filename, target_vm):
    input_file_stream = antlr4.FileStream(filename)
    lexer = InstantLexer(input_file_stream)
    token_stream = antlr4.CommonTokenStream(lexer)
    parser = InstantParser(token_stream)
    tree = parser.prog()
    if target_vm == 'jvm':
        listener = JVMListener()
    elif target_vm == 'llvm':
        listener = LLVMListener()
    else:
        print(f'Error: unknown target: "{target_vm}".')
        sys.exit(1)
    walker = antlr4.ParseTreeWalker()
    walker.walk(listener, tree)


if __name__ == '__main__':
    argv = sys.argv[1:]
    if '--llvm' in argv:
        target_vm = 'llvm'
        argv.remove('--llvm')
    elif '--jvm' in argv:
        target_vm = 'jvm'
        argv.remove('--jvm')
    else:
        print('Error: target not specified.')
        sys.exit(1)
    if len(argv) != 1:
        print('Error: invalid number of arguments.')
        sys.exit(1)
    main(argv[0], target_vm)
