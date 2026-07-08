# Monitor de Salud DB — Extensión de VS Code

Esta es la extensión oficial de VS Code para el sistema **Monitor de Salud DB**. Permite visualizar métricas en tiempo real, alertas de bases de datos y explorar archivos de logs y configuración del motor directamente desde el editor.

## Requisitos
- Servidor web del Monitor de Salud DB activo (por defecto en `http://localhost:5000`).
- Una API Key activa (generada desde el panel web de Integraciones).

## Características
- **Vista de árbol en la Barra de Actividad**: Lista de bases de datos registradas con sus estados e iconos de salud (Ok, Advertencia, Crítico, Inactivo).
- **Inspección de Archivos**: Expande cada base de datos para ver sus archivos de configuración y logs. Haz clic en ellos para abrirlos en un editor de VS Code en modo lectura.
- **Alertas en Segundo Plano**: Recibe notificaciones flotantes ante eventos críticos o advertencias en tus servidores de datos.
- **Dashboard Detallado**: Abre un panel webview dinámico para visualizar las métricas en tiempo real (CPU, memoria, disco y conexiones).
