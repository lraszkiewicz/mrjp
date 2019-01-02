grammar Latte;


program
    : topdef+ EOF;

topdef
    : lattype IDENT '(' arg? (',' arg)* ')' block           # TopDefFun
    | 'class' IDENT '{' classmember* '}'                    # TopDefClassBase
    | 'class' IDENT 'extends' IDENT '{' classmember* '}'    # TopDefClassDerived
    ;

arg
    : lattype IDENT;

block
    : '{' stmt* '}';

classmember
    : lattype IDENT (',' IDENT)* ';'                # ClassMemberField
    | lattype IDENT '(' arg? (',' arg)* ')' block   # ClassMemberMethod
    ;

stmt
    : ';'                                       # StmtEmpty
    | block                                     # StmtBlock
    | lattype item (',' item)* ';'              # StmtDecl
    | IDENT '=' exp ';'                         # StmtAss
    | IDENT '++' ';'                            # StmtIncr
    | IDENT '--' ';'                            # StmtDecr
    | 'return' exp ';'                          # StmtRetVal
    | 'return' ';'                              # StmtRetVoid
    | 'if' '(' exp ')' stmt                     # StmtIfNoElse
    | 'if' '(' exp ')' stmt 'else' stmt         # StmtIfElse
    | 'while' '(' exp ')' stmt                  # StmtWhile
    | 'for' '(' lattype IDENT ':' exp ')' stmt  # StmtFor
    | exp ';'                                   # StmtExp
    ;

item
    : IDENT             # ItemNoInit
    | IDENT '=' exp     # ItemInit
    ;

lattype
    : 'int'         # TypeInt
    | 'string'      # TypeStr
    | 'boolean'     # TypeBool
    | 'void'        # TypeVoid
    | IDENT         # TypeClass
    | lattype '[]'  # TypeArray
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
    | 'new' lattype '[' exp ']'         # ExpNewArr
    | IDENT '[' exp ']'                 # ExpArrElem
    | 'new' IDENT                       # ExpNewClass
    | exp '.' exp                       # ExpClassMember
    | '(' lattype ')' NULL              # ExpNull
    | INTEGER                           # ExpInt
    | IDENT                             # ExpVar
    | '(' exp ')'                       # ExpParen
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

IDENT:      [a-zA-Z][a-zA-Z0-9_']*;
INTEGER:    [0-9]+;
STR:        '"' (~[\r\n"] | '\\"')* '"';
NULL:       ('NULL' | 'null' | 'nullptr');

LINE_COMMENT_HASH:      '#'  .*? '\r'? '\n' -> skip;
LINE_COMMENT_SLASH:     '//' .*? '\r'? '\n' -> skip;
BLOCK_COMMENT:          '/*' .*? '*/' -> skip;

WS: [ \t\r\n]+ -> skip;
