"""Taller 3 - Informática 1 (UdeA): gestión de datos biomédicos y MongoDB."""
import csv
import json
import os
import random
import re
import shutil
from datetime import datetime
from pathlib import Path

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
except ImportError:  # permite usar el resto del programa sin pymongo
    MongoClient = None
    PyMongoError = Exception

# ---------------------------------------------------------------- rutas
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DIRS = {
    "txt": DATA_DIR / "txt",
    "csv": DATA_DIR / "csv",
    "json": DATA_DIR / "json",
}
LOG_FILE = BASE_DIR / "log.txt"
CAMPOS = ["id", "fr", "fc", "spo2"]

# ------------------------------------------------- expresiones regulares
PATRONES = {
    "id": re.compile(r"^ID-\d{3}$"),
    "fr": re.compile(r"^\d{2,3} Años$"),
    "fc": re.compile(r"^\d{3}ppm$"),
    "spo2": re.compile(r"^\d{2,3}%$"),
}

# --------------------------------------------------------------- MongoDB
# Defina la variable de entorno MONGO_URI con su cadena de MongoDB Atlas.
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = "biomedico"
COLECCION = "signos_vitales"


# ------------------------------------------------------------------ log
def registrar_log(mensaje):
    """Agrega una línea con fecha y hora a log.txt."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {mensaje}\n")
    except OSError as e:
        print(f"No se pudo escribir el log: {e}")


# ------------------------------------------------- carpetas y archivos
def crear_estructura():
    for ruta in DIRS.values():
        ruta.mkdir(parents=True, exist_ok=True)
    registrar_log("Estructura de carpetas verificada (data/txt, data/csv, data/json)")


def organizar_archivos():
    """Mueve a data/<ext> cualquier .txt/.csv/.json suelto junto a main.py."""
    crear_estructura()
    movidos = 0
    for archivo in BASE_DIR.iterdir():
        ext = archivo.suffix.lstrip(".").lower()
        if archivo.is_file() and ext in DIRS and archivo.name != LOG_FILE.name:
            destino = DIRS[ext] / archivo.name
            shutil.move(str(archivo), str(destino))
            registrar_log(f"Archivo movido: {archivo.name} -> {destino.relative_to(BASE_DIR)}")
            movidos += 1
    return movidos


# ------------------------------------------------------------ registros
def generar_registros(n=50):
    registros = []
    for i in range(1, n + 1):
        registros.append({
            "id": f"ID-{i:03d}",
            "fr": f"{random.randint(18, 90)} Años",
            "fc": f"{random.randint(50, 130):03d}ppm",
            "spo2": f"{random.randint(88, 100)}%",
        })
    registrar_log(f"Generados {n} registros aleatorios")
    return registros


def valor_numerico(texto):
    """Extrae el número de un campo como '090ppm' -> 90."""
    return int(re.search(r"\d+", texto).group())


def merge_sort(lista, clave):
    """Ordenamiento por mezcla (merge sort), implementado manualmente."""
    if len(lista) <= 1:
        return lista
    medio = len(lista) // 2
    izq = merge_sort(lista[:medio], clave)
    der = merge_sort(lista[medio:], clave)
    resultado, i, j = [], 0, 0
    while i < len(izq) and j < len(der):
        if clave(izq[i]) <= clave(der[j]):
            resultado.append(izq[i])
            i += 1
        else:
            resultado.append(der[j])
            j += 1
    return resultado + izq[i:] + der[j:]


def ordenar_por_fc(registros):
    ordenados = merge_sort(registros, lambda r: valor_numerico(r["fc"]))
    registrar_log("Registros ordenados por frecuencia cardiaca")
    return ordenados


# ------------------------------------------------------------ validación
def validar_registro(reg):
    """Devuelve la lista de errores del registro (vacía si es válido)."""
    errores = []
    for campo in CAMPOS:
        valor = reg.get(campo)
        if not isinstance(valor, str) or not PATRONES[campo].match(valor):
            errores.append(f"Campo '{campo}' inválido: {valor!r}")
    return errores


def validar_lista(registros):
    validos, invalidos = [], []
    for reg in registros:
        errores = validar_registro(reg)
        if errores:
            invalidos.append((reg, errores))
        else:
            validos.append(reg)
    registrar_log(f"Validación: {len(validos)} válidos, {len(invalidos)} inválidos")
    return validos, invalidos


# ------------------------------------------------------ TXT / CSV / JSON
def guardar_txt(registros, nombre="datos.txt"):
    crear_estructura()
    ruta = DIRS["txt"] / nombre
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            for r in registros:
                f.write(f"{r['id']},{r['fr']},{r['fc']},{r['spo2']}\n")
        registrar_log(f"Guardado TXT: {ruta.relative_to(BASE_DIR)}")
        return ruta
    except OSError as e:
        registrar_log(f"ERROR guardando TXT: {e}")
        print(f"Error al guardar TXT: {e}")


def guardar_csv(registros, nombre="datos.csv"):
    crear_estructura()
    ruta = DIRS["csv"] / nombre
    try:
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(registros)
        registrar_log(f"Guardado CSV: {ruta.relative_to(BASE_DIR)}")
        return ruta
    except OSError as e:
        registrar_log(f"ERROR guardando CSV: {e}")
        print(f"Error al guardar CSV: {e}")


def exportar_json(datos, nombre="datos.json"):
    crear_estructura()
    ruta = DIRS["json"] / nombre
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        registrar_log(f"Exportado JSON: {ruta.relative_to(BASE_DIR)}")
        return ruta
    except (OSError, TypeError) as e:
        registrar_log(f"ERROR exportando JSON: {e}")
        print(f"Error al exportar JSON: {e}")


def importar_json(nombre="datos.json"):
    ruta = DIRS["json"] / nombre
    if not ruta.exists():
        print(f"La ruta no existe: {ruta}")
        registrar_log(f"ERROR importando JSON: no existe {ruta}")
        return []
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        registrar_log(f"Importado JSON: {ruta.relative_to(BASE_DIR)} ({len(datos)} elementos)")
        return datos
    except (OSError, json.JSONDecodeError) as e:
        registrar_log(f"ERROR importando JSON: {e}")
        print(f"Error al importar JSON: {e}")
        return []


# --------------------------------------------------------------- MongoDB
def conectar_mongo():
    if MongoClient is None:
        print("pymongo no está instalado. Ejecute: pip install -r requirements.txt")
        return None
    if not MONGO_URI:
        print("Defina la variable de entorno MONGO_URI con su cadena de Atlas.")
        return None
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        cliente.admin.command("ping")
        registrar_log("Conexión a MongoDB Atlas exitosa")
        return cliente[DB_NAME][COLECCION]
    except PyMongoError as e:
        registrar_log(f"ERROR conectando a MongoDB: {e}")
        print(f"No se pudo conectar a MongoDB: {e}")
        return None


def insertar_en_mongo(coleccion, registros):
    """Inserta (upsert por id) solo registros validados."""
    validos, _ = validar_lista(registros)
    try:
        for r in validos:
            doc = dict(r)
            doc["fc_num"] = valor_numerico(r["fc"])
            doc["spo2_num"] = valor_numerico(r["spo2"])
            doc["fr_num"] = valor_numerico(r["fr"])
            coleccion.replace_one({"id": r["id"]}, doc, upsert=True)
        registrar_log(f"Insertados/actualizados {len(validos)} documentos en {COLECCION}")
        return len(validos)
    except PyMongoError as e:
        registrar_log(f"ERROR insertando en MongoDB: {e}")
        print(f"Error al insertar: {e}")
        return 0


def promedio_fc(coleccion):
    res = list(coleccion.aggregate([{"$group": {"_id": None, "promedio": {"$avg": "$fc_num"}}}]))
    return round(res[0]["promedio"], 2) if res else None


def spo2_bajo(coleccion, limite=94):
    return list(coleccion.find({"spo2_num": {"$lt": limite}}, {"_id": 0}))


def buscar_por_id(coleccion, id_):
    return coleccion.find_one({"id": id_}, {"_id": 0})


def ejecutar_consultas(coleccion):
    try:
        resultados = {
            "promedio_frecuencia_cardiaca": promedio_fc(coleccion),
            "spo2_menor_94": spo2_bajo(coleccion),
        }
    except PyMongoError as e:
        registrar_log(f"ERROR en consultas: {e}")
        print(f"Error en consultas: {e}")
        return None
    ruta = exportar_json(resultados, "resultados_mongo.json")
    registrar_log("Consultas ejecutadas y exportadas a resultados_mongo.json")
    print(f"Promedio FC: {resultados['promedio_frecuencia_cardiaca']} ppm")
    print(f"Documentos con SpO2 < 94: {len(resultados['spo2_menor_94'])}")
    print(f"Exportado en: {ruta}")
    return resultados


# ------------------------------------------------------------------ menú
def ingresar_manual(registros):
    print("\nIngrese los datos (formatos: ID-001, 18 Años, 090ppm, 95%)")
    reg = {
        "id": input("id: ").strip(),
        "fr": input("fr (edad): ").strip(),
        "fc": input("fc: ").strip(),
        "spo2": input("spo2: ").strip(),
    }
    errores = validar_registro(reg)
    if errores:
        print("Registro rechazado:")
        for e in errores:
            print(" -", e)
        registrar_log(f"Registro manual rechazado: {reg}")
    else:
        registros.append(reg)
        registros[:] = ordenar_por_fc(registros)
        print("Registro agregado.")
        registrar_log(f"Registro manual agregado: {reg['id']}")


def menu():
    crear_estructura()
    registros = []
    coleccion = None
    registrar_log("Programa iniciado")
    while True:
        print(f"""
