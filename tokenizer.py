import ply.lex as lex

# Palabras reservadas
reserved = {
    "print": "KW_PRINT",
    "program": "KW_PROGRAM",
    "main": "KW_MAIN",
    "var": "KW_VAR",
    "end": "KW_END",
    "int": "KW_INT",
    "float": "KW_FLOAT",
    "string": "KW_STRING",
    "void": "KW_VOID",
    "if": "KW_IF",
    "else": "KW_ELSE",
    "do": "KW_DO",
    "while": "KW_WHILE",
}

# Tokens
tokens = [
    "CONS_INT",
    "CONS_FLOAT",
    "ID",
    "OPASIGNA",
    "SEMICOL",
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "COMA",
    "COLON",
    "LPAREN",
    "RPAREN",
    "LBRACE",
    "RBRACE",
    "LBRACKET",
    "RBRACKET",
    "EQEQ",
    "GE",
    "LE",
    "NE",
    "LT",
    "GT",
    "STRING",
] + list(reserved.values())

# Reglas regex
t_OPASIGNA = r"="
t_SEMICOL = r";"
t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_COMA = r","
t_COLON = r":"
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACE = r"\{"
t_RBRACE = r"\}"
t_LBRACKET = r"\["
t_RBRACKET = r"\]"
t_EQEQ = r"=="
t_GE = r">="
t_LE = r"<="
t_NE = r"!="
t_LT = r"<"
t_GT = r">"
t_STRING = r"\".*?\""

# Comentarios: ignorar
def t_COMMENT(t):
    r'\#.*'
    pass

# Numeros
def t_CONS_FLOAT(t):
    r"\d+\.\d+\b"
    t.value = float(t.value)
    return t

def t_CONS_INT(t):
    r"\d+\b"
    t.value = int(t.value)
    return t

# Identificadores / Palabras reservadas
def t_ID(t):
    r"[a-zA-Z]\w*\b"
    if t.value in reserved:
        t.type = reserved[t.value]
    return t

# Espacios / tabs
t_ignore = " \t"

# Contar lineas
def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)

# Errores
def t_error(t):
    line = t.lineno
    pos = t.lexpos
    value = t.value[0]

    error_msg = f"ERROR lexico: caracter no reconocido '{value}' en linea {line}, posicion {pos}"
    print(f"{error_msg}")
    t.lexer.skip(1)

# Construir lexer
lexer = lex.lex()
