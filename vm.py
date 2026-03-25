import os
import sys

base_dir = os.path.dirname(__file__)
default_path = os.path.join(base_dir, "input_vm.txt")
input_path = sys.argv[1] if len(sys.argv) > 1 else default_path

with open(input_path, "r") as f:
  test = f.read()


class Quad():
  op = -1
  arg1 = -1
  arg2 = -1
  destino = -1

  def __init__(self, lista):
    self.op = lista[1]
    # Manejar arg1: puede ser int o string (nombre de función)
    try:
      self.arg1 = int(lista[2])
    except ValueError:
      self.arg1 = lista[2]
    # Manejar arg2
    try:
      self.arg2 = int(lista[3])
    except ValueError:
      self.arg2 = lista[3]
    # Manejar destino
    try:
      self.destino = int(lista[4])
    except ValueError:
      self.destino = lista[4]


class ActivationRecord():
  """Frame de activación para una función"""
  def __init__(self, func_name, return_address):
    self.func_name = func_name
    self.return_address = return_address
    self.local_memory = {}  # Memoria local (7000-9999)
    self.temp_memory = {}  # Memoria temporal (12000-14999)


cte_dir = {}
quads = {}
regions = {
    "global_int": ['1000'],
    "global_float": ['2000'],
    "global_string": ['3000'],
    "global_void": ['4000'],
    "local_int": ['7000'],
    "local_float": ['8000'],
    "local_string": ['9000'],
    "temp_int": ['12000'],
    "temp_float": ['13000'],
    "temp_bool": ['14000'],
    "cte_int": ['17000'],
    "cte_float": ['18000'],
    "cte_string": ['19000']
}
memo = {}

# Límite de recursión
MAX_CALL_STACK_SIZE = 1000

# Stack de activation records
activation_stack = []


def is_local(address):
  """Verifica si una dirección es local (7000-9999)"""
  return 7000 <= address <= 9999


def is_temp(address):
  """Verifica si una dirección es temporal (12000-14999)"""
  return 12000 <= address <= 14999


def is_global(address):
  """Verifica si una dirección es global (1000-4999)"""
  return 1000 <= address <= 4999


def address_type(address):
  """Devuelve el tipo segun la direccion"""
  if 1000 <= address < 2000 or 7000 <= address < 8000 or 12000 <= address < 13000 or 17000 <= address < 18000:
    return 'int'
  if 2000 <= address < 3000 or 8000 <= address < 9000 or 13000 <= address < 14000 or 18000 <= address < 19000:
    return 'float'
  if 3000 <= address < 4000 or 9000 <= address < 10000 or 19000 <= address < 20000:
    return 'string'
  if 14000 <= address < 15000:
    return 'bool'
  return None


def get_memory_value(address):
  """Obtiene el valor de una dirección, considerando el contexto actual"""
  if address == -1:
    return -1
  # Validar que la dirección esté en rangos válidos
  if not (1000 <= address <= 19999):
    raise RuntimeError(
        f"ERROR DE RUNTIME: Acceso a memoria inválida - dirección {address} fuera de rango"
    )
  # Si es local o temp: debe existir un frame activo
  if is_local(address) or is_temp(address):
    if not activation_stack:
      raise RuntimeError(
          f"ERROR DE RUNTIME: Acceso a memoria local/temporal sin frame activo - direccion {address}"
      )
    current_frame = activation_stack[-1]
    if is_local(address):
      if address not in current_frame.local_memory:
        raise RuntimeError(
            f"ERROR DE RUNTIME: Variable en direccion {address} usada sin inicializar"
        )
      return current_frame.local_memory[address]
    elif is_temp(address):
      if address not in current_frame.temp_memory:
        raise RuntimeError(
            f"ERROR DE RUNTIME: Variable en direccion {address} usada sin inicializar"
        )
      return current_frame.temp_memory[address]
  # Para direcciones globales y constantes
  if address not in memo:
    raise RuntimeError(
        f"ERROR DE RUNTIME: Variable en dirección {address} usada sin inicializar"
    )
  return memo[address]


def set_memory_value(address, value):
  """Establece el valor de una dirección, considerando el contexto actual"""
  if address == -1:
    return
  # Validar que la dirección esté en rangos válidos
  if not (1000 <= address <= 19999):
    raise RuntimeError(
        f"ERROR DE RUNTIME: Acceso a memoria inválida - dirección {address} fuera de rango"
    )
  # No permitir escribir en memoria de constantes (17000-19999)
  if 17000 <= address <= 19999:
    raise RuntimeError(
        f"ERROR DE RUNTIME: Intento de escritura en memoria de constantes - dirección {address}"
    )
  # Si es una dirección global (1000-4999), siempre usar memo
  if is_global(address):
    memo[address] = value
    return
  # Si hay un frame activo y la dirección es local o temporal
  if is_local(address) or is_temp(address):
    if not activation_stack:
      raise RuntimeError(
          f"ERROR DE RUNTIME: Escritura en memoria local/temporal sin frame activo - dirección {address}"
      )
    current_frame = activation_stack[-1]
    if is_local(address):
      current_frame.local_memory[address] = value
      return
    elif is_temp(address):
      current_frame.temp_memory[address] = value
      return
  raise RuntimeError(f"ERROR DE RUNTIME: Dirección no manejada {address}")


