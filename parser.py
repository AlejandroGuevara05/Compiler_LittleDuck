import ply.yacc as yacc
import os
import sys
from tokenizer import tokens, lexer

# ==================== CONTADORES ====================
vars_contador = {
'global_int': 0,
'global_float': 0,
'global_string': 0,
'global_void': 0,
'local_int': 0,
'local_float': 0,
'local_string': 0,
'temp_int': 0,
'temp_float': 0,
'temp_bool': 0,
'cte_int': 0,
'cte_float': 0,
'cte_string': 0,
}

# ==================== DIRECCIONES ====================
direcciones_base = { 
      "global_int": 1000,
      "global_float": 2000,
      "global_string":	3000,
      "global_void": 4000,
      "local_int": 7000,
      "local_float": 8000,
      "local_string": 9000,
      "temp_int": 12000,
      "temp_float": 13000,
      "temp_bool": 14000,
      "cte_int": 17000,
      "cte_float": 18000,
      "cte_string": 19000
}

# ==================== CONFIGURACION ====================
start = 'programa'
errores_encontrados = []
errores_semanticos = []
tabla_constantes = {}


# Wrapper para rastrear contexto del ultimo token
class TokenWrapper:

    def __init__(self, lexer):
        self.lexer = lexer
        self.last_token = None
        self.last_id = None

    def token(self):
        tok = self.lexer.token()
        if tok:
            self.last_token = tok
            if hasattr(tok, 'type') and tok.type == 'ID':
                self.last_id = tok.value
        return tok

    def input(self, data):
        self.lexer.input(data)


wrapped_lexer = TokenWrapper(lexer)

#-------------------------ESTRUCTURAS---------------------------------------

class Persistent:
    stack_args = ['none']  # Pila de operandos
    stack_jumps = []  # Pila de saltos pendientes
    temp_types = {}  # Diccionario de tipos de temporales

    nquads = 0  # contador de quads
    ntemps = 0  # Contador de temporales

    quad_list = []  # una lista de todos los quads

    func_dir = {}  # Directorio de funciones
    current_scope = 'global'  # Scope actual
    current_func = None  # Funcion actual siendo procesada
    param_counter = 0  # Contador de parametros
    local_var_counter = 0  # Contador de variables locales

    main_jump = None  # indice del quad gotomain (para rellenar al iniciar main)
    param_stack = []  # Pila temporal para parametros durante llamadas
    current_func_call = None  # Nombre de la función siendo llamada
    program_name = None  # Nombre del programa

    def __init__(self):
        self.stack_args = [('none', 'none')]
        self.stack_jumps = []
        self.nquads = 0
        self.ntemps = 0
        self.temp_types = {}
        self.func_dir = {}
        self.current_scope = 'global'
        self.current_func = None
        self.param_counter = 0
        self.local_var_counter = 0
        self.main_jump = None
        self.param_stack = []


# Tabla de simbolos:
names = {}
names['global'] = {}

# cubo para validar semantica
cubo = {
    # Suma
    ('int', 'int', '+'): 'int',
    ('float', 'float', '+'): 'float',
    ('int', 'float', '+'): 'float',
    ('float', 'int', '+'): 'float',
    ('string', 'int', '+'): 'err',
    ('string', 'float', '+'): 'err',
    ('int', 'string', '+'): 'err',
    ('float', 'string', '+'): 'err',
    ('string', 'string', '+'): 'err',

    # Resta
    ('int', 'int', '-'): 'int',
    ('float', 'float', '-'): 'float',
    ('int', 'float', '-'): 'float',
    ('float', 'int', '-'): 'float',
    ('string', 'int', '-'): 'err',
    ('string', 'float', '-'): 'err',
    ('int', 'string', '-'): 'err',
    ('float', 'string', '-'): 'err',
    ('string', 'string', '-'): 'err',

    # Multiplicacion
    ('int', 'int', '*'): 'int',
    ('float', 'float', '*'): 'float',
    ('int', 'float', '*'): 'float',
    ('float', 'int', '*'): 'float',
    ('string', 'int', '*'): 'err',
    ('string', 'float', '*'): 'err',
    ('int', 'string', '*'): 'err',
    ('float', 'string', '*'): 'err',
    ('string', 'string', '*'): 'err',

    # Division
    ('int', 'int', '/'): 'float',
    ('float', 'float', '/'): 'float',
    ('int', 'float', '/'): 'float',
    ('float', 'int', '/'): 'float',
    ('string', 'int', '/'): 'err',
    ('string', 'float', '/'): 'err',
    ('int', 'string', '/'): 'err',
    ('float', 'string', '/'): 'err',
    ('string', 'string', '/'): 'err',

    # Asignacion
    ('int', 'int', '='): 'true',
    ('int', 'float', '='): 'true',
    ('float', 'float', '='): 'true',
    ('float', 'int', '='): 'true',
    ('string', 'string', '='): 'true',
    ('int', 'string', '='): 'err',
    ('float', 'string', '='): 'err',
    ('string', 'int', '='): 'err',
    ('string', 'float', '='): 'err',

    # Operadores relacionales
    ('int', 'int', '>'): 'bool',
    ('int', 'int', '<'): 'bool',
    ('int', 'int', '>='): 'bool',
    ('int', 'int', '<='): 'bool',
    ('int', 'int', '=='): 'bool',
    ('int', 'int', '!='): 'bool',
    ('float', 'float', '>'): 'bool',
    ('float', 'float', '<'): 'bool',
    ('float', 'float', '>='): 'bool',
    ('float', 'float', '<='): 'bool',
    ('float', 'float', '=='): 'bool',
    ('float', 'float', '!='): 'bool',
    ('int', 'float', '>'): 'bool',
    ('int', 'float', '<'): 'bool',
    ('int', 'float', '>='): 'bool',
    ('int', 'float', '<='): 'bool',
    ('int', 'float', '=='): 'bool',
    ('int', 'float', '!='): 'bool',
    ('float', 'int', '>'): 'bool',
    ('float', 'int', '<'): 'bool',
    ('float', 'int', '>='): 'bool',
    ('float', 'int', '<='): 'bool',
    ('float', 'int', '=='): 'bool',
    ('float', 'int', '!='): 'bool',
    ('string', 'string', '!='): 'bool',
    ('string', 'string', '=='): 'bool',
}

