<center>

<img src="../media/logo-upt.png" alt="Logo UPT" style="width:1.088in;height:1.46256in;" />

**UNIVERSIDAD PRIVADA DE TACNA**

**FACULTAD DE INGENIERIA**

**Escuela Profesional de Ingeniería de Sistemas**

**Proyecto *Monitor de Salud de Bases de Datos (DB Health Monitor)***

Curso: *Base de Datos II*

Docente: *Mag. Patrick Cuadros Quiroga*

Integrantes:

***Vargas Candia, Hashira Belén (2022075480)***
***Espinoza Castañeda, Ariana Byanca (2022073904)***

**Tacna – Perú**

***2026***

**  
**
</center>
<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

|CONTROL DE VERSIONES||||||
| :-: | :- | :- | :- | :- | :- |
|Versión|Hecha por|Revisada por|Aprobada por|Fecha|Motivo|
|1.0|HVC|AEC|PCQ|04/07/2026|Versión inicial del documento de especificación de requerimientos|

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

# **INTRODUCCIÓN**

El presente documento de especificación de requerimientos describe el alcance, el comportamiento esperado y las restricciones del sistema **DB Health Monitor**, una solución web orientada al monitoreo de salud de múltiples motores de bases de datos y del servidor anfitrión. El documento se construyó a partir del repositorio real del proyecto, la interfaz web, los módulos Python, el esquema de base de datos y la configuración del sistema.

Su finalidad es servir como base de análisis funcional y técnica para el desarrollo realizado durante el semestre 2026-I en el curso Base de Datos II.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

# **I. Generalidades de la Empresa**

## 1. Nombre de la Empresa

La organización de referencia es la **Universidad Privada de Tacna**, a través de la **Escuela Profesional de Ingeniería de Sistemas**. El proyecto se desarrolla como una iniciativa académica orientada al aprendizaje aplicado en administración de bases de datos, desarrollo web y monitoreo de infraestructura.

## 2. Visión

Formar ingenieros de sistemas capaces de diseñar y desarrollar soluciones tecnológicas robustas, seguras y útiles para resolver problemas reales con impacto académico y profesional.

## 3. Misión

Brindar formación integral en ingeniería de sistemas mediante proyectos aplicados que integren teoría, práctica, innovación y uso de tecnologías abiertas.

## 4. Organigrama

```mermaid
graph TD
    UPT[Universidad Privada de Tacna] --> FI[Facultad de Ingeniería]
    FI --> EPIS[Escuela Profesional de Ingeniería de Sistemas]
    EPIS --> BD2[Curso Base de Datos II]
    BD2 --> DOC[Docente: Mag. Patrick Cuadros Quiroga]
    BD2 --> EQ[Equipo de desarrollo]
    EQ --> H[Vargas Candia, Hashira Belén]
    EQ --> A[Espinoza Castañeda, Ariana Byanca]
```

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

# **II. Visionamiento de la Empresa**

## 1. Descripción del Problema

La necesidad principal consiste en supervisar de manera centralizada múltiples motores de bases de datos y el servidor anfitrión, evitando la dispersión de información entre herramientas diferentes. La supervisión manual retrasa la detección de saturación de conexiones, degradación de rendimiento, consumo de recursos y revisión de archivos relevantes del motor.

## 2. Objetivos de Negocios

- Reducir el esfuerzo manual de monitoreo.
- Centralizar métricas y alertas en una única interfaz.
- Mejorar la trazabilidad histórica del comportamiento de las bases de datos.
- Incrementar la capacidad de reacción ante incidentes.
- Fortalecer el valor académico del proyecto.

## 3. Objetivos de Diseño

- Construir una aplicación web ligera y modular.
- Utilizar Flask como base del backend.
- Implementar autenticación por roles.
- Permitir consultas diferenciadas por usuario.
- Mantener compatibilidad con PostgreSQL, MySQL, MariaDB, SQL Server y MongoDB.

## 4. Alcance del Proyecto

El proyecto contempla autenticación, gestión de datasources, recolección automática de métricas, historial, alertas, inventario de archivos, panel de administración y exportación a CSV. No incluye mensajería externa, ejecución de consultas ad hoc ni modificación remota de configuración del motor.

