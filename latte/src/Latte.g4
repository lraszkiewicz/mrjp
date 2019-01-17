grammar Latte;


program
    : topdef+ EOF;

topdef
    : lattype IDENT '(' arg? (',' arg)* ')' block           # TopDefFun
    // | 'class' IDENT '{' classmember* '}'                    # TopDefClassBase
    // | 'class' IDENT 'extends' IDENT '{' classmember* '}'    # TopDefClassDerived
    ;

arg
    : lattype IDENT;

block
    : '{' stmt* '}';

// classmember
//     : lattype IDENT (',' IDENT)* ';'                # ClassMemberField
//     | lattype IDENT '(' arg? (',' arg)* ')' block   # ClassMemberMethod
//     ;

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
    | exp ';'                                   # StmtExp
    // | 'for' '(' lattype IDENT ':' exp ')' stmt  # StmtFor
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
    | lattype '[]'  # TypeArray
    | IDENT         # TypeClass
    ;

exp
    : negop exp                         # ExpNeg
    | exp mulop exp                     # ExpMul
    | exp addop exp                     # ExpAdd
    | exp relop exp                     # ExpRel
    | <assoc=right> exp '&&' exp        # ExpAnd
    | <assoc=right> exp '||' exp        # ExpOr
    | IDENT                             # ExpVar
    | INTEGER                           # ExpInt
    | 'true'                            # ExpTrue
    | 'false'                           # ExpFalse
    | IDENT '(' exp? (',' exp)* ')'     # ExpApp
    | STR                               # ExpStr
    | exp '.' exp                       # ExpClassMember
    | 'new' lattype ('[' exp ']')?      # ExpNew
    | exp '[' exp ']'                   # ExpArrElem
    | '(' lattype ')' nulllit           # ExpNull
    | '(' exp ')'                       # ExpParen
    ;

negop
    : '-'   # OpNeg
    | '!'   # OpNot
    ;

mulop
    : '*'   # OpMul
    | '/'   # OpDiv
    | '%'   # OpMod
    ;

addop
    : '+'   # OpAdd
    | '-'   # OpSub
    ;

relop
    : '<'   # OpLT
    | '<='  # OpLE
    | '>'   # OpGT
    | '>='  # OpGE
    | '=='  # OpEQ
    | '!='  # OpNE
    ;

nulllit
    : 'null'
    | 'NULL'
    | 'nullptr'
    ;

IDENT:      [a-zA-Z][a-zA-Z0-9_']*;
INTEGER:    [0-9]+;
STR:        '"' (~[\r\n"] | '\\"')* '"';
// NULL:       'nullptr|NULL|null';
// NULL:       ('NULL' | 'null' | 'nullptr');

LINE_COMMENT_HASH:      '#'  .*? '\r'? '\n' -> skip;
LINE_COMMENT_SLASH:     '//' .*? '\r'? '\n' -> skip;
BLOCK_COMMENT:          '/*' .*? '*/' -> skip;

WS: [ \t\r\n]+ -> skip;
