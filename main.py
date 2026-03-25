"""
Sistema de compilación e interpretación para Little Duck
Integración de compilador y máquina virtual
"""

import sys
import subprocess
import os

def main():
    # Verificar argumentos
    # if len(sys.argv) != 2:
    #     print("Uso: python main.py <archivo_fuente.txt>")
    #     sys.exit(1)

    source_file = "test.txt" #sys.argv[1]

    # Verificar que el archivo existe
    if not os.path.exists(source_file):
        print(f"Error: El archivo '{source_file}' no existe.")
        sys.exit(1)

    print("="*80)
    print("LITTLE DUCK COMPILER & VM")
    print("="*80)
    print(f"Archivo fuente: {source_file}")
    print("="*80)
    print()

    # Fase 1: Compilación
    print("FASE 1: COMPILACIÓN")

    compile_result = subprocess.run(
        ["python", "parser.py", source_file],
        capture_output=True,
        text=True
    )

    # Mostrar salida del compilador
    print(compile_result.stdout)

    if compile_result.stderr:
        print("Errores del compilador:")
        print(compile_result.stderr)

    # Si hubo errores, terminar
    if compile_result.returncode != 0:
        print("="*80)
        print("COMPILACIÓN FALLIDA - Programa terminado")
        print("="*80)
        sys.exit(1)

    # Verificar si hubo errores de sintaxis o semánticos
    if "errores de sintaxis encontrados: 0" not in compile_result.stdout.lower() or \
       "errores semanticos encontrados: 0" not in compile_result.stdout.lower():
        # El compilador reportó errores pero no salió con error code
        # Extraer info de errores si está disponible
        print("="*80)
        print("COMPILACIÓN COMPLETADA CON ERRORES")
        print("="*80)
        sys.exit(1)

    print("="*80)
    print("COMPILACIÓN EXITOSA")
    print("="*80)
    print()

    # Fase 2: Ejecución en VM
    print("FASE 2: EJECUCIÓN EN MÁQUINA VIRTUAL")
    print()
    print("="*80)

    vm_result = subprocess.run(
        ["python", "vm.py"],
        capture_output=True,
        text=True
    )

    # Mostrar salida del VM
    print(vm_result.stdout)

    if vm_result.stderr:
        print("Errores de ejecución:")
        print(vm_result.stderr)

    # Determinar el resultado final
    if vm_result.returncode == 0:
        print()
        print("="*80)
        print("EJECUCIÓN COMPLETADA EXITOSAMENTE")
        print("="*80)
    else:
        print()
        print("="*80)
        print("EJECUCIÓN TERMINADA CON ERRORES DE RUNTIME")
        print("="*80)
        sys.exit(1)

if __name__ == "__main__":
    main()
