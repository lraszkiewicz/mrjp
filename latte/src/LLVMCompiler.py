# pylint: disable=C0103, C0111, R1705

import sys
from typing import Dict, List, Set, Tuple, Union

import antlr4
from antlr_generated.LatteParser import LatteParser


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


# Used for variables or values returned from expressions.
class LatValue:

    def __init__(
            self, str_type: str, value: str = '',
            name: str = '', finish_label: str = ''):
        self.str_type = str_type  # 'int', 'boolean', etc.; not 'i32'
        self.value = value  # might be a constant or a register
        self.name = name  # variable name if it's a variable
        # some expressions produce labels when evaluating, this is the label
        # of the block in which the final result is assigned to a register
        self.finish_label = finish_label

    def llvm_type(self):
        return type_str_as_llvm(self.str_type)  # 'i32', 'i1', etc.


class LatFunSignature:

    def __init__(
            self, ret_type: str, arg_types: List[str],
            name: str = '', code: str = ''):
        self.ret_type = ret_type
        self.arg_types = arg_types
        self.name = name
        self.code = code

    def __str__(self):
        args = ', '.join(self.arg_types)
        return f'{self.ret_type} {self.name}({args})'

    def llvm_ret_type(self):
        return type_str_as_llvm(self.ret_type)


class LLVMCompiler:

    ### Constructor

    def __init__(self):
        self.used_functions: Set[str] = set()
        self.current_function_code: List[str] = []
        self.next_reg_index = 0
        self.next_label_index = 0
        self.tree_depth = -1
        self.str_consts: Dict[str, str] = {}
        self.builtin_functions: Set[str] = set()
        self.expected_ret_type: Union[str, None] = None
        self.var_envs: List[Dict[str, LatValue]] = []
        self.functions = {
            'printInt': LatFunSignature('void', ['int']),
            'printString': LatFunSignature('void', ['string']),
            'error': LatFunSignature('void', []),
            'readInt': LatFunSignature('int', []),
            'readString': LatFunSignature('string', []),
            'strcmp': LatFunSignature('int', ['string', 'string']),
            'strconcat': LatFunSignature('string', ['string', 'string']),
        }
        for fun in self.functions:
            self.functions[fun].name = fun
            self.builtin_functions.add(fun)


    ### Utils

    def get_new_register(self) -> str:
        reg = self.next_reg_index
        self.next_reg_index += 1
        return f'%.t{reg}'


    def get_str_const(self, str_val: str) -> LatValue:
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
        return LatValue('string', reg)


    def declare_variable(
            self, ctx: antlr4.ParserRuleContext, var: LatValue) -> None:
        if var.name in self.var_envs[-1]:
            compilation_error(ctx, f'Variable {var.name} already declared')
        var.value = self.get_new_register()
        llvm_type = var.llvm_type()
        self.current_function_code.append(f'{var.value} = alloca {llvm_type}')
        self.var_envs[-1][var.name] = var


    def get_variable(self, ctx: antlr4.ParserRuleContext, var_name: str) \
            -> LatValue:
        for var_env in reversed(self.var_envs):
            if var_name in var_env:
                return var_env[var_name]
        compilation_error(ctx, f'Variable {var_name} was not declared')


    # Returns (variable, loaded value of variable)
    def load_variable(
            self, ctx: antlr4.ParserRuleContext, var_name: str) \
            -> Tuple[LatValue, LatValue]:
        var = self.get_variable(ctx, var_name)
        reg = self.get_new_register()
        llvm_type = var.llvm_type()
        self.current_function_code.append(
            f'{reg} = load {llvm_type}, {llvm_type}* {var.value}')
        return (var, LatValue(var.str_type, reg))


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
        self.functions[fun_name] = LatFunSignature(
            ret_type, arg_types, name=fun_name)


    ### Program visitor

    def visit_prog(self, ctx: LatteParser.ProgramContext) -> str:
        for child in ctx.children:
            if isinstance(child, LatteParser.TopDefFunContext):
                self.declare_function(child)

        for child in ctx.children:
            if isinstance(child, LatteParser.TopDefFunContext):
                self.visit_topdef_fun(child)

        if 'main' not in self.functions:
            compilation_error(ctx, 'Function `int main()` was not declared')

        code = ''
        for fun_name in self.builtin_functions:
            if fun_name not in self.used_functions:
                continue
            fun = self.functions[fun_name]
            llvm_ret_type = fun.llvm_ret_type()
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
        return code.strip() + '\n'


    ### Function definition visitor

    def visit_topdef_fun(self, ctx: LatteParser.TopDefFunContext) -> None:
        llvm_ret_type = type_as_llvm(ctx.lattype())
        fun_name = ctx.IDENT().getText()
        llvm_args = []
        self.var_envs.append({})
        self.next_reg_index = 0
        self.next_label_index = 0
        self.current_function_code = []
        self.expected_ret_type = type_as_str(ctx.lattype())

        for arg in ctx.arg():
            arg_name = arg.IDENT().getText()
            arg_type = type_as_str(arg.lattype())
            arg_llvm_type = type_as_llvm(arg.lattype())
            llvm_args.append(f'{arg_llvm_type} %{arg_name}')
            var = LatValue(arg_type, name=arg_name)
            self.declare_variable(ctx, var)
            self.current_function_code.append(
                f'store {arg_llvm_type} %{arg_name}, '
                f'{arg_llvm_type}* {var.value}')
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
    # statement inside it or None if nothing is guaranteed to be returned.
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
            return None

        elif isinstance(ctx, LatteParser.StmtAssContext):
            var = self.get_variable(ctx, ctx.IDENT().getText())
            val = self.visit_exp(ctx.exp())
            if var.str_type != val.str_type:
                compilation_error(
                    ctx, f'Variable {var.name} has type {var.str_type}, '
                    f'but the value has type {val.str_type}')
            llvm_type = var.llvm_type()
            self.current_function_code.append(
                f'store {llvm_type} {val.value}, {llvm_type}* {var.value}')
            return None

        elif isinstance(ctx, (
                LatteParser.StmtIncrContext, LatteParser.StmtDecrContext)):
            if isinstance(ctx, LatteParser.StmtIncrContext):
                op, llvm_op = '++', 'add'
            else:
                op, llvm_op = '--', 'sub'
            var, var_val = self.load_variable(ctx, ctx.IDENT().getText())
            if var_val.str_type != 'int':
                compilation_error(
                    ctx, f'Argument to `{op}` has to be int, '
                    f'but {var.name} is {var_val.str_type}')
            reg = self.get_new_register()
            self.current_function_code += [
                f'{reg} = {llvm_op} i32 {var_val.value}, 1',
                f'store i32 {reg}, i32* {var.value}'
            ]
            return None

        elif isinstance(ctx, LatteParser.StmtRetValContext):
            val = self.visit_exp(ctx.exp())
            if val.str_type != self.expected_ret_type:
                compilation_error(
                    ctx, f'This function returns {self.expected_ret_type}, '
                    f'but value is {val.str_type}')
            llvm_type = val.llvm_type()
            self.current_function_code.append(
                f'ret {llvm_type} {val.value}')
            return val.str_type

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

        elif isinstance(ctx, LatteParser.StmtExpContext):
            self.visit_exp(ctx.exp())
            return None


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
                val = LatValue(str_type, '0')
            elif str_type == 'string':
                val = self.get_str_const('')

            var = LatValue(str_type, name=item.IDENT().getText())
            self.declare_variable(ctx, var)

            if val.str_type != var.str_type:
                compilation_error(
                    ctx, f'Variable {var.name} has type {var.str_type}, '
                    f'but the value has type {val.str_type}')
            self.current_function_code.append(
                f'store {llvm_type} {val.value}, {llvm_type}* {var.value}')


    def visit_stmt_if(self, ctx: LatteParser.StmtContext) -> Union[str, None]:
        has_else = isinstance(ctx, LatteParser.StmtIfElseContext)
        cond = self.visit_exp(ctx.exp())
        true_stmt_ctx = ctx.stmt(0) if has_else else ctx.stmt()
        if cond.str_type != 'boolean':
            compilation_error(
                ctx, f'Condition of if has to be boolean, is {cond.str_type}')

        if cond.value == '1':
            return self.visit_stmt(true_stmt_ctx)
        elif cond.value == '0' and has_else:
            return self.visit_stmt(ctx.stmt(1))

        label_true = self.get_new_label()
        label_false = self.get_new_label()
        label_after = self.get_new_label() if has_else else label_false
        self.current_function_code += [
            f'br i1 {cond.value}, label %{label_true}, label %{label_false}',
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
        if cond.str_type != 'boolean':
            compilation_error(
                ctx,
                f'Condition of while has to be boolean, is {cond.str_type}')

        self.current_function_code += [
            f'br i1 {cond.value}, label %{label_true}, label %{label_false}',
            f'{label_true}:'
        ]
        self.visit_stmt(ctx.stmt())
        self.current_function_code += [
            f'br label %{cond_label}',
            f'{label_false}:'
        ]


    ### Expression visitors

    def visit_exp(self, ctx: LatteParser.ExpContext) -> LatValue:
        if isinstance(ctx, (
                LatteParser.ExpOrContext, LatteParser.ExpAndContext)):
            return self.visit_bool_op_exp(ctx)

        elif isinstance(ctx, (
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
            return LatValue('boolean', '0')

        elif isinstance(ctx, LatteParser.ExpTrueContext):
            return LatValue('boolean', '1')

        elif isinstance(ctx, LatteParser.ExpIntContext):
            return LatValue('int', ctx.INTEGER().getText())

        elif isinstance(ctx, LatteParser.ExpVarContext):
            _, var_val = self.load_variable(ctx, ctx.IDENT().getText())
            return var_val

        elif isinstance(ctx, LatteParser.ExpParenContext):
            return self.visit_exp(ctx.exp())


    def visit_exp_neg(self, ctx: LatteParser.ExpNegContext) -> LatValue:
        op = ctx.negop().getText()
        arg = self.visit_exp(ctx.exp())
        reg = self.get_new_register()
        expected_type = 'boolean' if op == '!' else 'int'
        if arg.str_type != expected_type:
            compilation_error(
                ctx, f'Argument to `{op}` has to be {expected_type}, '
                f'but is {arg.str_type}'
            )
        if op == '!':
            self.current_function_code.append(
                f'{reg} = xor i1 {arg.value}, 1')
            return LatValue('boolean', reg)
        else:
            self.current_function_code.append(
                f'{reg} = sub i32 0, {arg.value}')
            return LatValue('int', reg)


    def visit_exp_app(self, ctx: LatteParser.ExpAppContext) -> LatValue:
        fun_name = ctx.IDENT().getText()
        fun_decl = self.functions.get(fun_name)
        if not fun_decl:
            compilation_error(ctx, f'Undeclared function: {fun_name}')
        args = [self.visit_exp(arg) for arg in ctx.exp()]
        if len(args) != len(fun_decl.arg_types):
            compilation_error(
                ctx, f'Invalid number of arguments to `{fun_decl}`')
        for i, (arg, arg_decl) in enumerate(zip(args, fun_decl.arg_types)):
            if arg.str_type != arg_decl:
                compilation_error(
                    ctx, f'Argument {i+1} to function `{fun_decl}` has to '
                    f'have type {arg_decl}, but value has type {arg.str_type}')
        self.used_functions.add(fun_name)
        llvm_ret_type = type_str_as_llvm(fun_decl.ret_type)
        str_args = ', '.join((
            '{arg_type} {arg_val}'.format(
                arg_type=arg.llvm_type(), arg_val=arg.value)
            for arg in args))
        call_str = f'call {llvm_ret_type} @{fun_decl.name}({str_args})'
        if fun_decl.ret_type != 'void':
            reg = self.get_new_register()
            call_str = f'{reg} = {call_str}'
        else:
            reg = 'void'
        self.current_function_code.append(call_str)
        return LatValue(fun_decl.ret_type, reg)


    def visit_bool_op_exp(self, ctx: LatteParser.ExpContext) -> LatValue:
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
        if left.str_type != 'boolean':
            compilation_error(
                ctx, f'Arguments to operator `{op}` have to be boolean,'
                f'but the left value is {left.str_type}')
        left_finish_label = left.finish_label or label_entry
        self.current_function_code += [
            f'br i1 {left.value}, label %{label_true}, label %{label_false}',
            f'{label_check}:'
        ]

        right = self.visit_exp(ctx.exp(1))
        if right.str_type != 'boolean':
            compilation_error(
                ctx, f'Arguments to operator `{op}` have to be boolean,'
                f'but the right value is {right.str_type}')
        right_finish_label = right.finish_label or label_check

        reg = self.get_new_register()
        self.current_function_code += [
            f'br label %{label_skip}',

            f'{label_skip}:',

            f'{reg} = phi i1 [ {left.value}, %{left_finish_label} ], '
            f'[ {right.value}, %{right_finish_label} ]'
        ]
        return LatValue('boolean', reg, finish_label=label_skip)


    def visit_binary_op_exp(self, ctx: LatteParser.ExpContext) -> LatValue:
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
        if left.str_type != right.str_type:
            compilation_error(
                ctx, f'Types to operator `{op}` do not match: '
                f'{left.str_type} and {right.str_type}')
        # true: left.str_type == right.str_type
        if left.str_type not in valid_types:
            compilation_error(
                ctx, f'Operator `{op}` does not accept type {left.str_type}')

        reg = self.get_new_register()
        if left.str_type != 'string':
            llvm_arg_type = type_str_as_llvm(left.str_type)
            self.current_function_code.append(
                f'{reg} = {instr} {llvm_arg_type} '
                f'{left.value}, {right.value}')
            return LatValue(op_ret_type, reg)

        elif isinstance(ctx, LatteParser.ExpRelContext):  # string comparison
            reg2 = self.get_new_register()
            self.used_functions.add('strcmp')
            self.current_function_code += [
                f'{reg} = call i32 @strcmp('
                f'i8* {left.value}, i8* {right.value})',

                f'{reg2} = {instr} i32 {reg}, 0'
            ]
            return LatValue('boolean', reg2)

        else:  # string concatenation
            self.used_functions.add('strconcat')
            self.current_function_code.append(
                f'{reg} = call i8* @strconcat('
                f'i8* {left.value}, i8* {right.value})')
            return LatValue('string', reg)