seccion = 0  # inicia en 0, avanza cada vez que aparezca una linea vacia
lineas = test.split("\n")

# Identifica de que linea se trata
#  constante: seccion 0, len 2
#  contadores de memoria :  seccion 1, len 2
#  quads: seccion 2, len 5
for i in lineas:
  linea_original = i.strip()

  # Si la línea está vacía, cambiar de sección
  if not linea_original:
    seccion += 1
    continue

  if seccion == 0:
    # Parsear constantes
    if linea_original.startswith('"'):
      # String: buscar el cierre de comillas y luego el tab
      end_quote = linea_original.rfind('"')
      if end_quote > 0:
        valor_raw = linea_original[1:end_quote]  # Sin las comillas
        resto = linea_original[end_quote + 1:].strip()
        direccion = int(resto)
        memo[direccion] = valor_raw
    else:
      # Número: separar por whitespace
      partes = linea_original.split()
      if len(partes) == 2:
        valor_raw = partes[0]
        direccion = int(partes[1])
        # ENTERO
        if valor_raw.isdigit() or (valor_raw.startswith(
            ('-', '+')) and valor_raw[1:].isdigit()):
          memo[direccion] = int(valor_raw)
        # FLOAT
        else:
          try:
            memo[direccion] = float(valor_raw)
          except:
            raise ValueError(f"Constante inválida: {valor_raw}")
  elif seccion == 1:
    linea = linea_original.split()
    if len(linea) == 2:
      tipo = linea[0]
      regions[tipo].append(int(linea[1]))
  elif seccion == 2:
    linea = linea_original.split()
    if len(linea) == 5:
      quads[int(linea[0])] = Quad(linea)

# for k, v in quads.items():
#   print(k, v.op, v.arg1, v.arg2, v.destino)

current_q = 1
print_line_string = ""

param_stack = []
pending_func_name = None  # Para guardar el nombre de función durante 'sub'

# Límite de iteraciones para evitar loops infinitos
MAX_ITERATIONS = 1000
iteration_count = 0

