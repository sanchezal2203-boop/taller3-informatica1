# Taller 3 – Informática 1 (Unidad 3 y 4)

Gestión de datos biomédicos (signos vitales) con Python, archivos TXT/CSV/JSON,
expresiones regulares y MongoDB Atlas.

## Estructura

```
main.py            # programa con menú
requirements.txt   # dependencias (pymongo)
data/txt|csv|json  # se crean automáticamente
log.txt            # registro de acciones
```

## Formato de los registros

| Campo | Significado | Ejemplo |
|-------|-------------|---------|
| `id`  | Identificación | `ID-001` |
| `fr`  | Edad | `18 Años` |
| `fc`  | Frecuencia cardiaca | `090ppm` |
| `spo2`| Saturación de oxígeno | `95%` |

Cada campo se valida con una expresión regular antes de aceptarse o insertarse en MongoDB.

## Uso

```bash
pip install -r requirements.txt
export MONGO_URI="mongodb+srv://usuario:clave@cluster.mongodb.net/"   # Windows: set MONGO_URI=...
python main.py
```

> No suba su cadena de conexión al repositorio; se lee desde la variable de entorno `MONGO_URI`.
> En Atlas, agregue su IP en *Network Access*.

## Menú

1. Generar 50 registros aleatorios y ordenarlos por FC (merge sort propio)
2. Ingresar un registro manual (validado con regex)
3. Guardar TXT y CSV
4. Exportar JSON
5. Importar JSON
6. Validar datos
7. Organizar archivos sueltos en `data/`
8. Conectar a MongoDB e insertar en la colección `signos_vitales`
9. Consultas: promedio de FC y SpO2 < 94 → `data/json/resultados_mongo.json`
10. Consultar un registro por ID

## MongoDB

- Base de datos: `biomedico`, colección: `signos_vitales`.
- Además de los textos originales se guardan `fc_num`, `spo2_num` y `fr_num` (numéricos) para poder promediar y comparar.
- La inserción usa *upsert* por `id`, así no se duplican documentos.
