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
|1\.0|HVC|AEC|PCQ|01/06/2026|Versión Original|
|1\.1|AEC|HVC|PCQ|04/07/2026|Revisión de contenido y diagramas|




**Sistema *DB Health Monitor***

**Documento de Visión**

**Versión *1.1***

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

|CONTROL DE VERSIONES||||||
| :-: | :- | :- | :- | :- | :- |
|Versión|Hecha por|Revisada por|Aprobada por|Fecha|Motivo|
|1\.0|HVC|AEC|PCQ|01/06/2026|Versión Original|
|1\.1|AEC|HVC|PCQ|04/07/2026|Revisión de contenido y diagramas|


<div style="page-break-after: always; visibility: hidden">\pagebreak</div>


**INDICE GENERAL**
#
[1.	Introducción](#_Toc52661346)

1.1	Propósito

1.2	Alcance

1.3	Definiciones, Siglas y Abreviaturas

1.4	Referencias

1.5	Visión General

[2.	Posicionamiento](#_Toc52661347)

2.1	Oportunidad de negocio

2.2	Definición del problema

[3.	Descripción de los interesados y usuarios](#_Toc52661348)

3.1	Resumen de los interesados

3.2	Resumen de los usuarios

3.3	Entorno de usuario

3.4	Perfiles de los interesados

3.5	Perfiles de los Usuarios

3.6	Necesidades de los interesados y usuarios

[4.	Vista General del Producto](#_Toc52661349)

4.1	Perspectiva del producto

4.2	Resumen de capacidades

4.3	Suposiciones y dependencias

4.4	Costos y precios

4.5	Licenciamiento e instalación

[5.	Características del producto](#_Toc52661350)

[6.	Restricciones](#_Toc52661351)

[7.	Rangos de calidad](#_Toc52661352)

[8.	Precedencia y Prioridad](#_Toc52661353)

[9.	Otros requerimientos del producto](#_Toc52661354)

b) Estandares legales

c) Estandares de comunicación	](#_toc394513800)37

d) Estandaraes de cumplimiento de la plataforma	](#_toc394513800)42

e) Estandaraes de calidad y seguridad	](#_toc394513800)42

[CONCLUSIONES](#_Toc52661355)

[RECOMENDACIONES](#_Toc52661356)

[BIBLIOGRAFIA](#_Toc52661357)

[WEBGRAFIA](#_Toc52661358)


<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

**<u>Informe de Visión</u>**

1. <span id="_Toc52661346" class="anchor"></span>**Introducción**

    1.1	Propósito

    El propósito de este documento es definir, a alto nivel, los requerimientos funcionales y no funcionales del sistema **DB Health Monitor**. Se busca recopilar, analizar y documentar las necesidades de los interesados y usuarios finales para establecer una visión compartida del producto. Este documento sirve como acuerdo base entre el equipo de desarrollo y los interesados del proyecto, proporcionando una descripción general de las características y restricciones del sistema de monitoreo de salud de bases de datos.

    El presente Informe de Visión está dirigido al docente del curso de Base de Datos II, a los integrantes del equipo de desarrollo y a cualquier profesional de TI o administrador de bases de datos que necesite comprender el alcance, los objetivos y las funcionalidades previstas del sistema.

    1.2	Alcance

    El sistema **DB Health Monitor** es una aplicación web desarrollada en Python con el framework Flask, cuyo propósito principal es monitorizar en tiempo real el estado de salud de múltiples motores de bases de datos (PostgreSQL, MySQL, MariaDB, SQL Server y MongoDB) así como las métricas del servidor anfitrión (CPU, memoria, disco).

    El alcance del producto comprende:

    - **Recolección automática de métricas**: Un hilo de fondo recolecta periódicamente (cada 10 segundos, configurable) métricas de rendimiento de cada fuente de datos registrada, incluyendo conexiones activas, cache hit ratio, consultas lentas, tamaño de la base de datos, uso de CPU, memoria y disco.
    - **Almacenamiento de snapshots históricos**: Las métricas capturadas se persisten en una base de datos PostgreSQL centralizada (tabla `health_snapshots`) para consulta histórica y análisis de tendencias.
    - **Sistema de alertas configurables**: Evaluación automática de umbrales (warning y critical) para conexiones, cache hit ratio, CPU y memoria, con registro de alertas en la tabla `alert_log`.
    - **Dashboard web interactivo**: Interfaz web con visualización de KPIs en tiempo real, gráficos históricos (Chart.js), gestión de fuentes de datos y exportación a CSV.
    - **Gestión multi-datasource**: Capacidad de registrar, editar, eliminar y probar conexiones a múltiples motores de bases de datos desde la interfaz web.
    - **Sistema de autenticación y autorización**: Roles de usuario (admin/viewer/user) con aislamiento de datos por propietario de datasource.
    - **Inventario de archivos de BD**: Inspección remota de archivos de configuración, datos, logs y respaldos de cada motor de base de datos monitoreado.

    El sistema **no** contempla en esta versión: modificación remota de la configuración de los motores de BD, ejecución de queries ad hoc, ni integración con herramientas de notificación externas (correo electrónico, Slack, etc.).

    1.3	Definiciones, Siglas y Abreviaturas

    | Término | Definición |
    |---|---|
    | **BD** | Base de Datos |
    | **SGBD** | Sistema de Gestión de Base de Datos |
    | **API** | Application Programming Interface (Interfaz de Programación de Aplicaciones) |
    | **REST** | Representational State Transfer (estilo arquitectónico para servicios web) |
    | **KPI** | Key Performance Indicator (Indicador Clave de Rendimiento) |
    | **Flask** | Microframework web de Python utilizado como base del backend |
    | **psutil** | Biblioteca de Python para obtener métricas del sistema operativo (CPU, RAM, disco) |
    | **Chart.js** | Biblioteca JavaScript para renderizado de gráficos interactivos en el navegador |
    | **Snapshot** | Captura instantánea de las métricas de una base de datos en un momento dado |
    | **Datasource** | Fuente de datos; representa la configuración de conexión a un motor de BD |
    | **Cache Hit Ratio** | Porcentaje de solicitudes de datos atendidas desde la caché del motor de BD |
    | **QPS** | Queries Per Second (Consultas por segundo) |
    | **VM** | Virtual Machine (Máquina Virtual) |
    | **DSN** | Data Source Name (cadena de conexión a una base de datos) |
    | **CRUD** | Create, Read, Update, Delete (operaciones básicas de datos) |
    | **CSV** | Comma-Separated Values (formato de exportación de datos) |
    | **Gunicorn** | Servidor HTTP WSGI para Python, utilizado en despliegue de producción |

    1.4	Referencias

    | Referencia | Descripción |
    |---|---|
    | README.md del proyecto | Documentación técnica de instalación, configuración y uso del sistema |
    | FD01-Informe-Factibilidad.md | Informe de factibilidad del proyecto |
    | Documentación oficial de Flask | https://flask.palletsprojects.com/ |
    | Documentación de psutil | https://psutil.readthedocs.io/ |
    | Documentación de Chart.js | https://www.chartjs.org/docs/ |
    | Documentación de PostgreSQL | https://www.postgresql.org/docs/ |
    | Documentación de MySQL | https://dev.mysql.com/doc/ |
    | IEEE Std 830-1998 | Prácticas recomendadas para especificación de requisitos de software |

    1.5	Visión General

    El presente documento se encuentra organizado de la siguiente manera:

    - **Sección 1 — Introducción**: Presenta el propósito, alcance, definiciones y referencias del documento.
    - **Sección 2 — Posicionamiento**: Describe la oportunidad de negocio y la definición del problema que motiva la creación del sistema.
    - **Sección 3 — Descripción de los interesados y usuarios**: Identifica los perfiles de interesados, usuarios y sus necesidades.
    - **Sección 4 — Vista General del Producto**: Detalla la perspectiva del producto, sus capacidades, suposiciones, costos y licenciamiento.
    - **Sección 5 — Características del producto**: Enumera las funcionalidades principales del sistema.
    - **Sección 6 — Restricciones**: Documenta las limitaciones técnicas, de negocio y regulatorias.
    - **Sección 7 — Rangos de calidad**: Define los atributos de calidad esperados del sistema.
    - **Sección 8 — Precedencia y Prioridad**: Establece el orden de prioridad de las características.
    - **Sección 9 — Otros requerimientos del producto**: Describe estándares legales, de comunicación, de plataforma y de calidad y seguridad.
    - **Conclusiones y Recomendaciones**: Cierre del documento con observaciones finales.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

2. <span id="_Toc52661347" class="anchor"></span>**Posicionamiento**

    2.1	Oportunidad de negocio

    En el contexto actual de las organizaciones educativas y empresariales, la gestión de múltiples motores de bases de datos se ha convertido en una tarea cada vez más compleja. Los administradores de bases de datos (DBA) y equipos de infraestructura de TI necesitan supervisar simultáneamente el rendimiento, la disponibilidad y la integridad de servidores que ejecutan distintos SGBD (PostgreSQL, MySQL, MariaDB, SQL Server, MongoDB), a menudo distribuidos en diferentes hosts y entornos.

    Actualmente, las soluciones de monitoreo de bases de datos disponibles en el mercado (como Datadog, New Relic, pgAdmin, MySQL Workbench, etc.) presentan alguna de las siguientes limitaciones:

    - **Costo elevado**: Las soluciones comerciales requieren licencias que pueden resultar prohibitivas para instituciones educativas y pequeñas y medianas empresas.
    - **Monitoreo mono-motor**: Muchas herramientas se especializan en un único SGBD, lo que obliga a mantener múltiples herramientas cuando se trabaja con entornos heterogéneos.
    - **Complejidad de configuración**: Herramientas como Prometheus + Grafana requieren configuración avanzada de exporters, dashboards y alertas.
    - **Sin gestión de archivos integrada**: Pocas soluciones ofrecen visibilidad sobre los archivos de configuración, datos, logs y backups del motor de BD de forma unificada.

    DB Health Monitor aprovecha esta oportunidad al ofrecer una solución **unificada, multi-motor, de código abierto y bajo costo**, que centraliza el monitoreo de salud de bases de datos y del servidor anfitrión en un único dashboard web. Su diseño orientado a la simplicidad permite que tanto estudiantes como profesionales de TI puedan desplegarla rápidamente sin conocimientos avanzados de infraestructura.

    2.2	Definición del problema

    |  |  |
    |---|---|
    | **El problema de** | La falta de visibilidad centralizada sobre el estado de salud y rendimiento de múltiples motores de bases de datos y sus servidores anfitriones. |
    | **Afecta a** | Administradores de bases de datos, equipos de infraestructura de TI, docentes y estudiantes del curso de Base de Datos II de la UPT que gestionan entornos con múltiples SGBD. |
    | **El impacto del cual es** | Detección tardía de problemas de rendimiento (saturación de conexiones, degradación del cache hit ratio, consumo excesivo de recursos del host), tiempos de inactividad no planificados, pérdida potencial de datos por falta de supervisión de backups, y dificultad para realizar análisis de tendencias históricas. |
    | **Una solución exitosa debería** | Proporcionar un dashboard web unificado que recolecte automáticamente métricas de múltiples motores de BD (PostgreSQL, MySQL, MariaDB, SQL Server, MongoDB), almacene snapshots históricos, genere alertas basadas en umbrales configurables, ofrezca inventario de archivos de los motores y permita la gestión multi-usuario con roles diferenciados. |

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

3. <span id="_Toc52661348" class="anchor"></span>**Vista General del Producto**

    3.1	Resumen de los interesados

    | Nombre | Descripción | Responsabilidad |
    |---|---|---|
    | Docente del curso (Mag. Patrick Cuadros Quiroga) | Docente responsable del curso Base de Datos II en la EPIS-UPT. | Supervisa el desarrollo del proyecto, evalúa el cumplimiento de los objetivos académicos y valida la calidad técnica del entregable. |
    | Equipo de desarrollo (Hashira Vargas, Ariana Espinoza) | Estudiantes de Ingeniería de Sistemas responsables del diseño, implementación y pruebas del sistema. | Análisis de requerimientos, diseño de la arquitectura, codificación del backend (Flask/Python) y frontend (HTML/CSS/JS), configuración de la base de datos PostgreSQL, pruebas funcionales e integración. |
    | Administradores de BD (usuarios finales) | Profesionales de TI o estudiantes avanzados encargados de gestionar servidores de bases de datos en entornos de laboratorio o producción. | Utilizan el sistema para monitorear el estado de sus bases de datos, configurar datasources, revisar alertas y exportar reportes. |

    3.2	Resumen de los usuarios

    | Nombre | Descripción | Responsabilidad |
    |---|---|---|
    | Administrador del sistema (rol `admin`) | Usuario con privilegios completos que puede gestionar todos los datasources y ver todos los usuarios del sistema. | Registrar y administrar fuentes de datos de cualquier usuario, supervisar el estado global del sistema, acceder al panel de administración y gestionar cuentas de usuario. |
    | Usuario estándar (rol `user`) | Usuario registrado que puede crear sus propias fuentes de datos y monitorear únicamente las que le pertenecen. | Registrar sus propias fuentes de datos (datasources), visualizar métricas y alertas de sus bases, exportar datos a CSV. |
    | Visor (rol `viewer`) | Usuario con acceso de solo lectura a las fuentes de datos asignadas. | Consultar métricas, historial y alertas de las fuentes de datos a las que tiene acceso, sin capacidad de modificar configuraciones. |

    3.3	Entorno de usuario

    Los usuarios acceden al sistema a través de un **navegador web moderno** (Chrome, Firefox, Edge, Safari) en cualquier dispositivo con conectividad de red hacia el servidor Flask. El entorno de despliegue contempla:

    - **Servidor de aplicación**: Máquina virtual Debian con Python 3.10+ ejecutando la aplicación Flask. En desarrollo se usa el servidor integrado de Flask (`python server.py`); en producción se recomienda Gunicorn con 4 workers.
    - **Servidor de base de datos del monitor**: PostgreSQL 15 en la misma VM Debian (IP: `38.250.116.71`, puerto `5432`, base `db_health_monitor`).
    - **Fuentes de datos monitoreadas**: Pueden residir en el mismo servidor o en hosts remotos accesibles por red. Se soportan PostgreSQL, MySQL, MariaDB, SQL Server y MongoDB.
    - **Interfaz web**: Dashboard SPA (Single Page Application) que consume endpoints REST JSON. Utiliza Chart.js para gráficos y diseño glassmorphism responsive con fuentes Inter y JetBrains Mono.

    El flujo típico del usuario es:
    1. Acceder a `http://<host>:5000` e iniciar sesión (o crear cuenta).
    2. Registrar una o más fuentes de datos (datasources) con los parámetros de conexión.
    3. El sistema recolecta métricas automáticamente cada 10 segundos y actualiza el dashboard.
    4. El usuario consulta KPIs, gráficos históricos, estado de archivos y alertas.
    5. Opcionalmente, exporta datos a CSV para análisis externo.

    3.4	Perfiles de los interesados

    **Docente del curso**

    |  |  |
    |---|---|
    | **Representante** | Mag. Patrick Cuadros Quiroga |
    | **Descripción** | Docente responsable del curso Base de Datos II, Facultad de Ingeniería, UPT. |
    | **Tipo** | Evaluador y supervisor académico |
    | **Responsabilidades** | Definir los criterios de evaluación del proyecto, revisar los entregables, validar que el sistema cumple con los objetivos de aprendizaje del curso. |
    | **Criterio de éxito** | El sistema demuestra el dominio de conceptos de administración de bases de datos, monitoreo de métricas y uso de múltiples motores SGBD. |
    | **Implicación** | Revisión periódica de avances y evaluación final del proyecto. |

    **Equipo de desarrollo**

    |  |  |
    |---|---|
    | **Representantes** | Hashira Vargas Candia (2022075480), Ariana Espinoza Castañeda (2022073904) |
    | **Descripción** | Estudiantes de la EPIS responsables del ciclo completo de desarrollo. |
    | **Tipo** | Desarrolladores full-stack |
    | **Responsabilidades** | Diseño de la arquitectura, implementación del backend en Flask/Python, frontend en HTML/CSS/JS, configuración de PostgreSQL como BD del monitor, integración con múltiples motores de BD, pruebas y documentación. |
    | **Criterio de éxito** | Sistema funcional que monitorea al menos 5 tipos de motores de BD con dashboard interactivo, alertas y gestión multi-usuario. |
    | **Implicación** | Dedicación completa al desarrollo durante el ciclo académico 2026-I. |

    3.5	Perfiles de los Usuarios

    **Administrador del sistema**

    |  |  |
    |---|---|
    | **Representante** | Usuario con rol `admin` (e.g., `hashira`) |
    | **Descripción** | Responsable de la configuración global del sistema, gestión de todos los datasources y supervisión de usuarios. |
    | **Tipo** | Usuario experto con conocimientos de administración de BD |
    | **Responsabilidades** | Configurar el sistema, registrar datasources propios y de otros usuarios, supervisar el estado global, gestionar cuentas de usuario desde el panel de administración. |
    | **Criterio de éxito** | Visibilidad completa del estado de todas las fuentes de datos y usuarios del sistema. |

    **Usuario estándar**

    |  |  |
    |---|---|
    | **Representante** | Cualquier usuario registrado con rol `user` |
    | **Descripción** | Usuario que registra y monitorea sus propias fuentes de datos. |
    | **Tipo** | Usuario intermedio con conocimientos básicos de bases de datos |
    | **Responsabilidades** | Registrar sus datasources, monitorear métricas, revisar alertas, exportar reportes. |
    | **Criterio de éxito** | Capacidad de monitorear el estado de sus bases de datos sin requerir acceso directo al servidor. |

    **Visor**

    |  |  |
    |---|---|
    | **Representante** | Usuario con rol `viewer` (e.g., `ariana`) |
    | **Descripción** | Usuario con acceso de solo lectura al sistema. |
    | **Tipo** | Usuario básico |
    | **Responsabilidades** | Consultar métricas y alertas de las fuentes de datos asignadas. |
    | **Criterio de éxito** | Acceso sencillo e intuitivo a la información de monitoreo sin riesgo de modificar la configuración. |

    3.6	Necesidades de los interesados y usuarios

    | Necesidad | Prioridad | Característica del sistema | Solución actual | Solución propuesta |
    |---|---|---|---|---|
    | Monitorear el rendimiento de múltiples motores de BD desde un único punto | Alta | Dashboard unificado multi-motor | Uso de herramientas separadas por motor (pgAdmin, MySQL Workbench, etc.) | Dashboard web que consolida métricas de PostgreSQL, MySQL, MariaDB, SQL Server y MongoDB |
    | Detectar problemas de rendimiento antes de que causen interrupciones | Alta | Sistema de alertas con umbrales configurables | Revisión manual periódica de logs y estadísticas | Alertas automáticas con niveles WARNING y CRITICAL basadas en umbrales de conexiones, cache, CPU y memoria |
    | Visualizar tendencias históricas del rendimiento | Media | Historial de snapshots con gráficos | No hay registro histórico; solo estadísticas en tiempo real | Snapshots almacenados en PostgreSQL con gráficos interactivos Chart.js y exportación a CSV |
    | Controlar el acceso al sistema de monitoreo | Media | Autenticación y autorización por roles | Sin control de acceso | Sistema de login con roles (admin/user/viewer) y aislamiento de datasources por propietario |
    | Inspeccionar archivos de configuración y estado de los motores de BD | Baja | Inventario de archivos | Acceso manual vía SSH/terminal al servidor | Explorador de archivos integrado con información de existencia, tamaño y fecha de modificación |
    | Despliegue sencillo sin costos de licenciamiento | Alta | Arquitectura basada en tecnologías open source | Herramientas comerciales con costo de licencia | Stack completo open source: Python, Flask, PostgreSQL, Chart.js |

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

4. <span id="_Toc52661349" class="anchor"></span>**Estudio de
    Factibilidad**

    4.1	Perspectiva del producto

    DB Health Monitor es un sistema web **independiente y autocontenido** que no depende de productos o componentes comerciales externos. Se integra con los motores de bases de datos monitoreados únicamente a través de sus protocolos nativos de conexión (protocolo wire de PostgreSQL, protocolo MySQL, TDS para SQL Server, protocolo wire de MongoDB).

    El siguiente diagrama muestra la arquitectura general del sistema:

    ```mermaid
    graph TB
        subgraph "Navegador Web (Cliente)"
            UI["Dashboard SPA<br/>HTML/CSS/JS + Chart.js"]
        end

        subgraph "Servidor Flask (Backend)"
            APP["Flask App<br/>server.py"]
            BG["Background Collector<br/>Hilo de fondo"]
            AUTH["Módulo de Autenticación<br/>Roles: admin/user/viewer"]
            CONN["db_connection.py<br/>Pool de conexiones"]
        end

        subgraph "BD del Monitor (PostgreSQL)"
            PG_MON["db_health_monitor"]
            T1["auth_users"]
            T2["datasources"]
            T3["health_snapshots"]
            T4["alert_log"]
        end

        subgraph "Fuentes de Datos Monitoreadas"
            DS_PG["PostgreSQL"]
            DS_MY["MySQL / MariaDB"]
            DS_SS["SQL Server"]
            DS_MO["MongoDB"]
        end

        UI -->|"REST API JSON<br/>HTTP"| APP
        APP --> AUTH
        APP --> CONN
        BG -->|"Cada 10s"| CONN
        CONN --> PG_MON
        PG_MON --> T1
        PG_MON --> T2
        PG_MON --> T3
        PG_MON --> T4
        CONN -->|"psycopg2"| DS_PG
        CONN -->|"mysql-connector"| DS_MY
        CONN -->|"pymssql"| DS_SS
        CONN -->|"pymongo"| DS_MO
    ```

    El sistema se compone de tres capas principales:

    - **Capa de presentación**: Dashboard SPA servido por Flask, con diseño responsive glassmorphism, fuentes Google Fonts (Inter, JetBrains Mono) y gráficos Chart.js.
    - **Capa de lógica de negocio**: Aplicación Flask con hilo de fondo para recolección periódica de métricas, evaluación de alertas, gestión de sesiones y control de acceso por roles.
    - **Capa de datos**: PostgreSQL como almacén centralizado del monitor (tablas `auth_users`, `datasources`, `health_snapshots`, `alert_log`), con conexiones dinámicas a los motores de BD monitoreados mediante drivers específicos.

    4.2	Resumen de capacidades

    | Beneficio para el usuario | Característica de soporte |
    |---|---|
    | Monitoreo centralizado de múltiples motores de BD | Soporte nativo para PostgreSQL, MySQL, MariaDB, SQL Server y MongoDB mediante drivers específicos (psycopg2, mysql-connector-python, pymssql, pymongo) |
    | Detección proactiva de problemas de rendimiento | Sistema de alertas con umbrales configurables (WARNING/CRITICAL) para conexiones, cache hit ratio, CPU y memoria |
    | Visualización intuitiva de métricas en tiempo real | Dashboard con 6 KPIs principales (Conexiones, Cache, CPU, Memoria, Disco, Estado General) con barras de progreso y código de colores |
    | Análisis de tendencias históricas | Almacenamiento de snapshots en PostgreSQL con gráficos interactivos de líneas (conexiones, cache hit, CPU/memoria) y exportación a CSV |
    | Gestión segura multi-usuario | Autenticación con hash seguro (werkzeug.security), roles diferenciados (admin/user/viewer) y aislamiento de datos por propietario |
    | Inspección remota de archivos del motor de BD | Inventario de archivos de configuración, datos, logs y backups con información de existencia, tamaño y fecha de modificación |
    | Gestión dinámica de fuentes de datos | CRUD completo de datasources con prueba de conectividad integrada (latencia en ms) |
    | Panel de administración global | Vista exclusiva para administradores con listado de todos los usuarios y todas las fuentes de datos del sistema |

    4.3	Suposiciones y dependencias

    **Suposiciones:**

    - Los motores de bases de datos a monitorear son accesibles por red desde el servidor donde se ejecuta DB Health Monitor (puertos abiertos, reglas de firewall configuradas).
    - Las credenciales proporcionadas para cada datasource tienen al menos permisos de lectura sobre las vistas del sistema y estadísticas del motor (e.g., `pg_stat_database`, `information_schema`, `sys.dm_exec_sessions`, etc.).
    - El servidor anfitrión cuenta con Python 3.10 o superior instalado.
    - Se dispone de una instancia PostgreSQL 15+ accesible para almacenar los datos del monitor.
    - Los navegadores web de los usuarios son versiones modernas que soportan ES6+ y CSS3.

    **Dependencias:**

    | Dependencia | Versión | Propósito |
    |---|---|---|
    | Python | ≥ 3.10 | Runtime del backend |
    | Flask | 3.1.0 | Framework web |
    | flask-cors | 5.0.0 | Habilitación de CORS para la API REST |
    | psycopg2-binary | Última estable | Driver PostgreSQL y pool de conexiones del monitor |
    | psutil | 6.1.1 | Métricas del sistema operativo (CPU, RAM, disco) |
    | mysql-connector-python | 8.4.0 | Driver para MySQL y MariaDB |
    | pymssql | 2.3.13 | Driver para SQL Server |
    | pymongo | 4.8.0 | Driver para MongoDB |
    | gunicorn | 23.0.0 | Servidor WSGI para despliegue en producción |
    | Chart.js | 4.4.4 (CDN) | Librería de gráficos para el frontend |
    | Google Fonts (Inter, JetBrains Mono) | CDN | Tipografía del dashboard |

    4.4	Costos y precios

    DB Health Monitor está diseñado como un proyecto académico de código abierto. Los costos asociados son mínimos y se resumen a continuación:

    | Concepto | Costo estimado (USD) | Observación |
    |---|---|---|
    | Servidor VM Debian (hosting) | $5.00 – $10.00/mes | VPS con 1–2 vCPU, 2 GB RAM, 20 GB SSD (e.g., DigitalOcean, Linode) |
    | Dominio (opcional) | $10.00 – $15.00/año | Registro de dominio `.com` o `.dev` |
    | Licencias de software | $0.00 | Todo el stack es open source (Python, Flask, PostgreSQL, Chart.js) |
    | Infraestructura de red | $0.00 | Se utiliza la red de la universidad o el proveedor de VPS |
    | Costos de desarrollo (personal) | $0.00 | Desarrollo realizado como proyecto académico por las integrantes del equipo |
    | **Total estimado (mensual)** | **$5.00 – $10.00** | Sin contar dominio opcional |

    > **Nota**: Para entornos de laboratorio universitario, el sistema puede desplegarse en la infraestructura existente de la UPT sin costos adicionales.

    4.5	Licenciamiento e instalación

    **Licenciamiento:**
    - El sistema utiliza exclusivamente componentes de **código abierto** con licencias permisivas (MIT, BSD, Apache 2.0, PSF License).
    - Python: PSF License. Flask: BSD License. PostgreSQL: PostgreSQL License. Chart.js: MIT License. psutil: BSD License.
    - No se requiere adquisición de licencias comerciales para ningún componente del stack tecnológico.

    **Instalación:**
    La instalación del sistema se realiza mediante los siguientes pasos:

    1. Clonar el repositorio del proyecto desde GitHub.
    2. Crear un entorno virtual de Python y activarlo:
       ```bash
       python -m venv .venv
       source .venv/bin/activate  # Linux/macOS
       ```
    3. Instalar las dependencias:
       ```bash
       pip install -r requirements.txt
       ```
    4. Configurar el archivo `config.ini` con los parámetros de conexión a PostgreSQL y los umbrales deseados.
    5. Ejecutar el servidor:
       ```bash
       python server.py
       ```
    6. Acceder al dashboard en `http://localhost:5000`.

    Para producción, se recomienda usar Gunicorn:
    ```bash
    gunicorn -w 4 -b 0.0.0.0:8000 server:app
    ```

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

5. <span id="_Toc52661350" class="anchor"></span>**Características del producto**

    Las características principales del sistema DB Health Monitor se agrupan en las siguientes áreas funcionales:

    **CP-01: Autenticación y gestión de usuarios**
    - Registro de nuevos usuarios con validación de longitud mínima (usuario ≥ 3 caracteres, contraseña ≥ 6 caracteres) y confirmación de contraseña.
    - Inicio de sesión con verificación de hash seguro (Werkzeug `scrypt`).
    - Gestión de sesiones con roles diferenciados: `admin`, `user`, `viewer`.
    - Cierre de sesión.
    - Protección de endpoints API con middleware `before_request`.

    **CP-02: Gestión de fuentes de datos (Datasources)**
    - Registro de nuevas fuentes de datos especificando: nombre, tipo de BD (PostgreSQL, MySQL, MariaDB, SQL Server, MongoDB), host, puerto, usuario, contraseña, nombre de la base de datos y estado (activa/inactiva).
    - Listado de fuentes de datos filtrado por propietario (aislamiento por usuario).
    - Edición de parámetros de conexión de fuentes existentes.
    - Eliminación de fuentes de datos con limpieza de caché.
    - Prueba de conectividad con medición de latencia en milisegundos.

    **CP-03: Recolección automática de métricas**
    - Hilo de fondo (`background_collector`) que recolecta métricas cada 10 segundos (configurable vía `config.ini`).
    - Métricas recolectadas por motor:
      - **PostgreSQL**: `max_connections`, `numbackends`, consultas activas, consultas en espera, cache hit ratio (`pg_stat_database`), tamaño de BD (`pg_database_size`), uptime.
      - **MySQL/MariaDB**: `Threads_connected`, `Threads_running`, `Slow_queries`, InnoDB buffer pool hit ratio, tamaño de BD (`information_schema.tables`), uptime.
      - **SQL Server**: sesiones de usuario, consultas activas/en espera, buffer cache hit ratio (`sys.dm_os_performance_counters`), tamaño de BD (`sys.master_files`), uptime.
      - **MongoDB**: conexiones actuales/disponibles, WiredTiger cache hit ratio, `dbStats`, operaciones activas (`currentOp`), uptime.
    - Métricas del host (psutil): CPU %, memoria %, uso de disco %, espacio libre en disco, número de procesos.
    - Evaluación de estado: `OK`, `WARNING`, `CRITICAL` basada en umbrales configurables.

    **CP-04: Sistema de alertas**
    - Evaluación automática de umbrales con cuatro métricas monitoreadas:
      - Conexiones %: WARNING ≥ 70%, CRITICAL ≥ 90%.
      - Cache Hit Ratio %: WARNING < 85%, CRITICAL < 70%.
      - CPU %: WARNING ≥ 75%, CRITICAL ≥ 90%.
      - Memoria %: WARNING ≥ 80%, CRITICAL ≥ 95%.
    - Registro persistente de alertas en tabla `alert_log` con severidad, métrica, valor, umbral y mensaje.
    - Consulta de historial de alertas con filtro por datasource.

    **CP-05: Dashboard de visualización**
    - 6 tarjetas KPI con barras de progreso: Conexiones, Cache Hit Ratio, CPU, Memoria, Disco, Estado General.
    - 3 gráficos históricos interactivos (Chart.js): Conexiones y estado, Cache Hit Ratio, CPU/Memoria.
    - Resumen global: BD activas, conectadas, offline, archivos monitoreados.
    - Actualización automática de la interfaz cada intervalo de recolección.
    - Exportación de historial de métricas, estado y alertas a formato CSV.

    **CP-06: Inventario de archivos de BD**
    - Explorador de archivos de configuración, datos, logs y backups de cada motor de BD.
    - Filtrado por tipo de archivo mediante chips interactivos.
    - Información de cada archivo: existencia, tipo (archivo/directorio), tamaño en MB, fecha de modificación, número de entradas.
    - Perfiles de rutas predefinidos para cada motor (configurable en `config.ini`).

    **CP-07: Panel de administración**
    - Vista exclusiva para usuarios con rol `admin`.
    - Listado de todos los usuarios del sistema con rol, estado, fecha de creación y último acceso.
    - Listado de todas las fuentes de datos con dueño, tipo, host, base y estado.
    - Contadores globales de usuarios y fuentes.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

6. <span id="_Toc52661351" class="anchor"></span>**Restricciones**

    El desarrollo e implementación del sistema DB Health Monitor está sujeto a las siguientes restricciones:

    **Restricciones técnicas:**
    - El backend debe desarrollarse en **Python 3.10+** utilizando el framework **Flask**, según los requisitos del curso de Base de Datos II.
    - La base de datos centralizada del monitor debe ser **PostgreSQL 15+**, ejecutándose en la VM Debian proporcionada.
    - La interfaz web debe ser funcional en navegadores modernos (Chrome ≥ 90, Firefox ≥ 88, Edge ≥ 90) sin requerir instalación de plugins adicionales.
    - Las conexiones a los motores de BD monitoreados se realizan mediante **drivers Python nativos** (psycopg2, mysql-connector-python, pymssql, pymongo); no se utiliza ORM.
    - La recolección de métricas del sistema operativo depende de la biblioteca `psutil`; si no está disponible, las métricas del host se reportan como 0.

    **Restricciones de negocio:**
    - El proyecto se desarrolla dentro del marco académico del ciclo 2026-I del curso SI783 — Base de Datos II, con fecha de entrega definida por el calendario académico.
    - El equipo de desarrollo está conformado por dos integrantes.
    - No se dispone de presupuesto para herramientas o servicios comerciales.

    **Restricciones de seguridad:**
    - Las contraseñas de usuario se almacenan como hashes seguros (algoritmo `scrypt` de Werkzeug); en ningún caso se almacenan en texto plano.
    - Las contraseñas de los datasources se almacenan en la tabla `datasources` en texto plano en la BD del monitor. Se recomienda restringir el acceso a la BD del monitor.
    - La comunicación entre el navegador y el servidor Flask no implementa HTTPS en la configuración por defecto; se recomienda configurar un reverse proxy con certificado SSL para entornos de producción.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

7. <span id="_Toc52661352" class="anchor"></span>**Rangos de Calidad**

    El sistema DB Health Monitor debe cumplir con los siguientes atributos de calidad:

    | Atributo | Descripción | Métrica objetivo |
    |---|---|---|
    | **Disponibilidad** | El sistema debe estar disponible de forma continua para la recolección de métricas y consulta del dashboard. | ≥ 99% de uptime durante el periodo de evaluación (excluyendo mantenimiento planificado). |
    | **Rendimiento** | El tiempo de respuesta de la API REST debe ser adecuado para una experiencia interactiva. | Respuesta de endpoints JSON ≤ 500 ms para ≤ 10 datasources concurrentes. |
    | **Escalabilidad** | El sistema debe soportar la adición de nuevas fuentes de datos sin degradación significativa. | Soporte de al menos 20 datasources activos simultáneamente con intervalo de recolección de 10 segundos. |
    | **Usabilidad** | La interfaz debe ser intuitiva y no requerir capacitación especializada. | Un usuario con conocimientos básicos de BD debe poder configurar un datasource y consultar métricas en menos de 5 minutos. |
    | **Mantenibilidad** | El código debe ser legible, modular y documentado. | Separación clara entre capas (presentación, lógica, datos). Código documentado con docstrings y comentarios. |
    | **Seguridad** | El sistema debe proteger las credenciales y controlar el acceso. | Hashing seguro de contraseñas, control de acceso por roles, protección de endpoints con middleware de autenticación. |
    | **Portabilidad** | El sistema debe poder desplegarse en diferentes entornos. | Compatible con Linux (Debian/Ubuntu) y Windows. Configuración mediante archivo `config.ini` y variables de entorno. |

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

8. <span id="_Toc52661353" class="anchor"></span>**Precedencia y Prioridad**

    Las características del producto se priorizan de acuerdo con su impacto en la funcionalidad core del sistema y los objetivos académicos del proyecto:

    | Prioridad | Característica | Justificación |
    |---|---|---|
    | **1 – Crítica** | CP-03: Recolección automática de métricas | Funcionalidad central del sistema; sin ella no hay monitoreo. |
    | **2 – Crítica** | CP-01: Autenticación y gestión de usuarios | Requisito de seguridad fundamental para el acceso al sistema. |
    | **3 – Alta** | CP-02: Gestión de fuentes de datos (CRUD) | Permite configurar los datasources a monitorear; habilitante para CP-03. |
    | **4 – Alta** | CP-05: Dashboard de visualización | Proporciona la interfaz principal para consumir las métricas recolectadas. |
    | **5 – Alta** | CP-04: Sistema de alertas | Agrega valor proactivo al monitoreo detectando anomalías automáticamente. |
    | **6 – Media** | CP-06: Inventario de archivos de BD | Funcionalidad complementaria que enriquece la visibilidad del estado del motor. |
    | **7 – Media** | CP-07: Panel de administración | Necesario para la gestión global pero no para el monitoreo operativo diario. |

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

9. <span id="_Toc52661354" class="anchor"></span>**Otros requerimientos del producto**

    a) **Estándares aplicables**

    - **ISO/IEC 25010:2011**: Modelo de calidad del producto de software. El sistema se evalúa bajo los atributos de adecuación funcional, eficiencia de desempeño, compatibilidad, usabilidad, fiabilidad, seguridad, mantenibilidad y portabilidad.
    - **ISO/IEC 27001**: Referencia para la gestión de seguridad de la información, aplicada al manejo de credenciales de acceso a bases de datos y al control de acceso por roles.

    b) Estandares legales

    - **Ley N° 29733 — Ley de Protección de Datos Personales (Perú)**: El sistema almacena credenciales de usuarios y contraseñas de conexión a bases de datos. Se implementa hashing seguro (scrypt) para las contraseñas de usuario. Las contraseñas de datasources se almacenan de forma cifrable en la BD del monitor, con acceso restringido a usuarios autenticados.
    - **Ley N° 30096 — Ley de Delitos Informáticos (Perú)**: El acceso al sistema requiere autenticación. Solo los usuarios autorizados pueden acceder a las métricas y configuraciones de las fuentes de datos que les pertenecen. El registro de actividad (alertas, snapshots) proporciona trazabilidad.
    - **Reglamento General de Protección de Datos (RGPD)**: Si bien es una regulación europea, se toman como buena práctica sus principios de minimización de datos y limitación de acceso.

    c) Estandares de comunicación

    - **HTTP/1.1 (RFC 7230-7235)**: Protocolo de comunicación entre el navegador y el servidor Flask para las peticiones REST.
    - **JSON (RFC 8259)**: Formato de intercambio de datos utilizado en todos los endpoints de la API (`/api/metrics`, `/api/health`, `/api/history`, `/api/alerts/history`, etc.).
    - **SQL**: Lenguaje de consulta estándar utilizado para la comunicación con los motores de bases de datos relacionales (PostgreSQL, MySQL, SQL Server).
    - **Protocolo Wire de MongoDB**: Protocolo binario utilizado para la comunicación con instancias MongoDB a través del driver pymongo.
    - **CORS (Cross-Origin Resource Sharing)**: Habilitado mediante flask-cors para permitir peticiones desde orígenes cruzados cuando sea necesario.

    d) Estandaraes de cumplimiento de la plataforma

    - **Python PEP 8**: Estilo de codificación del backend siguiendo las convenciones de Python.
    - **Compatibilidad con WSGI (PEP 3333)**: La aplicación Flask es compatible con servidores WSGI como Gunicorn para despliegue en producción.
    - **Responsive Web Design**: La interfaz web se adapta a diferentes tamaños de pantalla (desktop, tablet) mediante CSS Grid y media queries.
    - **Semántica HTML5**: Uso de elementos semánticos (`<header>`, `<main>`, `<footer>`, `<section>`, `<nav>`) para accesibilidad y SEO.

    e) Estandaraes de calidad y seguridad

    - **Hashing de contraseñas**: Uso del algoritmo `scrypt` (a través de `werkzeug.security`) con salt aleatorio para el almacenamiento seguro de contraseñas de usuario.
    - **Control de acceso basado en roles (RBAC)**: Tres niveles de acceso (admin, user, viewer) implementados mediante middleware `before_request` y verificación de sesión.
    - **Pool de conexiones**: Uso de `psycopg2.pool.ThreadedConnectionPool` para la gestión eficiente y segura de conexiones a la BD del monitor, evitando fugas de conexiones.
    - **Validación de entradas**: Validación de campos requeridos en la creación de datasources, longitud mínima de usuario y contraseña en el registro, y verificación de confirmación de contraseña.
    - **Manejo de errores**: Captura de excepciones en la recolección de métricas y la inicialización de la BD con reintentos configurables (`retries=10`, `delay=6.0`).
    - **Aislamiento de datos**: Los usuarios solo ven los datasources que les pertenecen (filtrado por `owner_username`), excepto los administradores que tienen visibilidad global.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

<span id="_Toc52661355" class="anchor"></span>**CONCLUSIONES**

1. El sistema **DB Health Monitor** responde a una necesidad real de los administradores de bases de datos y equipos de TI: disponer de una herramienta unificada y de bajo costo que centralice el monitoreo de múltiples motores de bases de datos y del servidor anfitrión en un único dashboard web.

2. El análisis de los interesados y usuarios permite identificar tres perfiles diferenciados (administrador, usuario estándar y visor) cuyas necesidades son cubiertas por las siete características funcionales del producto (CP-01 a CP-07).

3. La arquitectura propuesta, basada en **Flask + PostgreSQL + drivers nativos multi-motor**, garantiza la factibilidad técnica del proyecto al utilizar exclusivamente tecnologías de código abierto, maduras y ampliamente documentadas.

4. El soporte de cinco motores de bases de datos (PostgreSQL, MySQL, MariaDB, SQL Server, MongoDB) diferencia a DB Health Monitor de las herramientas mono-motor existentes, proporcionando un valor agregado significativo para entornos heterogéneos.

5. El sistema de alertas con umbrales configurables permite la detección proactiva de problemas de rendimiento, reduciendo el riesgo de interrupciones no planificadas en los servicios de base de datos.

6. Los costos operativos del sistema son mínimos (≈ $5–$10/mes en un VPS básico), lo que lo hace viable para entornos académicos y organizaciones con presupuesto limitado.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

<span id="_Toc52661356" class="anchor"></span>**RECOMENDACIONES**

1. **Implementar cifrado de contraseñas de datasources**: Actualmente las contraseñas de conexión a los motores de BD se almacenan en texto plano en la tabla `datasources`. Se recomienda implementar cifrado simétrico (e.g., Fernet de la biblioteca `cryptography`) para proteger estas credenciales en reposo.

2. **Configurar HTTPS**: Desplegar un reverse proxy (Nginx o Caddy) con certificado SSL/TLS (Let's Encrypt) frente a la aplicación Flask para cifrar la comunicación entre el navegador y el servidor.

3. **Integrar notificaciones externas**: Ampliar el sistema de alertas con canales de notificación como correo electrónico (SMTP), Telegram Bot o Slack webhooks para alertar a los administradores en tiempo real.

4. **Implementar exportación de reportes en PDF**: Complementar la exportación CSV con generación de reportes PDF que incluyan gráficos y resúmenes ejecutivos para presentaciones gerenciales.

5. **Agregar métricas adicionales**: Incorporar métricas como QPS (queries por segundo) mediante muestreo diferencial, replication lag para configuraciones maestro-réplica, y métricas específicas de cada motor (e.g., WAL lag en PostgreSQL, replication delay en MySQL).

6. **Evaluar la adopción de contenedores**: Empaquetar la aplicación en un contenedor Docker con un `docker-compose.yml` que incluya la BD del monitor, para simplificar el despliegue y garantizar reproducibilidad del entorno.

7. **Realizar pruebas de carga**: Ejecutar pruebas de rendimiento con herramientas como Locust o k6 para validar el comportamiento del sistema con un número creciente de datasources y usuarios concurrentes.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

<span id="_Toc52661357" class="anchor"></span>**BIBLIOGRAFIA**

1. Lutz, M. (2013). *Learning Python* (5th ed.). O'Reilly Media.
2. Grinberg, M. (2018). *Flask Web Development: Developing Web Applications with Python* (2nd ed.). O'Reilly Media.
3. Juba, S., & Volkov, A. (2019). *Learning PostgreSQL 12* (4th ed.). Packt Publishing.
4. Schwartz, B., Zaitsev, P., & Tkachenko, V. (2012). *High Performance MySQL* (3rd ed.). O'Reilly Media.
5. Chodorow, K. (2013). *MongoDB: The Definitive Guide* (2nd ed.). O'Reilly Media.
6. ISO/IEC 25010:2011. *Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — System and software quality models*.
7. IEEE Std 830-1998. *IEEE Recommended Practice for Software Requirements Specifications*.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

<span id="_Toc52661358" class="anchor"></span>**WEBGRAFIA**

1. Flask Documentation. Pallets Projects. Recuperado de: https://flask.palletsprojects.com/
2. psutil Documentation. Recuperado de: https://psutil.readthedocs.io/
3. Chart.js Documentation. Recuperado de: https://www.chartjs.org/docs/
4. PostgreSQL Official Documentation. Recuperado de: https://www.postgresql.org/docs/
5. MySQL Reference Manual. Recuperado de: https://dev.mysql.com/doc/
6. SQL Server Technical Documentation. Microsoft. Recuperado de: https://learn.microsoft.com/en-us/sql/
7. MongoDB Documentation. Recuperado de: https://www.mongodb.com/docs/
8. psycopg2 Documentation. Recuperado de: https://www.psycopg.org/docs/
9. mysql-connector-python Documentation. Recuperado de: https://dev.mysql.com/doc/connector-python/en/
10. pymssql Documentation. Recuperado de: https://pymssql.readthedocs.io/
11. pymongo Documentation. Recuperado de: https://pymongo.readthedocs.io/
12. Werkzeug Security Module. Recuperado de: https://werkzeug.palletsprojects.com/en/stable/utils/#module-werkzeug.security
13. Gunicorn Documentation. Recuperado de: https://docs.gunicorn.org/en/stable/
14. Google Fonts — Inter, JetBrains Mono. Recuperado de: https://fonts.google.com/

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>
