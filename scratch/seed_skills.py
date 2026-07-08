#!/usr/bin/env python3
"""Seed example Skills into the DB under the admin user 'hashira'."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db_connection import get_monitor_conn, release_conn

SKILLS = [
    {
        "name": "Umbrales de Rendimiento",
        "description": "Define los límites aceptables de CPU, memoria y disco para el entorno de producción.",
        "content": """# Propósito
Establece los umbrales de rendimiento aceptables para el monitor de salud de bases de datos en producción.

## Umbrales críticos
- **CPU**: advertencia a 75%, crítico a 90%
- **Memoria RAM**: advertencia a 80%, crítico a 95%
- **Disco**: advertencia a 70%, crítico a 85%
- **Conexiones activas**: advertencia a 70% del límite, crítico a 90%
- **Cache Hit Ratio**: advertencia si baja de 85%, crítico si baja de 70%

## Instrucciones de consulta
- Si el usuario pregunta por rendimiento, evalúa TODOS los umbrales anteriores.
- Indica siempre si el valor está en zona NORMAL, ADVERTENCIA o CRÍTICO.
- Cuando el CPU supere 75%, sugiere revisar consultas lentas (slow queries).
- Cuando la memoria supere 80%, sugiere incrementar el parámetro `shared_buffers`.

## Reglas de adaptación
- El servidor de producción principal tiene mayor prioridad en las alertas.
- Ignorar datasources marcados como inactivos.
- Las métricas de sistema operativo (CPU, RAM, disco) aplican al host donde corre la BD.
""",
    },
    {
        "name": "Protocolo de Alertas",
        "description": "Guía de respuesta ante alertas críticas del sistema de monitoreo.",
        "content": """# Propósito
Define el protocolo de actuación cuando el monitor detecta alertas de severidad WARNING o CRITICAL.

## Niveles de alerta
| Severidad | Color  | Acción inmediata                          |
|-----------|--------|-------------------------------------------|
| INFO      | Azul   | Registrar, no requiere intervención       |
| WARNING   | Amarillo | Monitorear con mayor frecuencia (5 min) |
| CRITICAL  | Rojo   | Escalar al DBA de guardia inmediatamente  |

## Protocolo ante alerta CRITICAL
1. Verificar si la base de datos responde con `SELECT 1`.
2. Revisar el log de errores del motor de BD.
3. Comprobar espacio en disco antes de reiniciar servicios.
4. Notificar al responsable del sistema antes de cualquier intervención.
5. Documentar la alerta y la acción tomada en el historial.

## Instrucciones de consulta
- Cuando el usuario pregunte por alertas, mostrar las más recientes primero.
- Distinguir siempre entre alertas activas y resueltas.
- Si hay más de 3 alertas CRITICAL activas, indicar que se requiere atención urgente.

## Escalamiento
- DBA de guardia: revisar `alertas` en el dashboard antes de actuar.
- No reiniciar servicios de BD sin antes verificar conexiones activas.
""",
    },
    {
        "name": "Guía de Conexiones PostgreSQL",
        "description": "Referencia de parámetros y buenas prácticas de conexiones para PostgreSQL.",
        "content": """# Propósito
Documentar las buenas prácticas de gestión de conexiones para las instancias PostgreSQL monitoreadas.

## Parámetros clave de PostgreSQL
- `max_connections`: número máximo de conexiones simultáneas (por defecto: 100).
- `shared_buffers`: memoria para caché de páginas (recomendado: 25% de RAM total).
- `work_mem`: memoria por operación de ordenamiento (cuidar con muchas conexiones).
- `idle_in_transaction_session_timeout`: cierra conexiones inactivas en transacción (recomendado: 30s).

## Señales de problemas de conexión
- **Connection pct > 70%**: agregar pgBouncer (pool de conexiones).
- **Threads waiting alto**: revisar locks y transacciones largas.
- **Cache hit ratio < 85%**: aumentar `shared_buffers` o `effective_cache_size`.

## Instrucciones de consulta
- Si se pregunta por conexiones, mostrar: activas, esperando y el porcentaje del límite.
- Si el uso supera el 80%, recomendar implementar pgBouncer como connection pooler.
- El parámetro `max_connections` de PostgreSQL se obtiene del datasource activo.

## Comandos de diagnóstico útiles
```sql
-- Ver conexiones activas por estado
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;

-- Ver consultas lentas (> 5 segundos)
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds';
```
""",
    },
    {
        "name": "Contexto del Proyecto",
        "description": "Información general del sistema Monitor de Salud de Bases de Datos.",
        "content": """# Propósito
Proveer contexto general del proyecto DB Health Monitor para orientar respuestas del asistente.

## Descripción del sistema
**DB Health Monitor** es un sistema de monitoreo centralizado desarrollado con Flask + PostgreSQL.
Permite monitorear múltiples bases de datos heterogéneas en tiempo real desde un único dashboard.

## Motores soportados
- PostgreSQL
- MySQL / MariaDB
- SQL Server
- MongoDB

## Métricas monitoreadas
- CPU y memoria del servidor host (via psutil)
- Conexiones activas vs límite máximo
- Cache Hit Ratio del motor de BD
- Espacio en disco utilizado y libre
- Consultas lentas (slow queries) en MySQL/MariaDB
- Historial de métricas capturadas automáticamente

## Usuarios del sistema
- **admin**: acceso total, gestión de usuarios y datasources globales.
- **viewer**: acceso de solo lectura, gestiona sus propias fuentes de datos.

## Instrucciones de consulta
- Al responder sobre "el sistema", referirse a este proyecto específico.
- Los datos se actualizan cada 10 segundos mediante el `background_collector`.
- El monitor propio corre sobre PostgreSQL en la VM de producción (38.250.116.71).
- Cada usuario solo ve sus propios datasources (aislamiento por user_id).
""",
    },
]

def main():
    conn = get_monitor_conn()
    try:
        with conn.cursor() as cur:
            # Get admin user id
            cur.execute("SELECT id FROM auth_users WHERE username = 'hashira' LIMIT 1")
            row = cur.fetchone()
            if not row:
                print("ERROR: usuario 'hashira' no encontrado. Inicia sesión una vez primero.")
                return
            user_id = row[0]
            print(f"Admin user id: {user_id}")

            for skill in SKILLS:
                # Check if already exists
                cur.execute(
                    "SELECT id FROM skill_files WHERE name = %s AND user_id = %s",
                    (skill["name"], user_id)
                )
                if cur.fetchone():
                    print(f"  [Skipped] Ya existe: {skill['name']}")
                    continue
                cur.execute(
                    """INSERT INTO skill_files (user_id, name, description, content, active)
                       VALUES (%s, %s, %s, %s, TRUE)""",
                    (user_id, skill["name"], skill["description"], skill["content"])
                )
                print(f"  [Created] Creada: {skill['name']}")

            conn.commit()
            print("\nSkills insertadas correctamente.")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        release_conn(conn)

if __name__ == "__main__":
    main()
