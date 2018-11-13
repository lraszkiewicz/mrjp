#!/usr/bin/env python3

import antlr4
import os
import sys

from antlr_generated.InstantLexer import InstantLexer
from antlr_generated.InstantParser import InstantParser
from JVMCompiler import JVMCompiler
from LLVMCompiler import LLVMCompiler


def main(argv):
    if len(argv) != 4:
        raise AttributeError('invalid number of arguments to compiler')
    input_file, target_vm, project_dir = argv[1:]
    if not input_file.endswith('.ins'):
        raise AttributeError('input_file must have `ins` extension')

    out_path = os.path.dirname(input_file)
    base_name = os.path.split(input_file)[1][:-4]
    out_base_name = os.path.join(out_path, base_name)

    input_file_stream = antlr4.FileStream(input_file)
    lexer = InstantLexer(input_file_stream)
    token_stream = antlr4.CommonTokenStream(lexer)
    parser = InstantParser(token_stream)
    prog_tree = parser.prog()
    if target_vm == 'jvm':
        compiler = JVMCompiler(base_name)
    elif target_vm == 'llvm':
        compiler = LLVMCompiler()
    else:
        raise AttributeError(f'unknown target VM: `{target_vm}`')

    code = compiler.visit_prog(prog_tree)

    if target_vm == 'llvm':
        ll_file_path = out_base_name + '.ll'
        bc_file_path = out_base_name + '.bc'
        with open(ll_file_path, 'w') as f:
            f.write(code)
            print(f'Saved {ll_file_path}')
        os.system(f'llvm-as {ll_file_path} -o {bc_file_path}')
        print(f'Compiled to {bc_file_path}')
    elif target_vm == 'jvm':
        j_file_path = out_base_name + '.j'
        with open(j_file_path, 'w') as f:
            f.write(code)
            print(f'Saved {j_file_path}')
        jasmin_path = os.path.join(project_dir, 'lib', 'jasmin.jar')
        os.system(f'java -jar {jasmin_path} -d {out_path} {j_file_path}')


if __name__ == '__main__':
    main(sys.argv)
