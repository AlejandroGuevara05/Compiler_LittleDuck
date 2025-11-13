import ply.yacc as yacc
import os
import sys
from tokenizer import tokens, lexer

# ==================== CONFIGURACION ====================
start = 'programa'
errores_encontrados = []


# Wrapper para rastrear contexto del ultimo token
class TokenWrapper:

    def __init__(self, lexer):
        self.lexer = lexer
        self.last_token = None

    def token(self):
        tok = self.lexer.token()
        if tok:
            self.last_token = tok
        return tok

    def input(self, data):
        self.lexer.input(data)


wrapped_lexer = TokenWrapper(lexer)

# ==================== REGLAS GRAMATICALES ====================


# PROGRAMA
def p_programa(p):
    'programa : KW_PROGRAM ID SEMICOL vars_opt funcs_list KW_MAIN body KW_END'


def p_programa_error(p):
    'programa : KW_PROGRAM ID error_program_header vars_opt funcs_list KW_MAIN body KW_END'


def p_error_program_header(p):
    'error_program_header : '
    report_error("ERROR: Falta ';' despues del nombre del programa", p)
    parser.errok()


# VARIABLES
def p_vars_opt_vars(p):
    'vars_opt : vars'


def p_vars_opt_empty(p):
    'vars_opt : empty'


def p_vars(p):
    'vars : KW_VAR var_decl_list'


def p_var_decl_list_rec(p):
    'var_decl_list : var_decl var_decl_list'


def p_var_decl_list_single(p):
    'var_decl_list : var_decl'


def p_var_decl(p):
    'var_decl : id_list COLON type SEMICOL'


def p_id_list_multiple(p):
    'id_list : ID COMA id_list'


def p_id_list_single(p):
    'id_list : ID'


def p_type_int(p):
    'type : KW_INT'


def p_type_float(p):
    'type : KW_FLOAT'


def p_type_string(p):
    'type : KW_STRING'


# BODY Y STATEMENTS
def p_body(p):
    'body : LBRACE statement_list RBRACE'


def p_statement_list_rec(p):
    'statement_list : statement statement_list'


def p_statement_list_empty(p):
    'statement_list : empty'


def p_statement_assign(p):
    'statement : assign'


def p_statement_condition(p):
    'statement : condition'


def p_statement_cycle(p):
    'statement : cycle'


def p_statement_f_call(p):
    'statement : f_call'


def p_statement_print(p):
    'statement : print'


# ASSIGN
def p_assign(p):
    'assign : ID OPASIGNA expresion SEMICOL'


def p_assign_missing_semicol(p):
    'assign : ID OPASIGNA expresion'
    report_error(f"ERROR: Falta ';' despues de la asignacion a '{p[1]}'", p)
    parser.errok()


# CONDITION
def p_condition_if_else(p):
    'condition : KW_IF LPAREN expresion RPAREN body KW_ELSE body SEMICOL'


def p_condition_if(p):
    'condition : KW_IF LPAREN expresion RPAREN body SEMICOL'


def p_condition_missing_semicol_if_else(p):
    'condition : KW_IF LPAREN expresion RPAREN body KW_ELSE body'
    report_error("ERROR: Falta ';' despues de la condicion IF-ELSE", p)
    parser.errok()


def p_condition_missing_semicol_if(p):
    'condition : KW_IF LPAREN expresion RPAREN body'
    report_error("ERROR: Falta ';' despues de la condicion IF", p)
    parser.errok()


def p_condition_error_paren(p):
    '''condition : KW_IF LPAREN expresion body KW_ELSE body SEMICOL
                 | KW_IF LPAREN expresion body SEMICOL'''
    report_error(
        "ERROR: Falta ')' de cierre en la condicion del IF. Resincronizando en ';'",
        p)
    parser.errok()


# CYCLE
def p_cycle(p):
    'cycle : KW_DO body KW_WHILE LPAREN expresion RPAREN SEMICOL'


def p_cycle_missing_semicol(p):
    'cycle : KW_DO body KW_WHILE LPAREN expresion RPAREN'
    report_error("ERROR: Falta ';' despues del ciclo DO-WHILE",
                 p,
                 token_index=-1)
    parser.errok()


