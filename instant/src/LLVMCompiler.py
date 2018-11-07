import antlr4

from antlr_generated.InstantParser import InstantParser


PRINT_TREE = False

# copied from /home/students/inf/PUBLIC/MRJP/Llvm/runtime.ll
LLVM_PRINT_INT = '''@dnl = internal constant [4 x i8] c"%d\\0A\\00"

declare i32 @printf(i8*, ...)

define void @printInt(i32 %x) {
    %t0 = getelementptr [4 x i8], [4 x i8]* @dnl, i32 0, i32 0
    call i32 (i8*, ...) @printf(i8* %t0, i32 %x)
    ret void
}'''


def tree_printer(fun):
    def fun_wrapper(self, ctx: antlr4.ParserRuleContext) -> str:
        if PRINT_TREE:
            self.tree_depth += 1
            print(' ' * self.tree_depth + ctx.getText().replace('\n', '; '))
            ret_val = fun(self, ctx)
            self.tree_depth -= 1
            return ret_val
        else:
            return fun(self, ctx)

    return fun_wrapper


class LLVMCompiler:

    def __init__(self):
        self.next_reg_index = 1
        self.main_code = []
        self.print_used = False
        self.var_env = {}
        self.tree_depth = -1

    def get_new_register(self) -> int:
        reg = self.next_reg_index
        self.next_reg_index += 1
        return reg

    @tree_printer
    def visit_prog(self, ctx: InstantParser.ProgContext) -> str:
        for child in ctx.children:
            if isinstance(child, InstantParser.StmtContext):
                self.main_code.append(f'; {child.getText()}')

            if isinstance(child, InstantParser.StmtAssContext):
                self.visit_stmt_ass(child)
            elif isinstance(child, InstantParser.StmtExpContext):
                self.visit_stmt_exp(child)

        self.main_code.append('ret i32 0')
        code = '{print_int}define i32 @main() {{\n{main_code}\n}}\n'.format(
            print_int=LLVM_PRINT_INT + '\n\n' if self.print_used else '',
            main_code='\n'.join(('    ' + line for line in self.main_code)))
        return code

    @tree_printer
    def visit_stmt_ass(self, ctx: InstantParser.StmtAssContext) -> None:
        ident = ctx.IDENT().getText()
        if PRINT_TREE:
            print(' ' * (self.tree_depth + 1) + ident)
        reg = self.var_env.get(ident)
        if reg is None:
            reg = self.get_new_register()
            self.main_code.append(f'%{reg} = alloca i32')
            self.var_env[ident] = reg
        value = self.visit_exp(ctx.exp())
        self.main_code.append(f'store i32 {value}, i32* %{reg}')

    @tree_printer
    def visit_stmt_exp(self, ctx: InstantParser.StmtExpContext) -> None:
        value = self.visit_exp(ctx.exp())
        self.main_code.append(f'call void @printInt(i32 {value})')
        self.print_used = True

    # Each function that visits an expression returns
    # either '%reg' when its result is stored in a register,
    # or a number if it's a constant (only for ExpLit).
    @tree_printer
    def visit_exp(self, ctx: InstantParser.ExpContext) -> str:
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
        raise TypeError('unknown expression context type')

    def visit_binary_op_exp(self, ctx: InstantParser.ExpContext) -> str:
        if isinstance(ctx, InstantParser.ExpMulDivContext) and ctx.MULDIVOP().getText() == '*':
            instr = 'mul'
        elif isinstance(ctx, InstantParser.ExpMulDivContext) and ctx.MULDIVOP().getText() == '/':
            instr = 'sdiv'
        elif isinstance(ctx, InstantParser.ExpSubContext):
            instr = 'sub'
        elif isinstance(ctx, InstantParser.ExpAddContext):
            instr = 'add'
        else:
            raise TypeError('unsupported context type')
        left = self.visit_exp(ctx.exp(0))
        right = self.visit_exp(ctx.exp(1))
        reg = self.get_new_register()
        self.main_code.append(f'%{reg} = {instr} i32 {left}, {right}')
        return f'%{reg}'

    def visit_exp_lit(self, ctx: InstantParser.ExpLitContext) -> str:
        return ctx.getText()

    def visit_exp_var(self, ctx: InstantParser.ExpVarContext) -> str:
        ident = ctx.IDENT().getText()
        var_reg = self.var_env.get(ident)
        if var_reg is None:
            raise RuntimeError(f'undefined variable `{ident}`')
        reg = self.get_new_register()
        self.main_code.append(f'%{reg} = load i32, i32* %{var_reg}')
        return f'%{reg}'

    def visit_exp_paren(self, ctx: InstantParser.ExpParenContext) -> str:
        return self.visit_exp(ctx.exp())