ds = Persistent()
# data structures


#--------------------------------FUNCIONES AUXILIARES--------------------------------------
# Funcion para reportar errores semanticos
def report_semantic_error(msg):
    full_msg = f"ERROR SEMANTICO: {msg}"
    # print(full_msg)
    errores_semanticos.append(msg)


# Funcion para buscar variables en los scopes
def lookup_var(var_name):
    current = ds.current_scope
    if current in names and var_name in names[current]:
        tipo, direccion = names[current][var_name]
        return tipo
    # Solo permitir acceso a globales si estamos en 'main' o 'global'
    elif (current == 'main' or current == 'global') and var_name in names.get('global', {}):
        tipo, direccion = names['global'][var_name]
        return tipo
    else:
        return None


def get_dir(var_name):
    # Si es un id
    current = ds.current_scope
    if current in names and var_name in names[current]:
        tipo, direccion = names[current][var_name]
        return direccion
    # Solo permitir acceso a globales si estamos en 'main' o 'global'
    elif (current == 'main' or current == 'global') and var_name in names.get('global', {}):
        tipo, direccion = names['global'][var_name]
        return direccion
    # Si es constante
    if isinstance(var_name, (int, float, str)):
        if var_name in tabla_constantes:
            return tabla_constantes[var_name]
        else:
            return None
    return None


def quad_gen_two_arg_ops(operator):
    # Ej. Al multiplicar
    # operador es '*'
    # extrae argumento_L y tipo_L de la stack de operandos
    # extrae argumento_R y tipo_R de la stack de operandos
    # tipo_resultado = consulta el cubo

    # verifica si tipo_resultado no es error
    #	aumenta contadores
    # 	forma el nombre de una variable temporal
    #	la variable temporal y el tipo_resultado pasan a la stack
    # 	imprime
    op = operator
    # Proteger contra stack vacia
    if not ds.stack_args or len(ds.stack_args) < 2:
        report_semantic_error(f"Expresion incompleta para operador '{op}'")
        ds.stack_args.append(('none', 'none'))
        return
    arg_R, tipo_R = ds.stack_args.pop()
    arg_L, tipo_L = ds.stack_args.pop()

    tipo_res = cubo.get((tipo_L, tipo_R, op), 'err')

    if tipo_res != 'err':
        ds.nquads += 1
        ds.ntemps += 1
        temp = "t" + str(ds.ntemps)

        # Guardar el tipo del temporal
        ds.temp_types[temp] = tipo_res

        ds.stack_args.append((temp, tipo_res))

        dir = direcciones_base[f'temp_{tipo_res}'] + vars_contador[f'temp_{tipo_res}']
        vars_contador[f'temp_{tipo_res}'] += 1

        scope = ds.current_scope
        if scope not in names: 
            names[scope] = {}
        names[scope][temp] = (tipo_res, dir)

        new_quad = [ds.nquads, op, get_dir(arg_L), get_dir(arg_R), get_dir(temp)]
        ds.quad_list.append(new_quad)
        # print(ds.nquads, op, arg_L, arg_R, temp)

    else:
        report_semantic_error(
            f"Operacion '{op}' no permitida entre tipos '{tipo_L}' y '{tipo_R}'"
        )
        ds.stack_args.append(('none', 'none'))


def asignar_dir_variable(scope, tipo):
    if scope == "global":
        key = f"global_{tipo}"
    else:
        key = f"local_{tipo}"
    return direcciones_base[key] + vars_contador[key]

# ==================== REGLAS GRAMATICALES ====================

# PROGRAMA
def p_programa(p):
    'programa : KW_PROGRAM ID m_save_program_name SEMICOL vars_opt m_gotomain funcs_list KW_MAIN m_main_start body KW_END'


def p_programa_error(p):
    'programa : KW_PROGRAM ID m_save_program_name error_program_header vars_opt m_gotomain funcs_list KW_MAIN m_main_start body KW_END'


# Guardar el nombre del programa para validaciones
def p_m_save_program_name(p):
    'm_save_program_name : '
    # Capturar el nombre del programa del último ID leído
    ds.program_name = wrapped_lexer.last_id if wrapped_lexer.last_id else None
    # print(f"  >> Nombre del programa: {ds.program_name}")


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
    # Asignar el tipo a todas las variables de la lista
    tipo = p[3]
    scope = ds.current_scope

    # Checar que el scope existe en la tabla de simbolos
    if scope not in names:
        names[scope] = {}

    for var_name in p[1]:
        # Validar que no use el nombre del programa
        if ds.program_name and var_name == ds.program_name:
            report_semantic_error(
                f"Variable '{var_name}' no puede usar el nombre del programa")
        elif var_name in names[scope]:
            report_semantic_error(
                f"Variable '{var_name}' ya fue declarada en scope '{scope}'")
        else:
            dir = asignar_dir_variable(scope, tipo)
            names[scope][var_name] = (tipo, dir)
            if scope == 'global':
                ds.local_var_counter += 1
                vars_contador[f"global_{tipo}"] += 1
            else:
                ds.local_var_counter += 1
                vars_contador[f"local_{tipo}"] += 1