# Envolver ejecución en try-catch para capturar errores de runtime
try:
  # Por cada quad, identifica que es y realiza la operacion correcta
  while current_q <= len(quads):
    q = quads[current_q]

    # Verificar límite de iteraciones
    iteration_count += 1
    if iteration_count > MAX_ITERATIONS:
      print(f"\n*** LÍMITE DE ITERACIONES ALCANZADO ({MAX_ITERATIONS}) ***")
      print(f"Última posición: quad {current_q}")
      print(f"Operación: {q.op}")
      if activation_stack:
        print(f"Frame actual: {activation_stack[-1].func_name}")
        print(f"Profundidad de stack: {len(activation_stack)}")
      break

    if q.op == 'gotomain':
      # Crear frame para main y push a la stack
      main_frame = ActivationRecord('main', None)
      activation_stack.append(main_frame)
      current_q = q.destino
      continue
    elif q.op == 'sub':
      # Preparar llamada a función: guardar nombre y limpiar param_stack
      pending_func_name = q.arg1 if isinstance(q.arg1, str) else str(q.arg1)
      # No incrementar current_q aquí, continuar normalmente
    elif q.op == "param":
      # Agregar parámetro a la pila
      param_stack.append(get_memory_value(q.arg1))
    elif q.op == "gosub":
      # Verificar límite de recursión
      if len(activation_stack) >= MAX_CALL_STACK_SIZE:
        raise RuntimeError(
            f"Error: Stack overflow - límite de recursión alcanzado ({MAX_CALL_STACK_SIZE})"
        )

      # Crear nuevo activation record
      return_address = current_q + 1
      func_name = pending_func_name if pending_func_name else 'unknown'
      new_frame = ActivationRecord(func_name, return_address)

      # Asignar parámetros a memoria local de la función
      # Los parámetros se asignan según el orden y tipo en que fueron declarados
      # Necesitamos asignarlos a las direcciones correctas según la declaración de la función

      # Contador por tipo para asignar direcciones
      local_int_index = 0
      local_float_index = 0
      local_string_index = 0

      for i, param_value in enumerate(param_stack):
        # Determinar el tipo y asignar a la dirección correspondiente
        if isinstance(param_value, str):
          address = 9000 + local_string_index  # local_string
          local_string_index += 1
        elif isinstance(param_value, float):
          address = 8000 + local_float_index  # local_float
          local_float_index += 1
        else:  # int o por defecto
          address = 7000 + local_int_index  # local_int
          local_int_index += 1

        new_frame.local_memory[address] = param_value

      # Push del frame a la stack
      activation_stack.append(new_frame)

      # Limpiar pila de parámetros
      param_stack = []
      pending_func_name = None

      # Saltar a la función
      current_q = q.destino
      continue
    elif q.op == "endfunc":
      # Pop del frame actual
      if not activation_stack:
        raise RuntimeError("Error: Intento de pop en stack vacía")

      finished_frame = activation_stack.pop()

      # Si era main, terminar programa
      if finished_frame.func_name == 'main':
        break

      # Restaurar dirección de retorno
      if finished_frame.return_address is not None:
        current_q = finished_frame.return_address
        continue
      else:
        break
    elif q.op == "goto":
      current_q = q.destino
      continue
    elif q.op == 'gotof':
      if get_memory_value(q.arg1) == 0 or get_memory_value(q.arg1) is False:
        current_q = q.destino
        continue
    elif q.op == "gotot":
      if get_memory_value(q.arg1) == 1 or get_memory_value(q.arg1) is True:
        current_q = q.destino
        continue
    elif q.op == '=':
      set_memory_value(q.destino, get_memory_value(q.arg1))
      val = get_memory_value(q.arg1)
      # Si destino es int pero la fuente es float, truncar
      dest_t = address_type(q.destino) if isinstance(q.destino, int) else None
      if dest_t == 'int' and isinstance(val, float):
        val = int(val)
      set_memory_value(q.destino, val)
    elif q.op == '+':
      set_memory_value(q.destino,
                       get_memory_value(q.arg1) + get_memory_value(q.arg2))
    elif q.op == '-':
      set_memory_value(q.destino,
                       get_memory_value(q.arg1) - get_memory_value(q.arg2))
    elif q.op == '*':
      set_memory_value(q.destino,
                       get_memory_value(q.arg1) * get_memory_value(q.arg2))
    elif q.op == '/':
      divisor = get_memory_value(q.arg2)
      if divisor == 0:
        raise RuntimeError(
            f"División entre cero detectada: {get_memory_value(q.arg1)} / {divisor}"
        )
      set_memory_value(q.destino, get_memory_value(q.arg1) / divisor)
    elif q.op == '>':
      set_memory_value(q.destino,
                       get_memory_value(q.arg1) > get_memory_value(q.arg2))
    elif q.op == '<':
      set_memory_value(q.destino,
                       get_memory_value(q.arg1) < get_memory_value(q.arg2))
    elif q.op == '>=':
      set_memory_value(q.destino,
                       get_memory_value(q.arg1) >= get_memory_value(q.arg2))
    elif q.op == '<=':
      set_memory_value(q.destino,
                       get_memory_value(q.arg1) <= get_memory_value(q.arg2))
    elif q.op == '==':
      set_memory_value(q.destino,
                       get_memory_value(q.arg1) == get_memory_value(q.arg2))
    elif q.op == '!=':
      set_memory_value(q.destino,
                       get_memory_value(q.arg1) != get_memory_value(q.arg2))
    elif q.op == 'print':
      if q.arg1 != -1:
        print_line_string += " " + str(get_memory_value(q.arg1))
      else:
        print("quack>", print_line_string, sep="")
        print_line_string = ""
    current_q += 1

except RuntimeError as e:
  # Errores de runtime controlados (división por cero, acceso inválido, etc.)
  print(f"\n{'='*80}")
  print(f"*** ERROR DE RUNTIME ***")
  print(f"{'='*80}")
  print(f"{str(e)}")
  if current_q <= len(quads):
    q = quads[current_q]
    print(f"Quad actual: {current_q}")
    print(f"Operación: {q.op} {q.arg1} {q.arg2} -> {q.destino}")
  if activation_stack:
    print(f"Contexto: función '{activation_stack[-1].func_name}'")
    print(f"Profundidad de stack: {len(activation_stack)}")
  print(f"{'='*80}")
  sys.exit(1)

except Exception as e:
  # Otros errores inesperados
  print(f"\n{'='*80}")
  print(f"*** ERROR INESPERADO ***")
  print(f"{'='*80}")
  print(f"Tipo: {type(e).__name__}")
  print(f"Mensaje: {str(e)}")
  if current_q <= len(quads):
    print(f"Quad actual: {current_q}")
  print(f"{'='*80}")
  import traceback
  traceback.print_exc()
  sys.exit(1)
