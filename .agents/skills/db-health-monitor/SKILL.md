---
name: db-health-monitor
description: Habilidad para interactuar con el Monitor de Salud DB de forma local mediante CLI o de forma remota a través de la API REST. Permite listar bases de datos, consultar métricas en tiempo real, obtener historiales, listar logs y leer archivos de configuración de bases de datos.
---

# Habilidad del Monitor de Salud DB

Esta habilidad permite a los agentes de IA (como Codex, Antigravity, etc.) diagnosticar y consultar el estado de las bases de datos registradas en este repositorio de forma local y remota.

---

## 1. Interfaz CLI Local (Recomendado)

La extensión incluye un script de ayuda en Python que ejecuta directamente la lógica de conexión y consultas a las bases de datos de forma local y sin necesidad de levantar el servidor Flask.

**Uso**:
```bash
python vscode/helper.py <comando> [argumentos]
```

> [!NOTE]
> Debes ejecutar este script con la variable de entorno `WORKSPACE_ROOT` configurada a la ruta absoluta de la raíz del proyecto para que lea el archivo `config.ini` correspondiente.

### Comandos del CLI:

*   **Listar Fuentes de Datos (`get_datasources`)**:
    Retorna la lista de todas las bases de datos configuradas en la base de datos principal y sus estados de salud.
    ```bash
    python vscode/helper.py get_datasources
    ```
    *Retorno (JSON)*: `[{"id": 1, "nombre": "DB Producción", "tipo_db": "postgresql", "host": "127.0.0.1", "status": "OK", "activa": true}, ...]`

*   **Obtener Métricas en Tiempo Real (`get_metrics <ds_id>`)**:
    Se conecta a la base de datos con ID `<ds_id>` en tiempo real y ejecuta las queries recolectoras de salud correspondientes al tipo de motor.
    ```bash
    python vscode/helper.py get_metrics 1
    ```
    *Retorno (JSON)*: Contiene las métricas recolectadas: `threads_connected`, `connection_pct`, `cache_hit_ratio`, `db_size_mb`, `cpu_pct`, `mem_pct`, `status` ("OK", "WARNING", "CRITICAL"), etc.

*   **Listar Archivos Registrados (`get_files <ds_id>`)**:
    Retorna el inventario de archivos de logs y configuración asociados al datasource según las rutas configuradas.
    ```bash
    python vscode/helper.py get_files 1
    ```

*   **Leer un Archivo (`read_file <ds_id> <ruta_absoluta>`)**:
    Lee de forma segura el contenido del archivo si pertenece al inventario permitido de la base de datos (límite de 2 MB).
    ```bash
    python vscode/helper.py read_file 1 "/var/log/postgresql/postgresql-15-main.log"
    ```

*   **Obtener Historial de Métricas (`get_history <ds_id>`)**:
    Obtiene las últimas 50 capturas de rendimiento del pool histórico guardadas en la tabla `health_snapshots`.
    ```bash
    python vscode/helper.py get_history 1
    ```

*   **Obtener Alertas (`get_alerts [ds_id]`)**:
    Retorna la lista de alertas recientes en el log de alertas de la base de datos indicada o de todas de forma global si se omite el ID.
    ```bash
    python vscode/helper.py get_alerts 1
    ```

---

## 2. Interfaz API REST Remota (Flask)

Si el servidor Flask del sistema (`server.py`) está ejecutándose, puedes consultar la API utilizando peticiones HTTP tradicionales con el Bearer Token asignado.

*   **Base URL**: `http://38.250.116.71:5000`
*   **API Key**: `dhm_6rBV1HQcfhwb7JAuiECUBTqt-LRf9R1emYy3kraODB4`
*   **Cabecera de Autenticación**: `Authorization: Bearer dhm_6rBV1HQcfhwb7JAuiECUBTqt-LRf9R1emYy3kraODB4`

### Endpoints Disponibles:

*   `GET /api/datasources`: Obtiene la lista de fuentes de datos.
*   `GET /api/metrics?datasource_id=<id>`: Obtiene métricas en vivo.
*   `GET /api/files?datasource_id=<id>`: Retorna el inventario de logs/config.
*   `GET /api/files/read?datasource_id=<id>&path=<ruta>`: Lee el archivo remoto.
*   `GET /api/alerts?datasource_id=<id>`: Registros de alertas recientes.
*   `GET /api/history?datasource_id=<id>`: Snapshots de histórico.

---

## 3. Ejemplo de Script en Python para Agentes

El siguiente ejemplo muestra cómo un agente de IA puede automatizar la consulta de métricas de base de datos desde Python usando la interfaz CLI local:

```python
import subprocess
import json
import os

# Configurar el entorno con la ruta del proyecto actual
env = os.environ.copy()
env["WORKSPACE_ROOT"] = os.getcwd()

# Ejecutar comando para obtener bases de datos
proc = subprocess.run(
    ["python", "vscode/helper.py", "get_datasources"],
    capture_output=True, text=True, env=env
)

if proc.returncode == 0:
    dbs = json.loads(proc.stdout)
    print(f"Bases de datos encontradas: {len(dbs)}")
    for db in dbs:
        print(f" - ID: {db['id']} | {db['nombre']} ({db['tipo_db']}) | Estado: {db['status']}")
else:
    print("Error consultando el helper local:", proc.stderr)
```