# FUNCTION CALL
def p_f_call(p):
    'f_call : ID LPAREN expresion_list_opt RPAREN SEMICOL'


def p_f_call_missing_semicol(p):
    'f_call : ID LPAREN expresion_list_opt RPAREN'
    report_error(f"ERROR: Falta ';' despues de la llamada a funcion '{p[1]}'",
                 p)
    parser.errok()


def p_expresion_list_opt_list(p):
    'expresion_list_opt : expresion_list'


def p_expresion_list_opt_empty(p):
    'expresion_list_opt : empty'


def p_expresion_list_rec(p):
    'expresion_list : expresion COMA expresion_list'


def p_expresion_list_single(p):
    'expresion_list : expresion'


# PRINT
def p_print(p):
    'print : KW_PRINT LPAREN print_list RPAREN SEMICOL'


def p_print_missing_semicol(p):
    'print : KW_PRINT LPAREN print_list RPAREN'
    report_error("ERROR: Falta ';' despues del print", p)
    parser.errok()


def p_print_list_rec(p):
    'print_list : print_item COMA print_list'


def p_print_list_single(p):
    'print_list : print_item'


def p_print_item(p):
    'print_item : expresion'


# EXPRESIONES
def p_expresion_gt(p):
    'expresion : exp GT exp'


def p_expresion_lt(p):
    'expresion : exp LT exp'


def p_expresion_ne(p):
    'expresion : exp NE exp'


def p_expresion_ge(p):
    'expresion : exp GE exp'


def p_expresion_le(p):
    'expresion : exp LE exp'


def p_expresion_eqeq(p):
    'expresion : exp EQEQ exp'


def p_expresion_single(p):
    'expresion : exp'


# EXP
def p_exp_plus(p):
    'exp : exp PLUS termino'


def p_exp_minus(p):
    'exp : exp MINUS termino'


def p_exp_termino(p):
    'exp : termino'


# TERMINO
def p_termino_times(p):
    'termino : termino TIMES factor'


def p_termino_divide(p):
    'termino : termino DIVIDE factor'


def p_termino_factor(p):
    'termino : factor'


# FACTOR
def p_factor_group(p):
    'factor : LPAREN expresion RPAREN'


def p_factor_plus(p):
    'factor : PLUS factor'


def p_factor_minus(p):
    'factor : MINUS factor'


def p_factor_id(p):
    'factor : ID'


def p_factor_cte(p):
    'factor : cte'


# CTE
def p_cte_int(p):
    'cte : CONS_INT'


def p_cte_float(p):
    'cte : CONS_FLOAT'


def p_cte_string(p):
    'cte : STRING'


# FUNCIONES
def p_funcs_list_rec(p):
    'funcs_list : funcs funcs_list'


def p_funcs_list_empty(p):
    'funcs_list : empty'


def p_funcs(p):
    'funcs : KW_VOID ID LPAREN params_opt RPAREN LBRACKET vars_opt body RBRACKET SEMICOL'


def p_funcs_missing_semicol(p):
    'funcs : KW_VOID ID LPAREN params_opt RPAREN LBRACKET vars_opt body RBRACKET'
    report_error(
        f"ERROR: Falta ';' despues de la declaracion de funcion '{p[2]}'", p)
    parser.errok()


def p_params_opt_params(p):
    'params_opt : params'


def p_params_opt_empty(p):
    'params_opt : empty'


def p_params_rec(p):
    'params : param COMA params'


def p_params_single(p):
    'params : param'


def p_param(p):
    'param : ID COLON type'


def p_empty(p):
    'empty :'


# ==================== MANEJO DE ERRORES ====================
def report_error(msg, p, token_index=None):
    if token_index is None:
        token_index = 1
    token = p.slice[token_index]
    line = getattr(token, "lineno", "¿?")
    pos = getattr(token, "lexpos", None)

    subcadena = ""
    if pos is not None and isinstance(pos, int):
        start = max(pos - 20, 0)
        end = pos + 20
        subcadena = codigo[start:end].replace("\n", "\\n")
        subcadena = f" → '{subcadena}'"

    full_msg = f"{msg} (linea {line}, pos {pos}){subcadena}"
    print(full_msg)
    errores_encontrados.append(full_msg)