def p_id_list_multiple(p):
    'id_list : ID COMA id_list'
    p[0] = [p[1]] + p[3]


def p_id_list_single(p):
    'id_list : ID'
    p[0] = [p[1]]


def p_type_int(p):
    'type : KW_INT'
    p[0] = 'int'


def p_type_float(p):
    'type : KW_FLOAT'
    p[0] = 'float'


def p_type_string(p):
    'type : KW_STRING'
    p[0] = 'string'


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
    # Verifica que el ID exista en la tabla de simbolos y obten su tipo
    name_id = p[1]

    # Si la variable NO existe, es un error
    type_id = lookup_var(name_id)
    if not type_id:
        report_semantic_error(f"Variable '{name_id}' no declarada")
        # Para continuar el analisis, asumimos tipo int
        dir = asignar_dir_variable(ds.current_scope, 'int')
        if ds.current_scope == 'global':
            vars_contador["global_int"] += 1
        else:
            vars_contador["local_int"] += 1
        names[ds.current_scope][name_id] = ('int', dir)
        type_id = 'int'

    # operador es '='
    op = '='
    # extrae argumento y tipo de la stack
    arg, tipo = ds.stack_args.pop()
    # extrae type_res del cubo
    tipo_res = cubo.get((type_id, tipo, op), 'err')
    # Si type_res no es error
    if tipo_res != 'err':
        ds.nquads += 1
        new_quad = [ds.nquads, op, get_dir(arg), -1, get_dir(name_id)]
        ds.quad_list.append(new_quad)
    else:
        report_semantic_error(f"Tipo incompatible en asignacion a '{name_id}'")


def p_assign_missing_semicol(p):
    'assign : ID OPASIGNA expresion'
    report_error(f"ERROR: Falta ';' despues de la asignacion a '{p[1]}'", p)
    parser.errok()


# CONDITION
def p_condition_if_else(p):
    'condition : KW_IF LPAREN expresion RPAREN m_gotof body m_goto KW_ELSE body SEMICOL'
    # Calcula el siguiente quad disponible (despues del else)
    end = ds.nquads + 1
    # Extrae de la pila el numero del quad que tiene el Goto pendiente
    if ds.stack_jumps:
        quad_pending = ds.stack_jumps.pop()
        # Rellena el destino del quad Goto
        ds.quad_list[quad_pending - 1][4] = end


def p_condition_if(p):
    'condition : KW_IF LPAREN expresion RPAREN m_gotof body SEMICOL'
    # Calcula el siguiente quad disponible (despues del body)
    end = ds.nquads + 1
    if ds.stack_jumps:
        # Extrae de la pila el numero del quad que tiene el GotoF pendiente
        quad_pending = ds.stack_jumps.pop()
        # Rellena el destino del quad GotoF
        ds.quad_list[quad_pending - 1][4] = end


def p_condition_missing_semicol_if_else(p):
    'condition : KW_IF LPAREN expresion RPAREN m_gotof body m_goto KW_ELSE body'
    report_error("ERROR: Falta ';' despues de la condicion IF-ELSE", p)
    # Limpiar pilas incompletas
    if ds.stack_jumps:
        ds.stack_jumps.pop()
    parser.errok()


def p_condition_missing_semicol_if(p):
    'condition : KW_IF LPAREN expresion RPAREN m_gotof body'
    report_error("ERROR: Falta ';' despues de la condicion IF", p)
    # Limpiar pilas incompletas
    if ds.stack_jumps:
        ds.stack_jumps.pop()
    parser.errok()


def p_condition_error_paren(p):
    '''condition : KW_IF LPAREN expresion body KW_ELSE body SEMICOL
                 | KW_IF LPAREN expresion body SEMICOL'''
    report_error(
        "ERROR: Falta ')' de cierre en la condicion del IF. Resincronizando en ';'",
        p)
    parser.errok()



# Despues de evaluar la expresion genera GotoF
def p_m_gotof(p):
    "m_gotof : "

    # Extrae el resultado de la expresion
    result, tipo = ds.stack_args.pop()

    # Valida que sea bool o int
    if tipo == 'bool':
        ds.nquads += 1

        # Crea el quad con destino pendiente
        new_quad = [ds.nquads, 'gotof', get_dir(result), -1, None]
        ds.quad_list.append(new_quad)

        # Guarda la posicion para rellenarla despues
        ds.stack_jumps.append(ds.nquads)

        # print(ds.nquads, 'GotoF', result, '_', 'pending')
    else:
        report_semantic_error(
            f"La condicion del if debe ser de tipo bool, se encontro {tipo}")


# Punto clave: antes del else, genera Goto para saltar el else
def p_m_goto(p):
    "m_goto : "

    # Genera el Goto incondicional
    ds.nquads += 1
    new_quad = [ds.nquads, 'goto', -1, -1, None]
    ds.quad_list.append(new_quad)

    # Rellena el GotoF anterior (salta del if al else)
    if ds.stack_jumps:
        false_jump = ds.stack_jumps.pop()  # Extrae posicion del GotoF
        ds.quad_list[false_jump -
                     1][4] = ds.nquads + 1  # Destino

    # Guarda el Goto para rellenarlo al final del else
    ds.stack_jumps.append(ds.nquads)


