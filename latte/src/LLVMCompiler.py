# pylint: disable=C0103, C0111, R1705

import sys
from typing import List, Union

import antlr4
from antlr_generated.LatteParser import LatteParser


EXT_NOT_IMPLEMENTED = 'Latte extension, not implemented'


def compilation_error(ctx: antlr4.ParserRuleContext, msg: str) -> None:
    line = ctx.start.line
    code = ctx.start.getInputStream().getText(
        ctx.start.start, ctx.stop.stop)
    code = code.split('\n')[0]
    print('ERROR')
    print(f'Compilation error in line {line}:')
    print(code)
    print(f'{msg}.')
    sys.exit(2)


def type_as_str(lattype: LatteParser.LattypeContext) -> str:
    if isinstance(lattype, LatteParser.TypeIntContext):
        return 'int'
    elif isinstance(lattype, LatteParser.TypeStrContext):
        return 'string'
    elif isinstance(lattype, LatteParser.TypeBoolContext):
        return 'boolean'
    elif isinstance(lattype, LatteParser.TypeVoidContext):
        return 'void'
    elif isinstance(lattype, LatteParser.TypeClassContext):
        compilation_error(lattype, EXT_NOT_IMPLEMENTED)
    elif isinstance(lattype, LatteParser.TypeArrayContext):
        compilation_error(lattype, EXT_NOT_IMPLEMENTED)


def type_str_as_llvm(type_str: str) -> str:
    BASIC_TYPES = {
        'int': 'i32',
        'string': 'i8*',
        'boolean': 'i1',
        'void': 'void',
    }
    if type_str in BASIC_TYPES:
        return BASIC_TYPES[type_str]
    elif type_str.endswith('[]'):
        raise NotImplementedError('Latte extension')
    else:
        raise NotImplementedError('Latte extension')


def type_as_llvm(lattype: LatteParser.LattypeContext) -> str:
    if isinstance(lattype, LatteParser.TypeIntContext):
        return 'i32'
    elif isinstance(lattype, LatteParser.TypeStrContext):
        return 'i8*'
    elif isinstance(lattype, LatteParser.TypeBoolContext):
        return 'i1'
    elif isinstance(lattype, LatteParser.TypeVoidContext):
        return 'void'
    elif isinstance(lattype, LatteParser.TypeClassContext):
        compilation_error(lattype, EXT_NOT_IMPLEMENTED)
    elif isinstance(lattype, LatteParser.TypeArrayContext):
        compilation_error(lattype, EXT_NOT_IMPLEMENTED)


class LatSignature:

    def __init__(
            self, ret_type: str, arg_types: List[str] = None,
            code: List[str] = None, name: str = '', ret_val: str = '',
            finish_label: str = None):
        self.ret_type = ret_type
        self.arg_types = arg_types or []
        self.code = code or []
        self.name = name
        self.ret_val = ret_val
        # ret_val is for expressions, might be a register or a constant
        self.finish_label = finish_label

    def __str__(self):
        args = ', '.join(self.arg_types)
        return f'{self.ret_type} {self.name}({args})'


