from antlr_generated.InstantParser import InstantParser
from antlr_generated.InstantListener import InstantListener


# This class defines a complete listener for a parse tree produced by InstantParser.
class LLVMListener(InstantListener):
    # Enter a parse tree produced by InstantParser#prog.
    def enterProg(self, ctx: InstantParser.ProgContext):
        pass

    # Exit a parse tree produced by InstantParser#prog.
    def exitProg(self, ctx: InstantParser.ProgContext):
        pass

    # Enter a parse tree produced by InstantParser#StmtAss.
    def enterStmtAss(self, ctx: InstantParser.StmtAssContext):
        pass

    # Exit a parse tree produced by InstantParser#StmtAss.
    def exitStmtAss(self, ctx: InstantParser.StmtAssContext):
        pass

    # Enter a parse tree produced by InstantParser#StmtExp.
    def enterStmtExp(self, ctx: InstantParser.StmtExpContext):
        pass

    # Exit a parse tree produced by InstantParser#StmtExp.
    def exitStmtExp(self, ctx: InstantParser.StmtExpContext):
        pass

    # Enter a parse tree produced by InstantParser#ExpLit.
    def enterExpLit(self, ctx: InstantParser.ExpLitContext):
        pass

    # Exit a parse tree produced by InstantParser#ExpLit.
    def exitExpLit(self, ctx: InstantParser.ExpLitContext):
        pass

    # Enter a parse tree produced by InstantParser#ExpVar.
    def enterExpVar(self, ctx: InstantParser.ExpVarContext):
        pass

    # Exit a parse tree produced by InstantParser#ExpVar.
    def exitExpVar(self, ctx: InstantParser.ExpVarContext):
        pass

    # Enter a parse tree produced by InstantParser#ExpMulDiv.
    def enterExpMulDiv(self, ctx: InstantParser.ExpMulDivContext):
        pass

    # Exit a parse tree produced by InstantParser#ExpMulDiv.
    def exitExpMulDiv(self, ctx: InstantParser.ExpMulDivContext):
        pass

    # Enter a parse tree produced by InstantParser#ExpParen.
    def enterExpParen(self, ctx:InstantParser.ExpParenContext):
        pass

    # Exit a parse tree produced by InstantParser#ExpParen.
    def exitExpParen(self, ctx:InstantParser.ExpParenContext):
        pass

    # Enter a parse tree produced by InstantParser#ExpAddSub.
    def enterExpAddSub(self, ctx: InstantParser.ExpAddSubContext):
        pass

    # Exit a parse tree produced by InstantParser#ExpAddSub.
    def exitExpAddSub(self, ctx: InstantParser.ExpAddSubContext):
        pass