# Despues del DO, guarda el inicio del ciclo
def p_m_do_start(p):
    "m_do_start : "

    # Guarda la posicion del siguiente quad (inicio del body del ciclo)
    start_pos = ds.nquads + 1
    ds.stack_jumps.append(start_pos)
    # print(f"  >> Guardando inicio de ciclo DO en posicion {start_pos}")



# Despues del ID, registrar la funcion
def p_m_func_init(p):
    "m_func_init : "
    pass


# Generar gotomain al iniciar el programa (se rellena despues)
def p_m_gotomain(p):
    "m_gotomain : "
    ds.nquads += 1
    new_quad = [ds.nquads, 'gotomain', -1, -1, None]
    ds.quad_list.append(new_quad)
    ds.main_jump = ds.nquads
    # print(ds.nquads, 'gotomain', ' ', ' ', 'pending')


# Al llegar a main rellenar el gotomain
def p_m_main_start(p):
    "m_main_start : "
    if ds.main_jump:
        start = ds.nquads + 1
        # rellenar el resultado del gotomain
        ds.quad_list[ds.main_jump - 1][4] = start
        # print(f"  >> Rellenando gotomain en quad {ds.main_jump} con destino {start}")

    # Cambiar al scope main para el body del programa
    ds.current_scope = 'main'
    if 'main' not in names:
        names['main'] = {}


# Despues de params y vars, establecer start_quad
def p_m_func_set_start(p):
    "m_func_set_start : "
    # q+1 sera el primer quad del body de la funcion
    start_quad = ds.nquads + 1

    # Actualizar el start_quad en el directorio de la funcion actual
    if ds.current_func and ds.current_func in ds.func_dir:
        ds.func_dir[ds.current_func]['start_quad'] = start_quad
        # print(f"  >> Estableciendo start_quad={start_quad} para funcion '{ds.current_func}'")


# CYCLE
def p_cycle(p):
    'cycle : KW_DO m_do_start LBRACE statement_list RBRACE KW_WHILE LPAREN expresion RPAREN SEMICOL'
    # Extrae el resultado de la expresion
    arg, tipo = ds.stack_args.pop()

    # Valida que sea bool o int
    if tipo == 'bool':
        ds.nquads += 1

        # Extrae el inicio del ciclo de la pila
        destino = ds.stack_jumps.pop()

        # Crea el quad GotoT que salta al inicio del ciclo
        new_quad = [ds.nquads, 'gotot', get_dir(arg), -1, destino]
        ds.quad_list.append(new_quad)

        # print(ds.nquads, 'GotoT', arg, ' ', destino)
    else:
        report_semantic_error(
            f"La condicion del while debe ser de tipo bool, se encontro {tipo}"
        )
        # Limpiar la pila si hay error
        if ds.stack_jumps:
            ds.stack_jumps.pop()


def p_cycle_missing_semicol(p):
    'cycle : KW_DO m_do_start LBRACE statement_list RBRACE KW_WHILE LPAREN expresion RPAREN'
    report_error("ERROR: Falta ';' despues del ciclo DO-WHILE",
                 p,
                 token_index=-1)
    # Limpiar pilas incompletas
    if ds.stack_args:
        ds.stack_args.pop()
    if ds.stack_jumps:
        ds.stack_jumps.pop()
    parser.errok()


# FUNCTION CALL
def p_f_call(p):
    'f_call : ID LPAREN m_sub expresion_list_opt RPAREN SEMICOL'
    func_name = p[1]  # El ID de la función

    # Actualizar el quadruplo 'sub' con el nombre correcto
    # Buscar el último 'sub' generado y actualizar su nombre
    for i in range(len(ds.quad_list) - 1, -1, -1):
        quad = ds.quad_list[i]
        if quad[1] == 'sub':
            quad[2] = func_name
            break

    ds.current_func_call = func_name

    # Checar si la funcion existe
    if not func_name or func_name not in ds.func_dir:
        report_semantic_error(
            f"Llamada a funcion incorrecta para '{func_name if func_name else '?'}' (funcion no declarada)"
        )
    else:
        expected_param_names = ds.func_dir[func_name].get('param_list', [])

        # Verificar numero de parametros
        if len(ds.param_stack) != len(expected_param_names):
            report_semantic_error(
                f"Llamada a funcion incorrecta para '{func_name}': se esperaban {len(expected_param_names)} parametros, recibidos {len(ds.param_stack)}"
            )

        # Validar tipos en orden (si hay param_list y tabla de simbolos)
        for i, (arg, tipo) in enumerate(ds.param_stack):
            if func_name in names and i < len(expected_param_names):
                expected_name = expected_param_names[i]
                entry = names[func_name].get(expected_name)
                expected_type = names[func_name].get(expected_name)
                if entry:
                    expected_type, expected_addr = entry
                    if expected_type and expected_type != tipo:
                        report_semantic_error(
                            f"Tipo de parametro {i+1} incorrecto en llamada a '{func_name}': se esperaba '{expected_type}', se recibio '{tipo}'"
                        )

    # Generar quadruplos 'param' para cada parámetro
    for idx, (arg, tipo) in enumerate(ds.param_stack):
        ds.nquads += 1
        new_quad = [ds.nquads, 'param', get_dir(arg), -1, idx]
        ds.quad_list.append(new_quad)
        # print(ds.nquads, 'param', get_dir(arg), -1, idx)

    # Generar quadruplo 'gosub' - llamada a función
    # Obtener el start_quad de la función desde el directorio
    start_quad = None
    if func_name and func_name in ds.func_dir:
        start_quad = ds.func_dir[func_name].get('start_quad')

    ds.nquads += 1
    new_quad = [
        ds.nquads, 'gosub', func_name, -1, start_quad
    ]
    ds.quad_list.append(new_quad)
    # print(ds.nquads, 'gosub', func_name, start_quad)

    # limpiar pila de params
    ds.param_stack = []


