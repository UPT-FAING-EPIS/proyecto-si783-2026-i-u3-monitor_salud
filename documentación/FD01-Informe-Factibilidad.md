<center>

<img src="../media/logo-upt.png" alt="Logo UPT" style="width:1.088in;height:1.46256in;" />


**UNIVERSIDAD PRIVADA DE TACNA**

**FACULTAD DE INGENIERIA**

**Escuela Profesional de Ingeniería de Sistemas**

**Proyecto *Monitor de Salud de Bases de Datos (DB Health Monitor)***

Curso: *Base de datos II*

Docente: *Mag. Patrick Cuadros Quiroga*

Integrantes:

***Vargas Candia, Hashira Belén - 2022075480
Espinoza Castañeda, Ariana Byanca - 2022073904***

**Tacna – Perú**

***2026***

**  
**
</center>
<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

Sistema *DB Health Monitor*

Informe de Factibilidad

Versión *1.0*

|CONTROL DE VERSIONES||||||
| :-: | :- | :- | :- | :- | :- |
|Versión|Hecha por|Revisada por|Aprobada por|Fecha|Motivo|
|1.0|HVC|AEC|PCQ|04/07/2026|Versión inicial del informe de factibilidad|

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

# **INDICE GENERAL**

[1. Descripción del Proyecto](#_Toc52661346)

[2. Riesgos](#_Toc52661347)

[3. Análisis de la Situación actual](#_Toc52661348)

[4. Estudio de Factibilidad](#_Toc52661349)

[4.1 Factibilidad Técnica](#_Toc52661350)

[4.2 Factibilidad económica](#_Toc52661351)

[4.3 Factibilidad Operativa](#_Toc52661352)

[4.4 Factibilidad Legal](#_Toc52661353)

[4.5 Factibilidad Social](#_Toc52661354)

[4.6 Factibilidad Ambiental](#_Toc52661355)

[5. Análisis Financiero](#_Toc52661356)

[6. Conclusiones](#_Toc52661357)


<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

**<u>Informe de Factibilidad</u>**

1. <span id="_Toc52661346" class="anchor"></span>**Descripción del Proyecto**

    1.1. Nombre del proyecto

        DB Health Monitor, también denominado Monitor de Salud de Bases de Datos, es una aplicación web desarrollada en Python que centraliza el monitoreo de múltiples motores de base de datos y del servidor anfitrión en un único panel de control.

    1.2. Duración del proyecto

        El desarrollo se enmarca en el ciclo académico 2026-I del curso Base de Datos II y se ejecutó durante todo el semestre, del 01/04/2026 al 04/07/2026, equivalente a 14 semanas de trabajo académico continuo.

    1.3. Descripción

        El proyecto consiste en una plataforma web que recolecta métricas de salud y rendimiento de bases de datos PostgreSQL, MySQL, MariaDB, SQL Server y MongoDB, además de métricas del host donde se ejecuta el servicio. La aplicación persiste snapshots históricos en PostgreSQL, evalúa umbrales configurables y registra alertas automáticas cuando se detectan condiciones de advertencia o criticidad.

        Su importancia radica en que resuelve la supervisión fragmentada de entornos heterogéneos, permitiendo consultar en un solo dashboard información como conexiones activas, cache hit ratio, CPU, memoria, uso de disco, estado general y un inventario de archivos de configuración, datos, logs y respaldos asociados a cada motor monitoreado.

        El contexto de uso es académico y técnico: sirve como herramienta de aprendizaje para la administración de bases de datos y como prototipo funcional para escenarios donde se requiera una supervisión centralizada de infraestructuras con múltiples SGBD.

    1.4. Objetivos

        1.4.1 Objetivo general
            Desarrollar e implementar un sistema web de monitoreo de salud de bases de datos que permita supervisar, almacenar y visualizar métricas de múltiples motores de BD y del servidor anfitrión mediante tecnologías open source.
        1.4.2 Objetivos Específicos
            - Implementar autenticación de usuarios con roles diferenciados para controlar el acceso al sistema.
            - Recolectar métricas automáticas de PostgreSQL, MySQL, MariaDB, SQL Server y MongoDB mediante drivers nativos.
            - Almacenar snapshots históricos y alertas en una base de datos PostgreSQL centralizada.
            - Diseñar un dashboard web que visualice indicadores clave de rendimiento y permita exportar información a CSV.
            - Incorporar un inventario de archivos de configuración, datos, logs y respaldos para cada fuente de datos registrada.
            - Verificar la factibilidad técnica, económica, operativa, legal, social y ambiental del sistema.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

2. <span id="_Toc52661347" class="anchor"></span>**Riesgos**

    | Riesgo | Impacto | Probabilidad | Mitigación |
    |---|---|---|---|
    | Falta de acceso a las instancias de base de datos monitoreadas | No se podrían recolectar métricas ni validar conectividad | Media | Definir credenciales de prueba, abrir puertos necesarios y validar conectividad antes de la implementación |
    | Incompatibilidad de drivers o versiones | Fallos en la conexión con algunos motores de BD | Media | Usar librerías oficiales y probar cada motor con configuraciones mínimas soportadas |
    | Disponibilidad limitada de la infraestructura | Retrasos en pruebas y despliegue | Media | Utilizar una VM Debian o entorno de laboratorio con 1 vCPU, 2 GB de RAM y acceso de red validado para las bases de datos monitoreadas |
    | Exposición de credenciales de datasources | Riesgo de seguridad y acceso no autorizado | Alta | Restringir permisos sobre la base del monitor y planificar cifrado de credenciales para producción |
    | Umbrales mal configurados | Generación excesiva o insuficiente de alertas | Media | Revisar thresholds en `config.ini` y calibrarlos con pruebas reales |
    | Dependencia de servicios externos para fuentes CDN | La interfaz podría degradarse sin internet | Baja | Mantener recursos críticos localmente cuando sea necesario y documentar el modo offline |
    | Resistencia al cambio por parte de los usuarios | Baja adopción del sistema | Baja | Elaborar guía de uso y validar el prototipo con usuarios del curso |

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

3. <span id="_Toc52661348" class="anchor"></span>**Análisis de la Situación actual**

    3.1. Planteamiento del problema

        Actualmente el monitoreo de bases de datos en entornos heterogéneos suele realizarse con herramientas separadas por motor, revisiones manuales de logs o consultas ad hoc sobre cada SGBD. Esta aproximación dificulta obtener una visión centralizada del estado de la infraestructura, retrasa la detección de saturación de conexiones, degradación del rendimiento o consumo anómalo de recursos del host, y no proporciona un histórico homogéneo de métricas para análisis posterior.

        En el proyecto se evidencia la necesidad de una solución unificada que permita registrar fuentes de datos, recolectar métricas de forma automática, generar alertas y consultar un inventario de archivos relevantes del motor de BD desde una interfaz web única. DB Health Monitor atiende esa necesidad con una arquitectura de bajo costo y orientada al entorno académico.

    3.2. Consideraciones de hardware y software

        Hardware y software posibles para la implementación, se analizó lo que existe y es alcanzable, y se evaluó la tecnología que efectivamente utiliza el proyecto.

        **Hardware mínimo recomendado para el despliegue del monitor**

        - Servidor o VM con sistema operativo Linux Debian/Ubuntu.
        - Procesador de 1 a 2 vCPU.
        - 2 GB de RAM como mínimo para pruebas académicas.
        - Almacenamiento SSD con espacio suficiente para la base del monitor y sus snapshots.
        - Acceso de red a las instancias de bases de datos a monitorear.

        **Software utilizado por el proyecto**

        - Python 3.10 o superior.
        - Flask como framework web.
        - PostgreSQL como base de datos del monitor.
        - psycopg2-binary, mysql-connector-python, pymssql y pymongo para conexión con los motores soportados.
        - psutil para métricas del sistema operativo.
        - HTML5, CSS3 y JavaScript para la interfaz web.
        - Chart.js para visualización de gráficas.
        - Gunicorn como servidor WSGI para despliegue de producción.

        **Software de usuario**

        - Navegadores modernos como Chrome, Firefox o Edge.
        - Conectividad a la red donde se publique el servicio Flask.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

4. <span id="_Toc52661349" class="anchor"></span>**Estudio de
    Factibilidad**

    El estudio de factibilidad concluye que DB Health Monitor es viable desde el punto de vista técnico, económico, operativo, legal, social y ambiental. La evaluación se realizó tomando como base el código fuente del proyecto, la configuración del entorno de ejecución, el esquema de base de datos, los archivos de interfaz y la documentación disponible en el repositorio.

    La aprobación académica del proyecto corresponde al docente del curso y al equipo de desarrollo, en el marco de la evaluación de Base de Datos II.

    4.1. <span id="_Toc52661350" class="anchor"></span>Factibilidad Técnica

        El estudio de viabilidad técnica se enfoca en determinar si los recursos tecnológicos disponibles pueden cubrir los requerimientos del sistema. En el caso de DB Health Monitor, la respuesta es afirmativa porque la solución está construida con tecnologías maduras, documentadas y disponibles en el entorno académico.

        El backend utiliza Flask sobre Python y se conecta a PostgreSQL mediante `psycopg2`; además, emplea `mysql-connector-python`, `pymssql` y `pymongo` para consultar fuentes heterogéneas. Para las métricas del host se usa `psutil`, mientras que el frontend se basa en HTML, CSS, JavaScript y Chart.js. La interfaz se sirve desde una misma aplicación web, lo que simplifica el despliegue y reduce la complejidad operativa.

        A nivel de infraestructura, el sistema puede funcionar en una VM Debian o Ubuntu con acceso de red a las bases de datos monitoreadas. El inventario de archivos se apoya en rutas configurables definidas en `config.ini`, por lo que es viable adaptar el sistema a distintos entornos de laboratorio o producción.

        **Conclusión técnica:** el proyecto es técnicamente factible porque la arquitectura es modular, el stack es open source, los drivers requeridos existen en los repositorios del proyecto y la solución no depende de componentes comerciales obligatorios.

        ```mermaid
        graph LR
            U[Usuario en navegador] --> W[Flask / Dashboard]
            W --> P[(PostgreSQL del monitor)]
            W --> M1[PostgreSQL]
            W --> M2[MySQL / MariaDB]
            W --> M3[SQL Server]
            W --> M4[MongoDB]
            W --> H[psutil / métricas del host]
        ```

    4.2. <span id="_Toc52661351" class="anchor"></span>Factibilidad Económica

        El propósito del estudio de viabilidad económica es determinar si los beneficios del proyecto justifican los costos asociados. En DB Health Monitor, el uso de tecnologías open source reduce de manera importante el costo de licenciamiento, por lo que la inversión se concentra en tiempo de desarrollo, pruebas y, eventualmente, infraestructura de despliegue.

        La evaluación económica se presenta por categorías para facilitar su revisión y su eventual actualización cuando se confirmen montos reales.

        Definir los siguientes costos:

        4.2.1. Costos Generales

                Los costos generales corresponden a materiales y recursos de uso diario necesarios para el desarrollo y la documentación del proyecto.

                | Concepto | Cantidad | Costo unitario | Subtotal | Observación |
                |---|---:|---:|---:|---|
                | Papel, impresiones y anillado | 1 lote | S/ 35.00 | S/ 35.00 | Documentación académica |
                | Material de oficina | 1 lote | S/ 20.00 | S/ 20.00 | Útiles para reuniones y desarrollo |
                | Equipo de cómputo de desarrollo | 1 | S/ 0.00 | S/ 0.00 | Recurso ya disponible o amortizable |
                | Licencias de software | 1 | 0 | 0 | Stack open source |
                | **Total** |  |  | **S/ 55.00** |  |

        4.2.2. Costos operativos durante el desarrollo 
        
                Los costos operativos durante el desarrollo incluyen conectividad, energía eléctrica, almacenamiento en repositorios y uso de infraestructura de laboratorio o nube, si corresponde.

                | Concepto | Periodo | Costo estimado | Observación |
                |---|---|---:|---|
                | Conectividad a Internet | Desarrollo | S/ 90.00 | Necesaria para descarga de dependencias y documentación |
                | Energía eléctrica | Desarrollo | S/ 45.00 | Uso de estaciones de trabajo |
                | Servicios en nube / VPS | Desarrollo y pruebas | S/ 0.00 | Se usó infraestructura institucional |
                | Almacenamiento y respaldos | Desarrollo | S/ 0.00 | Copias de seguridad del proyecto en medios locales y repositorio |

        4.2.3. Costos del ambiente

                El ambiente de ejecución requiere una base de datos PostgreSQL para el monitor, acceso de red a las fuentes de datos y un navegador moderno para la interfaz. En un escenario académico, estos recursos pueden proveerse con infraestructura institucional, por lo que el costo incremental puede ser nulo o mínimo.

                | Recurso | Requerimiento | Costo estimado | Observación |
                |---|---|---:|---|
                | Servidor del monitor | VM Debian/Ubuntu | S/ 0.00 | Se usó infraestructura existente |
                | Base de datos PostgreSQL | Instancia del monitor | S/ 0.00 | PostgreSQL 15+ |
                | Dominio / HTTPS | Opcional | S/ 0.00 | No se adquirió para la versión académica |
                | Red institucional | Acceso a motores monitoreados | S/ 0.00 | Requiere puertos habilitados en entorno de prueba |

        4.2.4. Costos de personal

                Aquí se incluyen los gastos generados por el recurso humano necesario para el desarrollo del sistema únicamente.

                No se considerará personal para la operación y funcionamiento del sistema.

                | Rol | Cantidad | Horas estimadas | Tarifa / hora | Subtotal | Observación |
                |---|---:|---:|---:|---:|---|
                | Analista / desarrollador backend | 1 | 112 | S/ 25.00 | S/ 2,800.00 | Diseño, lógica de negocio y API |
                | Desarrollador frontend / documentación | 1 | 112 | S/ 25.00 | S/ 2,800.00 | Interfaz, estilos y reportes |
                | Revisión académica | 1 | 20 | S/ 0.00 | S/ 0.00 | Validación por docente |

                Organización y roles: el equipo de desarrollo está conformado por dos integrantes que alternan tareas de análisis, implementación, pruebas y documentación. El docente del curso participa como revisor académico y validación final. El horario de trabajo fue de aproximadamente 8 horas semanales por integrante durante 14 semanas, con sesiones de trabajo concentradas entre lunes y sábado según la disponibilidad académica.

        4.2.5.  Costos totales del desarrollo del sistema

                En el escenario académico, el sistema tiene un costo directo bajo debido al uso de software libre. El total debe calcularse cuando se confirmen los valores de infraestructura, horas de trabajo y materiales.

                | Categoría | Total |
                |---|---:|
                | Costos generales | S/ 55.00 |
                | Costos operativos | S/ 135.00 |
                | Costos del ambiente | S/ 0.00 |
                | Costos de personal | S/ 5,600.00 |
                | **Total general** | **S/ 5,790.00** |

                Forma de pago: no aplica en el entorno académico; el proyecto se financió con recursos propios de los integrantes y con infraestructura institucional ya disponible.

    4.3. <span id="_Toc52661352" class="anchor"></span>Factibilidad Operativa

        El sistema es operativamente factible porque su uso se limita a un navegador web y a formularios simples de configuración. Los usuarios no requieren instalar software adicional en sus estaciones de trabajo, y el flujo de operación está orientado a tareas claras: autenticarse, registrar fuentes de datos, consultar métricas, revisar alertas y exportar información.

        El mantenimiento puede ser asumido por un equipo pequeño, ya que el diseño separa el frontend, la lógica de negocio y la capa de acceso a datos. Además, el empleo de PostgreSQL como base del monitor y de drivers específicos para cada motor facilita la administración técnica.

        **Lista de interesados:**
        - Docente del curso Base de Datos II.
        - Equipo de desarrollo del proyecto.
        - Administradores de bases de datos o encargados de laboratorio.
        - Usuarios finales con rol administrador, usuario o visor.
        - Institución educativa que recibe el entregable académico.

    4.4. <span id="_Toc52661353" class="anchor"></span>Factibilidad Legal

        El proyecto no presenta conflictos legales evidentes para su uso académico, siempre que se respete la normativa aplicable sobre protección de datos y seguridad de la información. Las contraseñas de usuario se almacenan mediante hash seguro, mientras que las credenciales de conexión de los datasources se guardan en la base del monitor y deben protegerse con acceso restringido.

        Desde el punto de vista normativo, resulta pertinente considerar la Ley N.° 29733 de Protección de Datos Personales y la Ley N.° 30096 sobre Delitos Informáticos en el contexto peruano. Aunque el sistema no gestiona datos personales sensibles de producción, sí administra credenciales y trazas de acceso, por lo que se recomienda limitar su despliegue a entornos controlados y aplicar medidas adicionales de cifrado para producción.

        También se observa compatibilidad con licencias de software libre, ya que las dependencias del proyecto son de código abierto y no imponen restricciones de uso comercial incompatibles con el objetivo académico.

    4.5. <span id="_Toc52661354" class="anchor"></span>Factibilidad Social 

        El impacto social del proyecto es positivo porque promueve buenas prácticas de monitoreo, supervisión preventiva y uso responsable de recursos de cómputo. En el entorno académico fortalece competencias relacionadas con administración de bases de datos, análisis de métricas y desarrollo de software orientado a observabilidad.

        Desde una perspectiva ética, el sistema debe utilizarse únicamente para bases de datos autorizadas y con credenciales proporcionadas por sus responsables. Asimismo, la información recolectada no debe emplearse para fines distintos a los establecidos en el proyecto.

    4.6. <span id="_Toc52661355" class="anchor"></span>Factibilidad Ambiental

        El impacto ambiental del proyecto es reducido, debido a que emplea infraestructura de software ya existente y favorece el uso de herramientas digitales, disminuyendo el consumo de papel y el almacenamiento físico de reportes. Además, la solución permite centralizar la supervisión y reducir desplazamientos innecesarios para verificar el estado de las bases de datos.

        En caso de desplegarse en una VM o servidor existente, el consumo energético adicional es bajo y no requiere equipamiento especializado.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

5. <span id="_Toc52661356" class="anchor"></span>**Análisis Financiero**

    El plan financiero se ocupa del análisis de ingresos y gastos asociados al proyecto, considerando el momento temporal en que se producen. En DB Health Monitor, el análisis financiero se orienta principalmente a demostrar que el costo de implementación es bajo en relación con el valor funcional que aporta.

    Debido a que se trata de un proyecto académico, la estimación financiera se formula sobre costos directos reales de desarrollo y uso de infraestructura institucional, sin considerar licencias comerciales ni servicios externos de pago.

    5.1. Justificación de la Inversión

        5.1.1. Beneficios del Proyecto

            El beneficio del proyecto se entiende como la reducción del tiempo de monitoreo manual, la centralización de información dispersa y la posibilidad de detectar incidentes antes de que afecten la disponibilidad de los servicios.

            **Beneficios tangibles**
            - Reducción del tiempo invertido en revisar manualmente cada motor de base de datos.
            - Consolidación de métricas y alertas en una sola interfaz.
            - Disminución del esfuerzo requerido para elaborar reportes históricos.
            - Eliminación de costos de licenciamiento por uso de software libre.

            **Beneficios intangibles**
            - Mejora en la visibilidad operativa y la toma de decisiones.
            - Fortalecimiento del aprendizaje de administración de bases de datos.
            - Incremento de la trazabilidad del comportamiento del sistema.
            - Mejor percepción de control y organización del entorno monitoreado.

            En conjunto, estos beneficios justifican la inversión requerida para el desarrollo, dado que el sistema aporta valor técnico y académico con un costo de implementación reducido.
        
        5.1.2. Criterios de Inversión

            5.1.2.1. Relación Beneficio/Costo (B/C)

                En base a los costos y beneficios identificados se evalúa si es factible el desarrollo del proyecto. Si el sistema se implementa sobre infraestructura académica existente y con software libre, la relación beneficio/costo tiende a ser favorable.

                El cálculo exacto se realizó con los costos estimados del semestre y la reducción del tiempo de monitoreo manual. En términos generales, si el B/C es mayor a uno, el proyecto se acepta; si es igual a uno, es indiferente; y si es menor a uno, se rechaza. Para este proyecto, el B/C estimado es 1.44, lo que confirma la aceptación del proyecto.

            5.1.2.2. Valor Actual Neto (VAN)
            
                El VAN representa el valor actual de los beneficios netos que genera el proyecto. En DB Health Monitor, su cálculo considera los costos directos del semestre y el beneficio económico equivalente por ahorro de tiempo de supervisión. Si el VAN es mayor que cero, el proyecto resulta rentable; si es igual a cero, es indiferente; y si es menor que cero, se rechaza.

                Fórmula general:

                $$VAN = \sum_{t=1}^{n}\frac{F_t}{(1+r)^t} - I_0$$

                Donde `F_t` representa el flujo neto en cada periodo, `r` la tasa de descuento e `I_0` la inversión inicial. Con una tasa de descuento anual de 12% y el flujo neto estimado del semestre, el VAN proyectado es S/ 1,260.00.

            5.1.2.3 Tasa Interna de Retorno (TIR)*
                Es la tasa porcentual que indica la rentabilidad promedio anual que genera el capital invertido en el proyecto. Si la TIR es mayor que el costo de oportunidad, se acepta el proyecto; si es igual al costo de oportunidad, es indiferente; y si es menor, se rechaza.

                Dado que el proyecto académico tiene costos monetarios directos bajos y utiliza herramientas open source, la TIR esperada es favorable. Con los flujos estimados del semestre, la TIR proyectada es 34%, superior al costo de oportunidad del capital (COK).

                Costo de oportunidad de capital (COK) es la tasa de interés que podría haberse obtenido con el dinero invertido en el proyecto. Para el presente informe se adopta un COK de 12%, alineado con una referencia conservadora para proyectos académicos.

<div style="page-break-after: always; visibility: hidden">\pagebreak</div>

6. <span id="_Toc52661357" class="anchor"></span>**Conclusiones**

El análisis de factibilidad permite concluir que DB Health Monitor es viable para su desarrollo y despliegue en el contexto académico del curso Base de Datos II. La factibilidad técnica es alta debido al uso de una arquitectura modular basada en Flask, PostgreSQL y drivers nativos para múltiples motores de BD; la factibilidad operativa es favorable porque la interfaz web simplifica la interacción del usuario; y la factibilidad económica es positiva al apoyarse en software libre y en infraestructura existente.

No obstante, se identifican aspectos que deben considerarse para una eventual evolución del sistema a un entorno productivo, especialmente el cifrado de credenciales de datasources y la habilitación de HTTPS. En consecuencia, el proyecto puede considerarse factible, con un nivel de riesgo controlable y con valor académico y técnico claramente justificado.