class LLVMCompiler:

    ### Constructor

    def __init__(self):
        self.used_functions = set()
        self.current_function_code = []
        self.next_reg_index = 0
        self.next_label_index = 0
        self.tree_depth = -1
        self.str_consts = {}
        self.builtin_functions = set()
        self.expected_ret_type = None
        self.next_local = 0
        self.var_envs = []
        self.functions = {
            'printInt': LatSignature('void', ['int']),
            'printString': LatSignature('void', ['string']),
            'error': LatSignature('void', []),
            'readInt': LatSignature('int', []),
            'readString': LatSignature('string', []),
            'strcmp': LatSignature('int', ['string', 'string']),
            'strconcat': LatSignature('string', ['string', 'string']),
        }
        for fun in self.functions:
            self.functions[fun].name = fun
            self.builtin_functions.add(fun)


    ### Utils

    def get_str_const(self, str_val: str) -> LatSignature:
        exists = False
        for name, val in self.str_consts.items():
            if val == str_val:
                exists = True
                break
        if not exists:
            name = '@.str{id}'.format(id=len(self.str_consts))
            self.str_consts[name] = str_val
        str_len = len(str_val) + 1
        reg = self.get_new_register()
        self.current_function_code.append(
            f'{reg} = getelementptr [{str_len} x i8], '
            f'[{str_len} x i8]* {name}, i32 0, i32 0')
        return LatSignature('string', ret_val=reg)


    def get_new_register(self) -> str:
        reg = self.next_reg_index
        self.next_reg_index += 1
        return f'%.t{reg}'


    def declare_variable(
            self, ctx: antlr4.ParserRuleContext, var: LatSignature) -> None:
        if var.name in self.var_envs[-1]:
            compilation_error(ctx, f'Variable {var.name} already declared')
        var.ret_val = self.get_new_register()
        llvm_type = type_str_as_llvm(var.ret_type)
        self.current_function_code.append(
            f'{var.ret_val} = alloca {llvm_type}')
        self.var_envs[-1][var.name] = var


    def get_variable(self, ctx: antlr4.ParserRuleContext, var_name: str) \
            -> LatSignature:
        for var_env in reversed(self.var_envs):
            if var_name in var_env:
                return var_env[var_name]
        compilation_error(ctx, f'Variable {var_name} was not declared')


    def load_variable(
            self, ctx: antlr4.ParserRuleContext, var_name: str) -> str:
        var = self.get_variable(ctx, var_name)
        reg = self.get_new_register()
        llvm_type = type_str_as_llvm(var.ret_type)
        self.current_function_code.append(
            f'{reg} = load {llvm_type}, {llvm_type}* {var.ret_val}')
        return (var, reg)


    def get_new_label(self) -> str:
        ind = self.next_label_index
        self.next_label_index += 1
        return f'L{ind}'


    def declare_function(self, ctx: LatteParser.TopDefFunContext) -> None:
        fun_name = ctx.IDENT().getText()
        if fun_name in self.functions:
            compilation_error(
                ctx, f'Multiple declarations of function {fun_name}')
        ret_type = type_as_str(ctx.lattype())
        if fun_name == 'main' and ret_type != 'int':
            compilation_error(ctx, 'Function main has to return int')
        arg_types = [type_as_str(arg.lattype()) for arg in ctx.arg()]
        if fun_name == 'main' and arg_types:
            compilation_error(ctx, 'Function main can not take arguments')
        self.functions[fun_name] = LatSignature(
            ret_type, arg_types=arg_types, name=fun_name)


    ### Program visitor

    def visit_prog(self, ctx: LatteParser.ProgramContext) -> str:
        for child in ctx.children:
            if isinstance(child, LatteParser.TopDefFunContext):
                self.declare_function(child)
            elif isinstance(child, LatteParser.TopDefClassBaseContext):
                compilation_error(ctx, EXT_NOT_IMPLEMENTED)
            elif isinstance(child, LatteParser.TopDefClassDerivedContext):
                compilation_error(ctx, EXT_NOT_IMPLEMENTED)

        for child in ctx.children:
            if isinstance(child, LatteParser.TopDefFunContext):
                self.visit_topdef_fun(child)
            elif isinstance(child, LatteParser.TopDefClassBaseContext):
                compilation_error(ctx, EXT_NOT_IMPLEMENTED)
            elif isinstance(child, LatteParser.TopDefClassDerivedContext):
                compilation_error(ctx, EXT_NOT_IMPLEMENTED)

        if 'main' not in self.functions:
            compilation_error(ctx, 'Function `int main()` was not declared')

        code = ''
        for fun_name in self.builtin_functions:
            if fun_name not in self.used_functions:
                continue
            fun = self.functions[fun_name]
            llvm_ret_type = type_str_as_llvm(fun.ret_type)
            args = ', '.join(type_str_as_llvm(arg) for arg in fun.arg_types)
            code += f'declare {llvm_ret_type} @{fun_name}({args})\n'
        code += '\n'
        for name, val in self.str_consts.items():
            str_len = len(val) + 1
            code += \
                f'{name} = internal constant [{str_len} x i8] c"{val}\\00"\n'
        if self.str_consts:
            code += '\n\n'
        for name, fun in self.functions.items():
            if name in self.builtin_functions:
                continue
            code += fun.code + '\n\n'
        return code.strip()


    ### Function definition visitor

    def visit_topdef_fun(self, ctx: LatteParser.TopDefFunContext) -> None:
        llvm_ret_type = type_as_llvm(ctx.lattype())
        fun_name = ctx.IDENT().getText()
        llvm_args = []
        self.var_envs.append(dict())
        self.next_reg_index = 0
        self.next_label_index = 0
        self.current_function_code = []
        self.expected_ret_type = type_as_str(ctx.lattype())
        for arg in ctx.arg():
            arg_name = arg.IDENT().getText()
            arg_type = type_as_str(arg.lattype())
            arg_llvm_type = type_as_llvm(arg.lattype())
            llvm_args.append(f'{arg_llvm_type} %{arg_name}')
            var = LatSignature(arg_type, name=arg_name)
            self.declare_variable(ctx, var)
            self.current_function_code.append(
                f'store {arg_llvm_type} %{arg_name}, '
                f'{arg_llvm_type}* {var.ret_val}')
        llvm_args_str = ', '.join(llvm_args)
        fun_def = f'define {llvm_ret_type} @{fun_name}({llvm_args_str})'
        returned = self.visit_block(ctx.block(), make_env=False)
        if not returned:
            if self.expected_ret_type == 'void':
                self.current_function_code.append('ret void')
            else:
                compilation_error(
                    ctx, 'Function can finish before returning a value')
        self.var_envs.pop()
        code = self.current_function_code
        fun_block_code = 'entry:\n'
        for line in code:
            if not line.endswith(':'):
                fun_block_code += ' ' * 4
            fun_block_code += line + '\n'
        code_str = f'{fun_def} {{\n{fun_block_code}}}'
        self.functions[fun_name].code = code_str
        self.current_function_code = []


    ### Block/statements visitors

    # Visiting blocks and statements returns the type returned in a return
    # statement inside it or None if nothing is returned.
    def visit_block(
            self, ctx: LatteParser.BlockContext,
            make_env: bool = True) -> Union[str, None]:
        if make_env:
            self.var_envs.append(dict())
        returned_type = None
        for stmt in ctx.stmt():
            returned_type = self.visit_stmt(stmt)
            if returned_type:
                break
        if make_env:
            self.var_envs.pop()
        return returned_type


    def visit_stmt(self, ctx: LatteParser.StmtContext) -> Union[str, None]:
        if isinstance(ctx, LatteParser.StmtEmptyContext):
            return None
        elif isinstance(ctx, LatteParser.StmtBlockContext):
            return self.visit_block(ctx.block())
        elif isinstance(ctx, LatteParser.StmtDeclContext):
            self.visit_stmt_decl(ctx)
        elif isinstance(ctx, LatteParser.StmtAssContext):
            var = self.get_variable(ctx, ctx.IDENT().getText())
            val = self.visit_exp(ctx.exp())
            if var.ret_type != val.ret_type:
                compilation_error(
                    ctx, f'Variable {var.name} has type {var.ret_type}, '
                    f'but the value has type {val.ret_type}')
            llvm_type = type_str_as_llvm(var.ret_type)
            self.current_function_code.append(
                f'store {llvm_type} {val.ret_val}, {llvm_type}* {var.ret_val}')
        elif isinstance(ctx, (
                LatteParser.StmtIncrContext, LatteParser.StmtDecrContext)):
            if isinstance(ctx, LatteParser.StmtIncrContext):
                op, llvm_op = '++', 'add'
            else:
                op, llvm_op = '--', 'sub'
            var, var_reg = self.load_variable(ctx, ctx.IDENT().getText())
            if var.ret_type != 'int':
                compilation_error(
                    ctx, f'Argument to `{op}` has to be int, '
                    f'but {var.name} is {var.ret_type}')
            reg = self.get_new_register()
            self.current_function_code += [
                f'{reg} = {llvm_op} i32 {var_reg}, 1',
                f'store i32 {reg}, i32* {var.ret_val}'
            ]
        elif isinstance(ctx, LatteParser.StmtRetValContext):
            val = self.visit_exp(ctx.exp())
            if val.ret_type != self.expected_ret_type:
                compilation_error(
                    ctx, f'This function returns {self.expected_ret_type}, '
                    f'but value is {val.ret_type}')
            llvm_type = type_str_as_llvm(val.ret_type)
            self.current_function_code.append(
                f'ret {llvm_type} {val.ret_val}')
            return val.ret_type
        elif isinstance(ctx, LatteParser.StmtRetVoidContext):
            if self.expected_ret_type != 'void':
                compilation_error(
                    ctx, 'This function returns non-void type '
                    f'{self.expected_ret_type}')
            self.current_function_code.append('ret void')
            return 'void'
        elif isinstance(ctx, (
                LatteParser.StmtIfNoElseContext,
                LatteParser.StmtIfElseContext)):
            return self.visit_stmt_if(ctx)
        elif isinstance(ctx, LatteParser.StmtWhileContext):
            return self.visit_stmt_while(ctx)
        elif isinstance(ctx, LatteParser.StmtForContext):
            compilation_error(ctx, EXT_NOT_IMPLEMENTED)
        elif isinstance(ctx, LatteParser.StmtExpContext):
            self.visit_exp(ctx.exp())


    def visit_stmt_decl(self, ctx: LatteParser.StmtDeclContext) \
            -> Union[str, None]:
        str_type = type_as_str(ctx.lattype())
        if str_type == 'void':
            compilation_error(ctx, 'Cannot declare void variables')
        llvm_type = type_as_llvm(ctx.lattype())
        for item in ctx.item():
            if isinstance(item, LatteParser.ItemInitContext):
                val = self.visit_exp(item.exp())
            elif str_type in ('int', 'boolean'):
                val = LatSignature(str_type, ret_val='0')
            elif str_type == 'string':
                val = self.get_str_const('')

            var = LatSignature(str_type, name=item.IDENT().getText())
            self.declare_variable(ctx, var)

            if val.ret_type != var.ret_type:
                compilation_error(
                    ctx, f'Variable {var.name} has type {var.ret_type}, '
                    f'but the value has type {val.ret_type}')
            self.current_function_code.append(
                f'store {llvm_type} {val.ret_val}, {llvm_type}* {var.ret_val}')


    def visit_stmt_if(self, ctx: LatteParser.StmtContext) -> Union[str, None]:
        has_else = isinstance(ctx, LatteParser.StmtIfElseContext)
        cond = self.visit_exp(ctx.exp())
        true_stmt_ctx = ctx.stmt(0) if has_else else ctx.stmt()
        if cond.ret_type != 'boolean':
            compilation_error(ctx, 'Condition of if has to be boolean')

        if cond.ret_val == '1':
            return self.visit_stmt(true_stmt_ctx)
        elif cond.ret_val == '0' and has_else:
            return self.visit_stmt(ctx.stmt(1))

        label_true = self.get_new_label()
        label_false = self.get_new_label()
        label_after = self.get_new_label() if has_else else label_false
        self.current_function_code += [
            f'br i1 {cond.ret_val}, label %{label_true}, label %{label_false}',
            f'{label_true}:'
        ]
        returned_block_true = self.visit_stmt(true_stmt_ctx)
        if not returned_block_true:
            self.current_function_code.append(f'br label %{label_after}')

        returned_block_false = None
        if has_else:
            self.current_function_code.append(f'{label_false}:')
            returned_block_false = self.visit_stmt(ctx.stmt(1))
            if not returned_block_false:
                self.current_function_code.append(f'br label %{label_after}')
        if (returned_block_true is not None
                and returned_block_true == returned_block_false):
            return returned_block_true
        self.current_function_code.append(f'{label_after}:')
        return None


    def visit_stmt_while(self, ctx: LatteParser.StmtWhileContext) -> None:
        cond_label = self.get_new_label()
        label_true = self.get_new_label()
        label_false = self.get_new_label()
        self.current_function_code += [
            f'br label %{cond_label}',
            f'{cond_label}:'
        ]
        cond = self.visit_exp(ctx.exp())
        self.current_function_code += [
            f'br i1 {cond.ret_val}, label %{label_true}, label %{label_false}',
            f'{label_true}:'
        ]
        self.visit_stmt(ctx.stmt())
        self.current_function_code += [
            f'br label %{cond_label}',
            f'{label_false}:'
        ]


    ### Expression visitors

    def visit_exp(self, ctx: LatteParser.ExpContext) -> LatSignature:
        if isinstance(ctx, (
                LatteParser.ExpOrContext, LatteParser.ExpAndContext)):
            return self.visit_bool_op_exp(ctx)
        if isinstance(ctx, (
                LatteParser.ExpRelContext, LatteParser.ExpAddContext,
                LatteParser.ExpMulContext)):
            return self.visit_binary_op_exp(ctx)
        elif isinstance(ctx, LatteParser.ExpNegContext):
            return self.visit_exp_neg(ctx)
        elif isinstance(ctx, LatteParser.ExpStrContext):
            return self.get_str_const(ctx.STR().getText()[1:-1])
        elif isinstance(ctx, LatteParser.ExpAppContext):
            return self.visit_exp_app(ctx)
        elif isinstance(ctx, LatteParser.ExpFalseContext):
            return LatSignature('boolean', ret_val='0')
        elif isinstance(ctx, LatteParser.ExpTrueContext):
            return LatSignature('boolean', ret_val='1')
        elif isinstance(ctx, LatteParser.ExpNewArrContext):
            compilation_error(ctx, EXT_NOT_IMPLEMENTED)
        elif isinstance(ctx, LatteParser.ExpArrElemContext):
            compilation_error(ctx, EXT_NOT_IMPLEMENTED)
        elif isinstance(ctx, LatteParser.ExpNewClassContext):
            compilation_error(ctx, EXT_NOT_IMPLEMENTED)
        elif isinstance(ctx, LatteParser.ExpClassMemberContext):
            compilation_error(ctx, EXT_NOT_IMPLEMENTED)
        elif isinstance(ctx, LatteParser.ExpNullContext):
            compilation_error(ctx, EXT_NOT_IMPLEMENTED)
        elif isinstance(ctx, LatteParser.ExpIntContext):
            return LatSignature('int', ret_val=ctx.INTEGER().getText())
        elif isinstance(ctx, LatteParser.ExpVarContext):
            var, var_reg = self.load_variable(ctx, ctx.IDENT().getText())
            return LatSignature(var.ret_type, ret_val=var_reg)
        elif isinstance(ctx, LatteParser.ExpParenContext):
            return self.visit_exp(ctx.exp())


    def visit_exp_neg(self, ctx: LatteParser.ExpNegContext) -> LatSignature:
        op = ctx.negop().getText()
        arg = self.visit_exp(ctx.exp())
        reg = self.get_new_register()
        expected_type = 'boolean' if op == '!' else 'int'
        if arg.ret_type != expected_type:
            compilation_error(
                ctx, f'Argument to `{op}` has to be {expected_type}, '
                f'but is {arg.ret_type}'
            )
        if op == '!':
            self.current_function_code.append(
                f'{reg} = xor i1 {arg.ret_val}, 1')
            return LatSignature('boolean', ret_val=reg)
        else:
            self.current_function_code.append(
                f'{reg} = sub i32 0, {arg.ret_val}')
            return LatSignature('int', ret_val=reg)


    def visit_exp_app(self, ctx: LatteParser.ExpAppContext) -> LatSignature:
        fun_name = ctx.IDENT().getText()
        fun_decl = self.functions.get(fun_name)
        if not fun_decl:
            compilation_error(ctx, f'Undeclared function: {fun_name}')
        args = [self.visit_exp(arg) for arg in ctx.exp()]
        if len(args) != len(fun_decl.arg_types):
            compilation_error(
                ctx, f'Invalid number of arguments to `{fun_decl}`')
        for i, (arg, arg_decl) in enumerate(zip(args, fun_decl.arg_types)):
            if arg.ret_type != arg_decl:
                compilation_error(
                    ctx, f'Argument {i+1} to function `{fun_decl}` has to '
                    f'have type {arg_decl}, but value has type {arg.ret_type}')
        self.used_functions.add(fun_name)
        llvm_ret_type = type_str_as_llvm(fun_decl.ret_type)
        str_args = ', '.join((
            '{arg_type} {arg_val}'.format(
                arg_type=type_str_as_llvm(arg.ret_type), arg_val=arg.ret_val)
            for arg in args))
        call_str = f'call {llvm_ret_type} @{fun_decl.name}({str_args})'
        if fun_decl.ret_type != 'void':
            reg = self.get_new_register()
            call_str = f'{reg} = {call_str}'
        else:
            reg = None
        self.current_function_code.append(call_str)
        return LatSignature(fun_decl.ret_type, ret_val=reg)


    def visit_bool_op_exp(self, ctx: LatteParser.ExpContext) -> LatSignature:
        if isinstance(ctx, LatteParser.ExpAndContext):
            op, instr = '&&', 'and'
        else:
            op, instr = '||', 'or'
        label_entry = self.get_new_label()
        label_check = self.get_new_label()
        label_skip = self.get_new_label()
        if instr == 'and':
            label_true, label_false = label_check, label_skip
        else:
            label_true, label_false = label_skip, label_check
        self.current_function_code += [
            f'br label %{label_entry}',
            f'{label_entry}:'
        ]

        left = self.visit_exp(ctx.exp(0))
        if left.ret_type != 'boolean':
            compilation_error(
                ctx, f'Arguments to operator `{op}` have to be boolean,'
                f'but the left value is {left.ret_type}')
        left_finish_label = left.finish_label or label_entry
        self.current_function_code += [
            f'br i1 {left.ret_val}, label %{label_true}, label %{label_false}',
            f'{label_check}:'
        ]

        right = self.visit_exp(ctx.exp(1))
        if right.ret_type != 'boolean':
            compilation_error(
                ctx, f'Arguments to operator `{op}` have to be boolean,'
                f'but the right value is {right.ret_type}')
        right_finish_label = right.finish_label or label_check

        reg = self.get_new_register()
        self.current_function_code += [
            f'br label %{label_skip}',

            f'{label_skip}:',

            f'{reg} = phi i1 [ {left.ret_val}, %{left_finish_label} ], '
            f'[ {right.ret_val}, %{right_finish_label} ]'
        ]
        return LatSignature('boolean', ret_val=reg, finish_label=label_skip)


    def visit_binary_op_exp(self, ctx: LatteParser.ExpContext) -> LatSignature:
        if isinstance(ctx, LatteParser.ExpRelContext):
            op = ctx.relop().getText()
            op_ret_type = 'boolean'
            valid_types = ('int', 'boolean', 'string')
            instr = 'icmp ' + {
                '<': 'slt',
                '<=': 'sle',
                '>': 'sgt',
                '>=': 'sge',
                '==': 'eq',
                '!=': 'ne',
            }[op]
        elif isinstance(ctx, LatteParser.ExpAddContext):
            op = ctx.addop().getText()
            op_ret_type = 'int'  # not used for strings
            valid_types = {'+': ('int', 'string'), '-': ('int',)}[op]
            instr = {'+': 'add', '-': 'sub'}[op]  # not used for strings
        elif isinstance(ctx, LatteParser.ExpMulContext):
            op = ctx.mulop().getText()
            op_ret_type = 'int'
            valid_types = ('int',)
            instr = {'*': 'mul', '/': 'sdiv', '%': 'srem'}[op]

        left = self.visit_exp(ctx.exp(0))
        right = self.visit_exp(ctx.exp(1))
        if left.ret_type != right.ret_type:
            return compilation_error(
                ctx, f'Types to operator `{op}` do not match: '
                f'{left.ret_type} and {right.ret_type}')
        # true: left.ret_type == right.ret_type
        if left.ret_type not in valid_types:
            return compilation_error(
                ctx, f'Operator `{op}` does not accept type {left.ret_type}')

        reg = self.get_new_register()
        if left.ret_type != 'string':
            llvm_arg_type = type_str_as_llvm(left.ret_type)
            self.current_function_code.append(
                f'{reg} = {instr} {llvm_arg_type} '
                f'{left.ret_val}, {right.ret_val}')
            return LatSignature(op_ret_type, ret_val=reg)
        elif isinstance(ctx, LatteParser.ExpRelContext):  # string comparison
            reg2 = self.get_new_register()
            self.used_functions.add('strcmp')
            self.current_function_code += [
                f'{reg} = call i32 @strcmp('
                f'i8* {left.ret_val}, i8* {right.ret_val})',

                f'{reg2} = {instr} i32 {reg}, 0'
            ]
            return LatSignature('boolean', ret_val=reg2)
        else:  # string concatenation
            self.used_functions.add('strconcat')
            self.current_function_code.append(
                f'{reg} = call i8* @strconcat('
                f'i8* {left.ret_val}, i8* {right.ret_val})')
            return LatSignature('string', ret_val=reg)