def p_f_call_missing_semicol(p):
    'f_call : ID LPAREN m_sub expresion_list_opt RPAREN'
    func_name = ds.current_func_call if hasattr(ds, 'current_func_call') else (p[1] if len(p) > 1 else '?')
    report_error(
        f"ERROR: Falta ';' despues de la llamada a funcion '{func_name}'",
        p)
    parser.errok()


# Generar quadruplo 'sub' antes de evaluar expresiones
def p_m_sub(p):
    "m_sub : "
    # El ID de la función es el último ID leído
    func_name = wrapped_lexer.last_id if wrapped_lexer.last_id else 'unknown'
    ds.current_func_call = func_name

    # Generar quad 'sub' - señaliza inicio de llamada a función
    ds.nquads += 1
    new_quad_sub = [ds.nquads, 'sub', func_name, -1, -1]
    ds.quad_list.append(new_quad_sub)
    # print(ds.nquads, 'sub', func_name, -1, -1)


# Al empezar la llamada, guardar nombre de la funcion y el estado de la pila de args
def p_m_call_start(p):
    "m_call_start : "
    if wrapped_lexer.last_id:
        ds.current_call_name = wrapped_lexer.last_id
    else:
        ds.current_call_name = None

    # Guardar el indice de la pila de argumentos antes de evaluar los argumentos
    ds.call_arg_start = len(ds.stack_args)
    # print(f"  >> Inicio llamada a funcion '{ds.current_call_name}', call_arg_start={ds.call_arg_start}")


# Al terminar la lista de argumentos, generar quads param y el gosub
def p_m_call_end(p):
    "m_call_end : "
    func_name = getattr(ds, 'current_call_name', None)

    # Checar si la funcion existe
    if not func_name or func_name not in ds.func_dir:
        report_semantic_error(
            f"Llamada a funcion incorrecta para '{func_name if func_name else '?'}' (funcion no declarada)"
        )
        # Generar quads param si hay args igualmente para continuar
    else:
        expected_param_names = ds.func_dir[func_name].get('param_list', [])

        # Verificar numero de parametros
        if len(ds.param_stack) != len(expected_param_names):
            report_semantic_error(
                f"Llamada a funcion incorrecta para '{func_name}': se esperaban {len(expected_param_names)} parametros, recibidos {len(ds.param_stack)}"
            )

        # Validar tipos en orden (si hay param_list y tabla de sibolos)
        for i, (arg, tipo) in enumerate(ds.param_stack):
            if func_name in names and i < len(expected_param_names):
                expected_name = expected_param_names[i]
                entry = names[func_name].get(expected_name)
                if entry:
                    expected_type, expected_addr = entry
                    if expected_type and expected_type != tipo:
                        report_semantic_error(
                            f"Tipo de parametro {i+1} incorrecto en llamada a '{func_name}': se esperaba '{expected_type}', se recibio '{tipo}'"
                        )

    # Generar gosub, obtener start_quad de la funcion
    start_quad = None
    if func_name and func_name in ds.func_dir:
        start_quad = ds.func_dir[func_name].get('start_quad')

    # Generar quad 'sub' primero
    ds.nquads += 1
    dir = ds.func_dir[func_name].get('address')
    new_quad_sub = [ds.nquads, 'sub', dir, -1, -1]
    ds.quad_list.append(new_quad_sub)
    # print(ds.nquads, 'sub', func_name if func_name else ' ', ' ', -1)

    # Generar quads param en orden con indices
    for idx, (arg, tipo) in enumerate(ds.param_stack):
        ds.nquads += 1
        new_quad = [ds.nquads, 'param', get_dir(arg), -1, idx]
        ds.quad_list.append(new_quad)
        # print(ds.nquads, 'param', arg, ' ', idx)

    # Generar quad 'gosub'
    ds.nquads += 1
    new_quad = [
        ds.nquads, 'gosub', dir, -1, start_quad
    ]
    ds.quad_list.append(new_quad)
    # print(ds.nquads, 'gosub', func_name if func_name else ' ', ' ', start_quad)

    # limpiar campos temporales
    ds.current_call_name = None
    ds.call_arg_start = None
    ds.param_stack = []


def p_expresion_list_opt_list(p):
    'expresion_list_opt : expresion_list'


def p_expresion_list_opt_empty(p):
    'expresion_list_opt : empty'


def p_expresion_list_rec(p):
    'expresion_list : expresion m_param_push COMA expresion_list'


def p_expresion_list_single(p):
    'expresion_list : expresion m_param_push'


# PRINT
def p_print(p):
    'print : KW_PRINT LPAREN print_list RPAREN SEMICOL'
    # Despues del punto y coma, agregar un print de salto de linea
    ds.nquads += 1
    new_quad = [ds.nquads, 'print', -1, -1, -1]
    ds.quad_list.append(new_quad)
    # print(ds.nquads, 'print', '\\n', " ", " ")


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
    # Despues de cada expresion o string, generar el cuadruplo print
    arg, tipo = ds.stack_args.pop()
    ds.nquads += 1
    new_quad = [ds.nquads, 'print', get_dir(arg), -1, -1]
    ds.quad_list.append(new_quad)
    # print(ds.nquads, 'print', arg, " ", " ")


