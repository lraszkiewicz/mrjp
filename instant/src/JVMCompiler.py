from antlr_generated.InstantParser import InstantParser


JVM_TEMPLATE = '''.source {class_name}.j
.class public {class_name}
.super java/lang/Object

.method public <init>()V
    aload_0
    invokespecial java/lang/Object/<init>()V
    return
.end method

.method public static main([Ljava/lang/String;)V
.limit locals {locals_limit}
.limit stack {stack_limit}
{main_code}
    return
.end method
'''

JVM_PRINT_INT = [
    'getstatic java/lang/System/out Ljava/io/PrintStream;',
    'swap',
    'invokevirtual java/io/PrintStream/println(I)V'
]


def get_jvm_instr(instr: str, arg: int) -> str:
    if instr in ['iload', 'istore'] and 0 <= arg <= 3:
        return f'{instr}_{arg}'
    if instr == 'ldc':
        if arg == -1:
            return 'iconst_m1'
        if 0 <= arg <= 5:
            return f'iconst_{arg}'
        if -128 <= arg <= 127:
            return f'bipush {arg}'
        if -32768 <= arg <= 32767:
            return f'sipush {arg}'
    return f'{instr} {arg}'


class JVMCompiler:

    def __init__(self, class_name: str):
        self.var_env = {}
        self.locals = 1
        self.class_name = class_name

    def get_new_local(self) -> int:
        local_index = self.locals
        self.locals += 1
        return local_index

    def visit_prog(self, ctx: InstantParser.ProgContext):
        main_code = []
        stack_limit = 0

        for child in ctx.children:
            if isinstance(child, InstantParser.StmtContext):
                main_code.append(f'; {child.getText()}')

            if isinstance(child, InstantParser.StmtAssContext):
                visit_result = self.visit_stmt_ass(child)
            elif isinstance(child, InstantParser.StmtExpContext):
                visit_result = self.visit_stmt_exp(child)
            else:
                continue

            stack_limit = max(stack_limit, visit_result['stack_limit'])
            main_code += visit_result['code']

        return JVM_TEMPLATE.format(
            class_name=self.class_name,
            locals_limit=self.locals,
            stack_limit=stack_limit,
            main_code='\n'.join(('    ' + line for line in main_code)))

    def visit_stmt_ass(self, ctx: InstantParser.StmtAssContext):
        ident = ctx.IDENT().getText()
        var_local = self.var_env.get(ident)
        if var_local is None:
            var_local = self.get_new_local()
            self.var_env[ident] = var_local
        visit_result = self.visit_exp(ctx.exp())
        return {
            'code': visit_result['code'] + [get_jvm_instr('istore', var_local)],
            'stack_limit': visit_result['stack_limit']
        }

    def visit_stmt_exp(self, ctx: InstantParser.StmtExpContext):
        visit_result = self.visit_exp(ctx.exp())
        return {
            'code': visit_result['code'] + JVM_PRINT_INT,
            'stack_limit': max(2, visit_result['stack_limit'])
        }

    def visit_exp(self, ctx: InstantParser.ExpContext):
        if isinstance(ctx, (InstantParser.ExpMulDivContext,
                            InstantParser.ExpSubContext,
                            InstantParser.ExpAddContext)):
            return self.visit_binary_op_exp(ctx)
        if isinstance(ctx, InstantParser.ExpLitContext):
            return self.visit_exp_lit(ctx)
        if isinstance(ctx, InstantParser.ExpVarContext):
            return self.visit_exp_var(ctx)
        if isinstance(ctx, InstantParser.ExpParenContext):
            return self.visit_exp_paren(ctx)
        raise TypeError(f'unknown expression context type')

    def visit_binary_op_exp(self, ctx: InstantParser.ExpContext):
        if isinstance(ctx, InstantParser.ExpMulDivContext) and ctx.MULDIVOP().getText() == '*':
            instr = 'imul'
            commutative = True
        elif isinstance(ctx, InstantParser.ExpMulDivContext) and ctx.MULDIVOP().getText() == '/':
            instr = 'idiv'
            commutative = False
        elif isinstance(ctx, InstantParser.ExpSubContext):
            instr = 'isub'
            commutative = False
        elif isinstance(ctx, InstantParser.ExpAddContext):
            instr = 'iadd'
            commutative = True
        else:
            raise TypeError('unsupported context type')

        left_visit_res = self.visit_exp(ctx.exp(0))
        right_visit_res = self.visit_exp(ctx.exp(1))
        if left_visit_res['stack_limit'] >= right_visit_res['stack_limit']:
            code = left_visit_res['code'] + right_visit_res['code']
            stack_limit = left_visit_res['stack_limit']
            swapped = False
            if left_visit_res['stack_limit'] == right_visit_res['stack_limit']:
                stack_limit += 1
        else:
            code = right_visit_res['code'] + left_visit_res['code']
            stack_limit = right_visit_res['stack_limit']
            swapped = True

        if swapped and not commutative:
            code.append('swap')
        code.append(instr)

        return {
            'code': code,
            'stack_limit': stack_limit
        }

    def visit_exp_lit(self, ctx: InstantParser.ExpLitContext):
        return {
            'code': [get_jvm_instr('ldc', int(ctx.getText()))],
            'stack_limit': 1
        }

    def visit_exp_var(self, ctx: InstantParser.ExpVarContext):
        ident = ctx.IDENT().getText()
        var_local = self.var_env.get(ident)
        if var_local is None:
            raise RuntimeError(f'undefined variable `{ident}`')
        return {
            'code': [get_jvm_instr('iload', var_local)],
            'stack_limit': 1
        }

    def visit_exp_paren(self, ctx: InstantParser.ExpParenContext):
        return self.visit_exp(ctx.exp())
