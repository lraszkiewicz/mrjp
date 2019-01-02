#!/usr/bin/env python3

import antlr4
import os
import sys

from antlr_generated.LatteLexer import LatteLexer
from antlr_generated.LatteParser import LatteParser
from LLVMCompiler import LLVMCompiler


def main(argv):
    if len(argv) != 3:
        raise AttributeError('invalid number of arguments to compiler')
    input_file, project_dir = argv[1:]
    if not input_file.endswith('.ins'):
        raise AttributeError('input_file must have `lat` extension')

    out_path = os.path.dirname(input_file)
    base_name = os.path.split(input_file)[1][:-4]
    out_base_name = os.path.join(out_path, base_name)

    input_file_stream = antlr4.FileStream(input_file)
    lexer = LatteLexer(input_file_stream)
    token_stream = antlr4.CommonTokenStream(lexer)
    parser = LatteParser(token_stream)
    prog_tree = parser.program()
    compiler = LLVMCompiler()

    code = compiler.visit_prog(prog_tree)

    ll_file_path = out_base_name + '.ll'
    bc_file_path = out_base_name + '.bc'
    with open(ll_file_path, 'w') as f:
        f.write(code)
        print(f'Saved {ll_file_path}')
    os.system(f'llvm-as {ll_file_path} -o {bc_file_path}')
    print(f'Compiled to {bc_file_path}')


if __name__ == '__main__':
    main(sys.argv)