# EXPRESIONES
def p_expresion_gt(p):
    'expresion : exp GT exp'
    quad_gen_two_arg_ops('>')


def p_expresion_lt(p):
    'expresion : exp LT exp'
    quad_gen_two_arg_ops('<')


def p_expresion_ne(p):
    'expresion : exp NE exp'
    quad_gen_two_arg_ops('!=')


def p_expresion_ge(p):
    'expresion : exp GE exp'
    quad_gen_two_arg_ops('>=')


def p_expresion_le(p):
    'expresion : exp LE exp'
    quad_gen_two_arg_ops('<=')


def p_expresion_eqeq(p):
    'expresion : exp EQEQ exp'
    quad_gen_two_arg_ops('==')


def p_expresion_single(p):
    'expresion : exp'


# EXP
def p_exp_plus(p):
    'exp : exp PLUS termino'
    quad_gen_two_arg_ops('+')


def p_exp_minus(p):
    'exp : exp MINUS termino'
    quad_gen_two_arg_ops('-')


def p_exp_termino(p):
    'exp : termino'


# TERMINO
def p_termino_times(p):
    'termino : termino TIMES factor'
    quad_gen_two_arg_ops('*')


def p_termino_divide(p):
    'termino : termino DIVIDE factor'
    quad_gen_two_arg_ops('/')


def p_termino_factor(p):
    'termino : factor'


# FACTOR
def p_factor_group(p):
    'factor : LPAREN expresion RPAREN'


def p_factor_plus(p):
    'factor : PLUS factor_base'
    pass


def p_factor_minus(p):
    'factor : MINUS factor_base'
    # generar un temporal = arg * -1
    arg, tipo = ds.stack_args.pop()

    if tipo not in ('int', 'float'):
        report_semantic_error(f"Operador unario '-' solo aplica a int/float, se encontro {tipo}")
        ds.stack_args.append((arg, tipo)) # para poder continuar
        return

    # Si es constante se convierte a su negativo
    if isinstance(arg, (int, float)):
        neg = -arg
        if neg not in tabla_constantes:
            if tipo == 'int':
                address = direcciones_base['cte_int'] + vars_contador['cte_int']
                vars_contador['cte_int'] += 1
            else:
                address = direcciones_base['cte_float'] + vars_contador['cte_float']
                vars_contador['cte_float'] += 1
            tabla_constantes[neg] = address
        ds.stack_args.append((neg, tipo))
        return

    # Si es variable o temporal se genera temp = arg * (-1)
    neg_one = -1 if tipo == 'int' else -1.0
    if neg_one not in tabla_constantes:
        if tipo == 'int':
            address = direcciones_base['cte_int'] + vars_contador['cte_int']
            vars_contador['cte_int'] += 1
        else:
            address = direcciones_base['cte_float'] + vars_contador['cte_float']
            vars_contador['cte_float'] += 1
        tabla_constantes[neg_one] = address

    # crear temporal
    ds.nquads += 1
    ds.ntemps += 1
    temp = "t" + str(ds.ntemps)
    ds.temp_types[temp] = tipo

    dir_temp = direcciones_base[f'temp_{tipo}'] + vars_contador[f'temp_{tipo}']
    vars_contador[f'temp_{tipo}'] += 1

    scope = ds.current_scope
    if scope not in names:
        names[scope] = {}
    names[scope][temp] = (tipo, dir_temp)

    # cuadruplo: temp = arg * (-1)
    new_quad = [ds.nquads, '*', get_dir(arg), tabla_constantes[neg_one], get_dir(temp)]
    ds.quad_list.append(new_quad)

    ds.stack_args.append((temp, tipo))


def p_factor_factor_base(t):
    'factor : factor_base'


def p_factor_base_id(p):
    'factor_base : ID'
    # accede a la tabla de simbolos
    # verifica que el id exista, y extrae su tipo
    name_id = p[1]

    type_id = lookup_var(name_id)
    if type_id:
        ds.stack_args.append((name_id, type_id))
    else:
        report_semantic_error(f"Variable '{name_id}' no declarada")
        # Asumimos int para continuar el analisis
        dir = asignar_dir_variable(ds.current_scope, 'int')
        if ds.current_scope == 'global':
            vars_contador["global_int"] += 1
        else:
            vars_contador["local_int"] += 1
        names[ds.current_scope][name_id] = ('int', dir)
        ds.stack_args.append((name_id, 'int'))


def p_factor_cte(p):
    'factor_base : cte'


# CTE
def p_cte_int(p):
    'cte : CONS_INT'
    # push operando con tipo int
    ds.stack_args.append((p[1], 'int'))
    # generar direccion y guardar en tabla de constantes
    val = p[1]
    if val not in tabla_constantes:
        address = direcciones_base['cte_int'] + vars_contador['cte_int']
        vars_contador['cte_int'] += 1
        tabla_constantes[val] = address


def p_cte_float(p):
    'cte : CONS_FLOAT'
    # push operando con tipo float
    ds.stack_args.append((p[1], 'float'))
    # generar direccion y guardar en tabla de constantes
    val = p[1]
    if val not in tabla_constantes:
        address = direcciones_base['cte_float'] + vars_contador['cte_float']
        vars_contador['cte_float'] += 1
        tabla_constantes[val] = address


