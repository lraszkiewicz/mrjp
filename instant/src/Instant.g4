grammar Instant;


prog
    : stmt (STMTSEP+ stmt)* STMTSEP*;

stmt
    : IDENT '=' exp  # StmtAss
    | exp            # StmtExp
    ;

exp
    : exp MULDIVOP exp                # ExpMulDiv
    | <assoc=right> exp ADDSUBOP exp  # ExpAddSub
    | INTEGER                         # ExpLit
    | IDENT                           # ExpVar
    | '(' exp ')'                     # ExpParen
    ;


IDENT:   [a-zA-Z][a-zA-Z0-9_']*;
INTEGER: [0-9]+;

ADDSUBOP: [+-];
MULDIVOP: [*/];

STMTSEP: [;\r\n]+;
WS:      [ \t]+ -> skip;