## 5. Viabilidad del Sistema

La viabilidad es alta porque la solución está construida con tecnologías abiertas y maduras, requiere infraestructura modesta, separa claramente la lógica de aplicación y permite el monitoreo de fuentes heterogéneas sin licencias comerciales.

## 6. Información obtenida del Levantamiento de Información

Del análisis del repositorio se obtuvo que el sistema:

- usa roles `admin`, `user` y `viewer`;
- almacena métricas de conexiones, cache hit ratio, CPU, memoria y estado;
- genera alertas por umbrales;
- conserva snapshots históricos;
- administra datasources por usuario;
- consulta archivos de configuración, datos, logs y backups.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

# **III. Análisis de Procesos**

## a) Diagrama del Proceso Actual – Diagrama de actividades

```mermaid
flowchart TD
    A[Inicio] --> B[Revisión manual de cada motor]
    B --> C[Consulta de logs y métricas por separado]
    C --> D[Registro manual de hallazgos]
    D --> E[Generación manual de reportes]
    E --> F[Fin]
```

## b) Diagrama del Proceso Propuesto – Diagrama de actividades inicial

```mermaid
flowchart TD
    A[Inicio] --> B[Usuario inicia sesión]
    B --> C[Selecciona datasource]
    C --> D[El sistema valida la conexión]
    D --> E[Collector obtiene métricas]
    E --> F[Se guardan snapshots y alertas]
    F --> G[Dashboard muestra KPIs e historial]
    G --> H[Consulta de archivos y exportación CSV]
    H --> I[Fin]
```

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

# **IV. Especificación de Requerimientos de Software**

## a) Cuadro de Requerimientos Funcionales Inicial

| ID | Requerimiento | Descripción |
|---|---|---|
| RF-01 | Autenticación | Permitir registro, inicio y cierre de sesión. |
| RF-02 | Gestión de roles | Diferenciar admin, user y viewer. |
| RF-03 | Registro de datasources | Crear fuentes de datos con parámetros de conexión. |
| RF-04 | Prueba de conexión | Verificar conectividad a cada datasource. |
| RF-05 | Recolección automática | Obtener métricas de forma periódica. |
| RF-06 | Historial | Consultar snapshots históricos. |
| RF-07 | Alertas | Generar y consultar alertas por umbral. |
| RF-08 | Archivos | Mostrar archivos de configuración, datos, logs y backups. |
| RF-09 | Administración | Visualizar usuarios y fuentes para el rol admin. |
| RF-10 | CSV | Exportar información relevante. |

## b) Cuadro de Requerimientos No Funcionales

| ID | Requerimiento | Descripción |
|---|---|---|
| RNF-01 | Rendimiento | Respuesta ágil del dashboard y de los endpoints. |
| RNF-02 | Disponibilidad | Operación continua durante el semestre 2026-I. |
| RNF-03 | Seguridad | Hashing de contraseñas y control por sesión. |
| RNF-04 | Usabilidad | Interfaz clara para usuarios con conocimientos básicos. |
| RNF-05 | Portabilidad | Ejecución en Linux y navegadores modernos. |
| RNF-06 | Mantenibilidad | Código modular y configuración externa. |
| RNF-07 | Compatibilidad | Soporte para motores PostgreSQL, MySQL, MariaDB, SQL Server y MongoDB. |
| RNF-08 | Escalabilidad | Posibilidad de agregar más datasources sin rediseño completo. |

## c) Cuadro de Requerimientos Funcionales Final

| ID | Requerimiento | Prioridad | Estado |
|---|---|---|---|
| RF-01 | Autenticación | Alta | Implementado |
| RF-02 | Gestión de roles | Alta | Implementado |
| RF-03 | Registro de datasources | Alta | Implementado |
| RF-04 | Prueba de conexión | Alta | Implementado |
| RF-05 | Recolección automática | Crítica | Implementado |
| RF-06 | Historial | Alta | Implementado |
| RF-07 | Alertas | Alta | Implementado |
| RF-08 | Archivos | Media | Implementado |
| RF-09 | Administración | Media | Implementado |
| RF-10 | CSV | Media | Implementado |

