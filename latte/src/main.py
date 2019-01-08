#!/usr/bin/env python3

# pylint: disable=C0103, C0111

import os
import sys

import antlr4
from antlr_generated.LatteLexer import LatteLexer
from antlr_generated.LatteParser import LatteParser
from LLVMCompiler import LLVMCompiler


class LatteParserErrorListener(antlr4.error.ErrorListener.ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        print('ERROR')
        print(f'Syntax error in line {line}:{column}:')
        print(msg)
        sys.exit(1)


def main(argv):
    if len(argv) != 3:
        raise AttributeError('invalid number of arguments to compiler')
    input_file, project_dir = argv[1:]
    if not input_file.endswith('.lat'):
        raise AttributeError('input_file must have `lat` extension')

    out_path = os.path.dirname(input_file)
    base_name = os.path.split(input_file)[1][:-4]
    out_base_name = os.path.join(out_path, base_name)

    input_file_stream = antlr4.FileStream(input_file)
    lexer = LatteLexer(input_file_stream)
    token_stream = antlr4.CommonTokenStream(lexer)
    parser = LatteParser(token_stream)
    syntax_error_listener = LatteParserErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(syntax_error_listener)
    prog_tree = parser.program()

    compiler = LLVMCompiler()
    code = compiler.visit_prog(prog_tree)

    print('OK')
    # print(code)

    ll_file_path = out_base_name + '.ll'
    runtime_path = os.path.join(project_dir, 'lib', 'runtime.bc')
    bc_no_runtime_path = out_base_name + '_no_runtime.bc'
    bc_final_path = out_base_name + '.bc'
    with open(ll_file_path, 'w') as f:
        f.write(code)
        print(f'Saved {ll_file_path}')
    if os.system(f'llvm-as -o {bc_no_runtime_path} {ll_file_path}') != 0:
        sys.exit(3)
    print(f'Compiled to {bc_no_runtime_path}')
    if os.system(
            f'llvm-link -o {bc_final_path} '
            f'{bc_no_runtime_path} {runtime_path}') != 0:
        sys.exit(4)
    os.remove(bc_no_runtime_path)
    print(f'Linked to runtime: {bc_final_path}')


if __name__ == '__main__':
    main(sys.argv)
