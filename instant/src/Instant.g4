grammar Instant;


prog
    : stmt (STMTSEP+ stmt)* STMTSEP*;

stmt
    : IDENT '=' exp  # StmtAss
    | exp            # StmtExp
    ;

exp
    : exp MULDIVOP exp           # ExpMulDiv
    | exp '-' exp                # ExpSub
    | <assoc=right> exp '+' exp  # ExpAdd
    | INTEGER                    # ExpLit
    | IDENT                      # ExpVar
    | '(' exp ')'                # ExpParen
    ;


IDENT:   [a-zA-Z][a-zA-Z0-9_']*;
INTEGER: [0-9]+;

MULDIVOP: [*/];

STMTSEP: [;\r\n]+;
WS:      [ \t]+ -> skip;