===== SIGNOS VITALES ({len(registros)} registros en memoria) =====
1. Generar registros aleatorios (50) y ordenar por FC
2. Ingresar un registro manualmente
3. Guardar TXT y CSV
4. Exportar JSON
5. Importar JSON
6. Validar datos en memoria
7. Organizar archivos sueltos
8. Conectar a MongoDB e insertar registros
9. Ejecutar consultas (promedio FC, SpO2 < 94) y exportar
10. Consultar un registro por ID en MongoDB
0. Salir""")
        op = input("Opción: ").strip()

        if op == "1":
            registros = ordenar_por_fc(generar_registros(50))
            print("50 registros generados y ordenados por frecuencia cardiaca.")
        elif op == "2":
            ingresar_manual(registros)
        elif op == "3":
            if registros:
                print("TXT:", guardar_txt(registros))
                print("CSV:", guardar_csv(registros))
            else:
                print("No hay datos. Use la opción 1, 2 o 5.")
        elif op == "4":
            if registros:
                print("JSON:", exportar_json(registros))
            else:
                print("No hay datos para exportar.")
        elif op == "5":
            nombre = input("Nombre del archivo [datos.json]: ").strip() or "datos.json"
            datos = importar_json(nombre)
            if datos:
                registros = ordenar_por_fc(datos)
                print(f"{len(datos)} registros importados.")
        elif op == "6":
            validos, invalidos = validar_lista(registros)
            print(f"Válidos: {len(validos)} | Inválidos: {len(invalidos)}")
            for reg, errs in invalidos:
                print(reg.get("id"), errs)
        elif op == "7":
            print(f"Archivos movidos: {organizar_archivos()}")
        elif op == "8":
            coleccion = coleccion if coleccion is not None else conectar_mongo()
            if coleccion is not None and registros:
                print(f"Documentos insertados: {insertar_en_mongo(coleccion, registros)}")
            elif coleccion is not None:
                print("No hay registros en memoria para insertar.")
        elif op == "9":
            coleccion = coleccion if coleccion is not None else conectar_mongo()
            if coleccion is not None:
                ejecutar_consultas(coleccion)
        elif op == "10":
            coleccion = coleccion if coleccion is not None else conectar_mongo()
            if coleccion is not None:
                id_ = input("ID (ej. ID-001): ").strip()
                if not PATRONES["id"].match(id_):
                    print("Formato de ID inválido.")
                else:
                    try:
                        doc = buscar_por_id(coleccion, id_)
                        print(json.dumps(doc, indent=4, ensure_ascii=False) if doc else "No encontrado.")
                        registrar_log(f"Consulta por ID {id_}")
                    except PyMongoError as e:
                        print(f"Error de consulta: {e}")
        elif op == "0":
            registrar_log("Programa finalizado")
            print("Hasta luego.")
            break
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    menu()