def p_cte_string(p):
    'cte : STRING'
    # push operando con tipo string
    ds.stack_args.append((p[1], 'string'))
    # generar direccion y guardar en tabla de constantes
    val = p[1]
    if val not in tabla_constantes:
        address = direcciones_base['cte_string'] + vars_contador['cte_string']
        vars_contador['cte_string'] += 1
        tabla_constantes[val] = address


# FUNCIONES
def p_funcs_list_rec(p):
    'funcs_list : funcs funcs_list'


def p_funcs_list_empty(p):
    'funcs_list : empty'


def p_funcs(p):
    'funcs : KW_VOID func_header LPAREN params_opt RPAREN LBRACKET vars_opt func_body body RBRACKET SEMICOL'
    func_name = p[2]  # func_header retorna el nombre

    # Despues del semicol, generar el cuadruplo endfunc
    ds.nquads += 1
    new_quad = [ds.nquads, 'endfunc', -1, -1, -1]
    ds.quad_list.append(new_quad)
    # print(ds.nquads, 'endfunc', " ", " ", " ")

    # Actualizar el registro de la funcion
    if func_name in ds.func_dir:
        ds.func_dir[func_name]['n_params'] = ds.param_counter
        ds.func_dir[func_name]['n_local_vars'] = ds.local_var_counter
        # print(
        #    f"  >> Funcion '{func_name}' completada: start_quad={ds.func_dir[func_name]['start_quad']}, n_params={ds.func_dir[func_name]['n_params']}, n_local_vars={ds.func_dir[func_name]['n_local_vars']}"
        # )

    # Restaurar el scope a main
    ds.current_scope = 'main'
    ds.current_func = None
    ds.param_counter = 0
    ds.local_var_counter = 0


# Regla auxiliar para procesar el header de la funcion
def p_func_header(p):
    'func_header : ID'
    func_name = p[1]

    # Validar que no use el nombre del programa
    if ds.program_name and func_name == ds.program_name:
        report_semantic_error(
            f"Funcion '{func_name}' no puede usar el nombre del programa")

    if func_name in ds.func_dir:
        report_semantic_error(f"Funcion '{func_name}' ya fue declarada")

    # Registrar la funcion en el directorio
    ds.func_dir[func_name] = {
        'return_type': 'void',
        'start_quad': None,  # Se establecera despues
        'n_params': 0,
        'n_local_vars': 0,
        'var_table': func_name,
        'param_list': [],
        'address': direcciones_base['global_void'] + vars_contador['global_void']
    }
    vars_contador['global_void'] += 1

    # Establecer scope actual y funcion actual
    ds.current_scope = func_name
    ds.current_func = func_name
    ds.param_counter = 0
    ds.local_var_counter = 0

    # Resetear contadores de variables locales para esta función
    vars_contador['local_int'] = 0
    vars_contador['local_float'] = 0
    vars_contador['local_string'] = 0
    vars_contador['temp_int'] = 0
    vars_contador['temp_float'] = 0
    vars_contador['temp_bool'] = 0

    # Crear tabla de simbolos para esta funcion
    if func_name not in names:
        names[func_name] = {}

    # print(f">> Registrando funcion '{func_name}' en directorio")

    # Retornar el nombre para usarlo despues
    p[0] = func_name


# Regla auxiliar para establecer el start_quad
def p_func_body(p):
    'func_body : '
    # Este punto se ejecuta justo antes del body
    # q+1 sera el primer quad del body
    start_quad = ds.nquads + 1

    if ds.current_func and ds.current_func in ds.func_dir:
        ds.func_dir[ds.current_func]['start_quad'] = start_quad
        # print(
        #    f"  >> Estableciendo start_quad={start_quad} para funcion '{ds.current_func}'"
        # )


def p_funcs_missing_semicol(p):
    'funcs : KW_VOID func_header LPAREN params_opt RPAREN LBRACKET vars_opt func_body body RBRACKET'
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
    # Registrar el parametro en la tabla de simbolos del scope actual
    param_name = p[1]
    param_type = p[3]

    if ds.current_scope not in names:
        names[ds.current_scope] = {}

    # Validar que el parámetro no tenga el mismo nombre que la función
    if ds.current_func and param_name == ds.current_func:
        report_semantic_error(
            f"Parametro '{param_name}' no puede tener el mismo nombre que la funcion '{ds.current_func}'"
        )
    elif param_name in names[ds.current_scope]:
        report_semantic_error(
            f"Parametro '{param_name}' ya fue declarado en '{ds.current_scope}'"
        )
    else:
        dir = asignar_dir_variable(ds.current_scope, param_type)
        names[ds.current_scope][param_name] = (param_type, dir)
        vars_contador[f"local_{param_type}"] += 1
        ds.param_counter += 1
        # print(
        #    f">> Parametro '{param_name}' declarado como '{param_type}' en '{ds.current_scope}'"
        # )
        if ds.current_scope in ds.func_dir:
            ds.func_dir[ds.current_scope]['param_list'].append(param_name)