def p_var_decl_error(p):
    'var_decl : error SEMICOL'
    report_error("ERROR: Declaracion de variable incorrecta", p)
    parser.errok()


def p_var_decl_missing_semicol(p):
    'var_decl : id_list COLON type'
    report_error("ERROR: Falta ';' despues de la declaracion de variable", p)
    parser.errok()


def p_assign_error(p):
    'assign : ID OPASIGNA error SEMICOL'
    report_error(f"ERROR: Expresion de asignacion incorrecta para '{p[1]}'", p)
    parser.errok()


def p_condition_error(p):
    '''condition : KW_IF LPAREN error RPAREN body SEMICOL
                 | KW_IF LPAREN error RPAREN body KW_ELSE body SEMICOL
                 | KW_IF error SEMICOL'''
    report_error("ERROR: Condicion IF incorrecta", p)
    parser.errok()


def p_cycle_error(p):
    '''cycle : KW_DO body KW_WHILE LPAREN error RPAREN SEMICOL
             | KW_DO body error SEMICOL'''
    report_error("ERROR: Ciclo DO-WHILE incorrecto", p)
    parser.errok() 


def p_f_call_error(p):
    'f_call : ID LPAREN error RPAREN SEMICOL'
    report_error(
        f"ERROR: Llamada a funcion incorrecta para '{p[1] if len(p) > 1 else '?'}'",
        p)
    parser.errok()  


def p_print_error(p):
    'print : KW_PRINT LPAREN error RPAREN SEMICOL'
    report_error("ERROR: Instruccion PRINT incorrecta", p)
    parser.errok() 


def p_funcs_error(p):
    'funcs : KW_VOID ID LPAREN error RPAREN LBRACKET vars_opt body RBRACKET SEMICOL'
    report_error(f"ERROR: Declaracion de funcion '{p[2]}' incorrecta", p)
    parser.errok() 


def p_statement_error(p):
    'statement : error SEMICOL'
    report_error("ERROR: Declaracion incorrecta", p)
    parser.errok()  


def p_error(t):
    if t:
        error_msg = f"ERROR de sintaxis en '{t.value}' (token {t.type})"

        if t.type == 'KW_END':
            error_msg = "ERROR: Estructura del programa incompleta antes de 'end'"
        elif t.type in ('RPAREN', 'RBRACE', 'RBRACKET'):
            error_msg = f"ERROR: '{t.value}' inesperado - posible error en expresion"

        line = getattr(t, "lineno", "¿?")
        pos = getattr(t, "lexpos", None)

        subcadena = ""
        if pos is not None and isinstance(pos, int):
            start = max(pos - 20, 0)
            end = pos + 20
            subcadena = codigo[start:end].replace("\n", "\\n")
            subcadena = f" → '{subcadena}'"

        full_msg = f"{error_msg} (linea {line}, pos {pos}){subcadena}"
        print(full_msg)
        errores_encontrados.append(full_msg)
    else:
        full_msg = "ERROR: Fin de entrada inesperado"
        print(full_msg)
        errores_encontrados.append(full_msg)


# ==================== EJECUCION ====================

if __name__ == '__main__':
    # Configurar archivo de entrada
    base_dir = os.path.dirname(__file__)
    default_path = os.path.join(base_dir, "error1.txt")
    input_path = sys.argv[1] if len(sys.argv) > 1 else default_path

    # Leer archivo
    with open(input_path, "r", encoding="utf-8") as f:
        codigo = f.read()

    # Resetear errores
    errores_encontrados = []

    # Parsear
    parser = yacc.yacc()
    parser.parse(codigo, lexer=wrapped_lexer)

    # Reporte final
    print("\n" + "=" * 50)
    print("Analisis sintactico completado.")
    print(
        f"Total de errores de sintaxis encontrados: {len(errores_encontrados)}"
    )
    print("=" * 50)