## d) Reglas de Negocio

| ID | Regla de Negocio | Descripción |
|---|---|---|
| RN-01 | Acceso autenticado | Ningún usuario puede ingresar sin iniciar sesión. |
| RN-02 | Aislamiento por propietario | Cada usuario visualiza solo sus datasources, salvo admin. |
| RN-03 | Datasource activo | Solo las fuentes activas se monitorean automáticamente. |
| RN-04 | Evaluación de umbrales | El sistema genera alertas si se exceden o caen los valores configurados. |
| RN-05 | Contraseñas seguras | Las credenciales de usuario se almacenan con hash seguro. |
| RN-06 | Visibilidad global del admin | El administrador tiene acceso a usuarios y fuentes de todo el sistema. |
| RN-07 | Inventario por tipo de BD | Los archivos mostrados dependen del tipo de datasource. |

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

# **V. Fase de Desarrollo**

## 1. Perfiles de Usuario

| Perfil | Descripción | Responsabilidades |
|---|---|---|
| Administrador | Usuario con visibilidad completa del sistema. | Gestionar usuarios, datasources, alertas y estado global. |
| Usuario estándar | Usuario que administra sus propias fuentes de datos. | Registrar datasources, monitorear métricas y revisar alertas. |
| Visor | Usuario de solo lectura. | Consultar métricas, alertas e historial. |

## 2. Modelo Conceptual

### Diagrama de Paquetes

```mermaid
graph TD
    subgraph Presentacion
        UI[templates/index.html]
        JS[static/dashboard.js]
        CSS[static/style.css]
    end

    subgraph Aplicacion
        APP[server.py]
        AUTH[Autenticación]
        API[API REST]
        COL[Collector]
    end

    subgraph Integracion
        CONN[db_connection.py]
        CFG[config.ini]
    end

    subgraph Persistencia
        DB[(PostgreSQL del monitor)]
        DS[(Datasources externos)]
    end

    UI --> JS
    JS --> API
    CSS --> UI
    APP --> AUTH
    APP --> API
    APP --> COL
    APP --> CONN
    CONN --> CFG
    CONN --> DB
    COL --> DS
```

### Diagrama de Casos de Uso

```mermaid
flowchart LR
    Admin[Administrador]
    User[Usuario]
    Viewer[Visor]

    UC1[Iniciar sesión]
    UC2[Registrar datasource]
    UC3[Probar conexión]
    UC4[Consultar métricas]
    UC5[Consultar alertas]
    UC6[Consultar archivos]
    UC7[Administrar usuarios]

    Admin --> UC1
    Admin --> UC2
    Admin --> UC3
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7

    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC6

    Viewer --> UC1
    Viewer --> UC4
    Viewer --> UC5
    Viewer --> UC6
```

### Escenarios de Caso de Uso (narrativa) — CU-1 a CU-7

**CU-1 Iniciar sesión**

| Campo | Descripción |
|---|---|
| Actor principal | Usuario |
| Propósito | Autenticarse para acceder al sistema. |
| Flujo principal | 1. El usuario ingresa credenciales. 2. El sistema valida usuario y contraseña. 3. El sistema crea la sesión. 4. Se muestra el dashboard. |
| Flujo alterno | Si las credenciales son inválidas, el sistema rechaza el acceso. |

**CU-2 Registrar datasource**

| Campo | Descripción |
|---|---|
| Actor principal | Usuario / Administrador |
| Propósito | Crear una nueva fuente de datos. |
| Flujo principal | 1. El usuario completa nombre, tipo, host, puerto, usuario y base. 2. El sistema valida los datos. 3. Se almacena el datasource. |
| Flujo alterno | Si faltan campos, el sistema informa el error. |

**CU-3 Probar conexión**

| Campo | Descripción |
|---|---|
| Actor principal | Usuario / Administrador |
| Propósito | Verificar que la fuente de datos sea accesible. |
| Flujo principal | 1. El usuario selecciona Probar. 2. El sistema conecta al datasource. 3. El sistema devuelve latencia y estado. |
| Flujo alterno | Si falla la conexión, el sistema retorna el mensaje de error. |

**CU-4 Consultar métricas**

