grammar Instant;


prog
    : stmt (STMTSEP+ stmt)* STMTSEP*;

stmt
    : IDENT '=' exp  # SAss
    | exp            # SExp
    ;

exp 
    : exp mulOp exp                # ExpMulOp
    | <assoc=right> exp addOp exp  # ExpAddOp
    | INTEGER                      # ExpLit
    | IDENT                        # ExpVar
    ;

addOp
    : '+'
    | '-'
    ;

mulOp
    : '*'
    | '/'
    ;


IDENT:   [a-zA-Z][a-zA-Z0-9_']*;
INTEGER: [0-9]+;

STMTSEP: [;\r\n]+;
WS:      [ \t]+ -> skip;