# Despues de evaluar una expresion en una lista de argumentos, moverla a param_stack
def p_m_param_push(p):
    "m_param_push : "
    if ds.stack_args:
        arg, tipo = ds.stack_args.pop()
        # Evitar el marcador inicial ('none','none')
        if arg != 'none' or tipo != 'none':
            # Solo guardar en param_stack, NO generar quadruplo aquí
            # Los quadruplos se generarán en el orden correcto en p_f_call
            ds.param_stack.append((arg, tipo))
            # print(f"  >> Param push: {arg} : {tipo}")


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
    # print(full_msg)
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
    '''cycle : KW_DO m_do_start LBRACE statement_list RBRACE KW_WHILE LPAREN error RPAREN SEMICOL
             | KW_DO m_do_start LBRACE statement_list RBRACE error SEMICOL'''
    report_error("ERROR: Ciclo DO-WHILE incorrecto", p)
    # Limpiar pilas incompletas
    if ds.stack_args:
        ds.stack_args.pop()
    if ds.stack_jumps:
        ds.stack_jumps.pop()
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
    'funcs : KW_VOID func_header LPAREN error RPAREN LBRACKET vars_opt func_body body RBRACKET SEMICOL'
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
        # print(full_msg)
        errores_encontrados.append(full_msg)
    else:
        full_msg = "ERROR: Fin de entrada inesperado"
        # print(full_msg)
        errores_encontrados.append(full_msg)

# ==================== EJECUCION ====================

if __name__ == '__main__':
    # Configurar archivo de entrada
    base_dir = os.path.dirname(__file__)
    default_path = os.path.join(base_dir, "test.txt")
    input_path = sys.argv[1] if len(sys.argv) > 1 else default_path

    # Leer archivo
    with open(input_path, "r", encoding="utf-8") as f:
        codigo = f.read()

    # Resetear errores y estructuras de datos
    errores_encontrados = []
    errores_semanticos = []
    ds.__init__()  # Reinicializar estructuras persistentes
    names.clear()
    names['global'] = {}

    # Parsear
    parser = yacc.yacc()
    parser.parse(codigo, lexer=wrapped_lexer)

    # Reporte final
    print("\n" + "=" * 50)
    print("Analisis sintactico completado.")
    print(
        f"Total de errores de sintaxis encontrados: {len(errores_encontrados)}"
    )
    print(
        f"Total de errores semanticos encontrados: {len(errores_semanticos)}")
    print("=" * 50)

    # Reporte detallado de errores
    if errores_encontrados or errores_semanticos:
        print("\n" + "=" * 80)
        print("RESUMEN DETALLADO DE ERRORES:")
        print("=" * 80)

        if errores_encontrados:
            print(f"\nErrores de Sintaxis ({len(errores_encontrados)}):")
            print("-" * 80)
            for i, error in enumerate(errores_encontrados, 1):
                print(f"{i}. {error}")

        if errores_semanticos:
            print(f"\nErrores Semanticos ({len(errores_semanticos)}):")
            print("-" * 80)
            for i, error in enumerate(errores_semanticos, 1):
                print(f"{i}. {error}")

        print("=" * 80)

    """
    # Reporte de cuadruplos generados
    if ds.quad_list:
        print("\n" + "=" * 80)
        print("TABLA DE QUADRUPLES CON TIPO DE RESULTADO:")
        print("=" * 80)
        print(
            f"{'#':<5} {'Operador':<10} {'Arg1':<10} {'Arg2':<10} {'Resultado':<12} {'Tipo':<10}"
        )
        print("-" * 80)

        for q in ds.quad_list:
            num, op, arg1, arg2, result = q

            if result in ds.temp_types:
                tipo_resultado = ds.temp_types[result]
            else:
                tipo_encontrado = None
                for scope_vars in names.values():
                    if isinstance(scope_vars, dict) and result in scope_vars:
                        tipo_encontrado = scope_vars[result]
                        break

                if tipo_encontrado:
                    tipo_resultado = tipo_encontrado
                elif op in ['gotof', 'goto']:
                    tipo_resultado = ' '
                else:
                    tipo_resultado = ' '

            print(
                f"{num:<5} {op:<10} {str(arg1):<10} {str(arg2):<10} {str(result):<12} {tipo_resultado:<10}"
            )

        print("=" * 80)

    # Reporte de directorio de funciones
    if ds.func_dir:
        print("\n" + "=" * 80)
        print("DIRECTORIO DE FUNCIONES:")
        print("=" * 80)
        print(
            f"{'Funcion':<15} {'Tipo':<10} {'Start':<10} {'Params':<10} {'Vars Loc':<10} {'Address':<10}"
        )
        print("-" * 80)
        for func_name, func_info in ds.func_dir.items():
            ret_type = func_info.get('return_type', '-')
            start = func_info.get('start_quad', '-')
            params = func_info.get('n_params', 0)
            local_vars = func_info.get('n_local_vars', 0)
            address = func_info.get('address', '-')
            print(
                f"{func_name:<15} {ret_type:<10} {start:<10} {params:<10} {local_vars:<10} {address:<10}"
            )
        print("=" * 80)

    # Reporte de tabla de simbolos
    if names and any(names.values()):
        print("\n" + "=" * 80)
        print("TABLA DE SIMBOLOS:")
        print("=" * 80)
        print(f"{'Variable':<15} {'Tipo':<10} {'Scope':<10} {'Direccion':<10}")
        print("-" * 80)
        for scope, variables in names.items():
            for var_name, var_data in variables.items():
                var_type, var_dir = var_data
                print(f"{var_name:<15} {var_type:<10} {scope:<10} {var_dir:<10}")
        print("=" * 80)
    """

    # Escribir reporte en archivo txt
    with open("input_vm.txt", 'w', encoding='utf-8') as out:
        for key, num in tabla_constantes.items():
            out.write(f"{key}\t{num}\n")
        out.write("\n")
        for key, num in vars_contador.items():
            out.write(f"{key}\t{num}\n")
        out.write("\n")
        for q in ds.quad_list:
            num, op, arg1, arg2, result = q
            out.write(f"{num}\t{op}\t{str(arg1)}\t{str(arg2)}\t{str(result)}\n")