| Campo | Descripción |
|---|---|
| Actor principal | Todos los roles autenticados |
| Propósito | Revisar indicadores actuales. |
| Flujo principal | 1. El usuario abre el dashboard. 2. El sistema entrega el último snapshot o métricas en caché. 3. Se muestran KPIs y gráficos. |

**CU-5 Consultar alertas**

| Campo | Descripción |
|---|---|
| Actor principal | Usuario / Administrador / Visor |
| Propósito | Ver alertas recientes o históricas. |
| Flujo principal | 1. El usuario abre la sección de alertas. 2. El sistema consulta `alert_log`. 3. Se muestran severidad, métrica y mensaje. |

**CU-6 Consultar archivos**

| Campo | Descripción |
|---|---|
| Actor principal | Usuario / Administrador / Visor |
| Propósito | Revisar archivos de configuración, datos, logs y backups. |
| Flujo principal | 1. El usuario selecciona un datasource. 2. El sistema identifica rutas por tipo de BD. 3. El sistema muestra existencia, tamaño y fecha. |

**CU-7 Administrar usuarios**

| Campo | Descripción |
|---|---|
| Actor principal | Administrador |
| Propósito | Supervisar cuentas y fuentes globales. |
| Flujo principal | 1. El administrador accede al panel de administración. 2. El sistema muestra usuarios y datasources. 3. El administrador revisa la información. |

### Diagrama de Secuencia (vista de diseño)

```mermaid
sequenceDiagram
    actor Usuario
    participant UI as Navegador
    participant App as Flask
    participant Conn as db_connection.py
    participant DB as PostgreSQL monitor
    participant Src as Datasource

    Usuario->>UI: Ingresa credenciales
    UI->>App: POST /api/login
    App->>DB: Validar usuario
    DB-->>App: Usuario y rol
    App-->>UI: Sesión activa
    Usuario->>UI: Solicita métricas
    UI->>App: GET /api/metrics
    App->>DB: Consultar caché y snapshots
    DB-->>App: Datos históricos
    App-->>UI: JSON con métricas
    Usuario->>UI: Probar datasource
    UI->>App: POST /api/datasources/{id}/test
    App->>Conn: test_datasource(ds)
    Conn->>Src: Ping / SELECT 1
    Src-->>Conn: Respuesta
    Conn-->>App: Resultado
    App-->>UI: Estado y latencia
```

### Diagrama de Colaboración (vista de diseño)

```mermaid
flowchart LR
    A[Usuario] --> B[Navegador]
    B --> C[Flask / server.py]
    C --> D[db_connection.py]
    D --> E[PostgreSQL del monitor]
    D --> F[Datasource externo]
    C --> G[Collector en hilo de fondo]
    G --> F
```

### Diagrama de Objetos

```mermaid
flowchart TB
    U[usuario: auth_users\nusername=hashira\nrole=admin]
    DS[datasource: datasources\nnombre=Monitor Principal\ntipo_db=postgresql]
    SP[snapshot: health_snapshots\nconnection_pct=18.4\nstatus=OK]
    AL[alerta: alert_log\nseverity=INFO\nmetric_name=CPU %]
    FI[archivo: inventario\npath=/etc/postgresql/15/main/postgresql.conf]

    U --> DS
    DS --> SP
    DS --> AL
    DS --> FI
```

### Diagrama de Clases

```mermaid
classDiagram
    class AppController {
        +index()
        +api_login()
        +api_logout()
        +api_metrics()
        +api_history()
        +api_alerts_history()
    }

    class AuthService {
        +authenticate_user()
        +seed_default_user()
        +is_admin()
        +is_logged_in()
    }

    class DatasourceService {
        +api_ds_list()
        +api_ds_create()
        +api_ds_update()
        +api_ds_delete()
        +api_ds_test()
    }

    class CollectorService {
        +background_collector()
        +collect_pg_metrics()
        +collect_mysql_metrics()
        +collect_mariadb_metrics()
        +collect_sqlserver_metrics()
        +collect_mongodb_metrics()
    }

    class AlertService {
        +evaluate_alerts()
        +save_alerts()
    }

    class InventoryService {
        +build_file_inventory()
        +get_file_profile_defs()
    }

    class DbConnectionService {
        +get_pool()
        +get_monitor_conn()
        +release_conn()
        +connect_to_datasource()
        +test_datasource()
    }

    AppController --> AuthService
    AppController --> DatasourceService
    AppController --> CollectorService
    AppController --> AlertService
    AppController --> InventoryService
    AppController --> DbConnectionService
```

