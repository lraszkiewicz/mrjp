grammar Latte;


program
    : topdef+ EOF;

topdef
    : type IDENT '(' arg? (',' arg)* ')' block  # TopDefFun
    ;

arg
    : type IDENT;

block
    : '{' stmt* '}';

stmt
    : ';'                                   # StmtEmpty
    | block                                 # StmtBlock
    | type item (',' item)* ';'             # StmtDecl
    | IDENT '=' exp ';'                     # StmtAss
    | IDENT '++' ';'                        # StmtIncr
    | IDENT '--' ';'                        # StmtDecr
    | 'return' exp ';'                      # StmtRetVal
    | 'return' ';'                          # StmtRetVoid
    | 'if' '(' exp ')' stmt                 # StmtIfNoElse
    | 'if' '(' exp ')' stmt 'else' stmt     # StmtIfElse
    | 'while' '(' exp ')' stmt              # StmtWhile
    | exp ';'                               # Stmtexp
    ;

item
    : IDENT             # ItemNoInit
    | IDENT '=' exp     # ItemInit
    ;

type
    : 'int'                             # TypeInt
    | 'string'                          # TypeStr
    | 'boolean'                         # TypeBool
    | 'void'                            # TypeVoid
    // | type '(' type? (',' type)* ')'    # TypeFun
    ;

exp
    : <assoc=right> exp '||' exp        # ExpOr
    | <assoc=right> exp '&&' exp        # ExpAnd
    | exp relop exp                     # ExpRel
    | exp addop exp                     # ExpAdd
    | exp mulop exp                     # ExpMul
    | '!' exp                           # ExpNot
    | '-' exp                           # ExpNeg
    | STR                               # ExpStr
    | IDENT '(' exp? (',' exp)* ')'     # ExpApp
    | 'false'                           # ExpFalse
    | 'true'                            # ExpTrue
    | INTEGER                           # ExpInt
    | IDENT                             # ExpVar
    ;

relop
    : '<'   # OpLT
    | '<='  # OpLE
    | '>'   # OpGT
    | '>='  # OpGE
    | '=='  # OpEQ
    | '!='  # OpNE
    ;

addop
    : '+'   # OpAdd
    | '-'   # OpSub
    ;

mulop
    : '*'   # OpMul
    | '/'   # OpDiv
    | '%'   # OpMod
    ;

// TODO: string, Latte comments, extensions

IDENT:      [a-zA-Z][a-zA-Z0-9_']*;
INTEGER:    [0-9]+;
STR:        '"' (~[\r\n"] | '\\"')* '"';

LINE_COMMENT_SLASH: '#'  .*? '\r'? '\n' -> skip;
LINE_COMMENT_HASH:  '//' .*? '\r'? '\n' -> skip;
BLOCK_COMMENT:      '/*' .*? '*/' -> skip;

WS: [ \t\r\n]+ -> skip;