## 3. Modelo Lógico

### Análisis de Objetos

| Objeto | Descripción |
|---|---|
| Usuario | Persona autenticada con rol admin, user o viewer. |
| Datasource | Fuente de datos registrada para monitoreo. |
| Snapshot | Captura histórica de métricas del datasource. |
| Alerta | Evento generado por umbral superado o incumplido. |
| Archivo | Ruta asociada a configuración, datos, logs o backup. |

### Diagrama de Actividades con Objetos

```mermaid
flowchart TD
    U[Usuario] --> L[Inicia sesión]
    L --> D[Selecciona datasource]
    D --> C[Collector obtiene métricas]
    C --> S[Se crea snapshot]
    S --> A{¿Hay alerta?}
    A -->|Sí| AL[Registrar alerta]
    A -->|No| V[Actualizar dashboard]
    AL --> V
    V --> F[Consultar archivos]
```

### c. Diagrama de Secuencia

```mermaid
sequenceDiagram
    actor Usuario
    participant Web as Frontend
    participant API as Flask API
    participant DB as PostgreSQL
    participant Mon as Motor monitoreado

    Usuario->>Web: Solicita dashboard
    Web->>API: GET /api/datasources
    API->>DB: Buscar datasources del usuario
    DB-->>API: Lista de fuentes
    API-->>Web: JSON
    Usuario->>Web: Solicita historial
    Web->>API: GET /api/history?datasource_id=1
    API->>DB: Consultar snapshots
    DB-->>API: Historial
    API-->>Web: JSON
    Usuario->>Web: Probar conexión
    Web->>API: POST /api/datasources/1/test
    API->>Mon: Conectar y validar
    Mon-->>API: Estado
    API-->>Web: Respuesta de prueba
```

### d. Diagrama de Clases

```mermaid
classDiagram
    class AuthUser {
        +id
        +username
        +password_hash
        +role
        +active
        +created_at
        +last_login
    }

    class Datasource {
        +id
        +nombre
        +tipo_db
        +host
        +puerto
        +usuario
        +password
        +database
        +activa
        +owner_username
    }

    class HealthSnapshot {
        +id
        +datasource_id
        +captured_at
        +max_connections
        +threads_connected
        +threads_running
        +connection_pct
        +qps
        +slow_queries
        +cache_hit_ratio
        +db_size_mb
        +cpu_pct
        +mem_pct
        +status
    }

    class AlertLog {
        +id
        +datasource_id
        +alerted_at
        +severity
        +metric_name
        +metric_value
        +threshold
        +message
    }

    AuthUser "1" --> "many" Datasource
    Datasource "1" --> "many" HealthSnapshot
    Datasource "1" --> "many" AlertLog
```

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

# **Conclusiones**

DB Health Monitor queda formalmente especificado como una solución académica de monitoreo centralizado de bases de datos, con una arquitectura clara, un modelo lógico definido y una interfaz web adecuada para supervisión y análisis histórico.

# **Recomendaciones**

- Mantener el código y la documentación sincronizados ante cualquier cambio funcional.
- Incorporar futuras mejoras de seguridad para credenciales de datasource.
- Validar los diagramas y la narrativa con el docente antes de la entrega final.

# **Bibliografía**

1. Documentación oficial de Flask. https://flask.palletsprojects.com/
2. Documentación oficial de PostgreSQL. https://www.postgresql.org/docs/
3. Documentación de psutil. https://psutil.readthedocs.io/
4. Documentación de Chart.js. https://www.chartjs.org/docs/
5. IEEE Std 830-1998. *Software Requirements Specifications*.

# **Webgrafía**

1. README.md del proyecto.
2. `server.py` del proyecto.
3. `db_connection.py` del proyecto.
4. `config.ini` del proyecto.
5. `migrations/init.sql` del proyecto.
