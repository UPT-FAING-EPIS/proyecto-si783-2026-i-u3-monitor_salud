-- ============================================================
-- vulnerable_demo.sql
-- Script de DEMOSTRACIÓN ACADÉMICA para probar la Auditoría SQL
-- de la extensión "Monitor de Salud DB".
-- Contiene patrones INSEGUROS A PROPÓSITO. NO USAR EN PRODUCCIÓN.
-- ============================================================

-- 1) INYECCIÓN SQL: concatenación dinámica dentro de EXECUTE
--    (regla: EXEC/EXECUTE + concatenación con '+' o '||')
EXECUTE 'SELECT * FROM usuarios WHERE id = ' || id_usuario;

-- 2) CREDENCIAL EXPUESTA: creación de usuario con contraseña en texto plano
--    (regla: IDENTIFIED BY '...')
CREATE USER admin_temporal IDENTIFIED BY 'SuperSecret123';

-- 3) CONTRASEÑA EN TEXTO PLANO en una asignación directa
--    (regla: PASSWORD = '...')
SET PASSWORD = 'Monitor2026!@#';

-- 4) TOKEN / API KEY EXPUESTA en el propio script
--    (regla: SECRET|API_KEY|TOKEN = '...')
SET API_KEY = 'dhm_QLv99H_y50yQD0WT_xZOKG5';

-- 5) PRIVILEGIOS EXCESIVOS: GRANT ALL sin restricción de tabla
--    (regla: GRANT ALL [PRIVILEGES])
GRANT ALL PRIVILEGES ON db_ventas_prod.* TO 'admin_temporal'@'%';

-- 6) ACCESO AL ROL GLOBAL PUBLIC (cualquier usuario del sistema)
--    (regla: TO PUBLIC)
GRANT SELECT ON clientes TO PUBLIC;

-- 7) OPERACIÓN ALTAMENTE DESTRUCTIVA: eliminar toda una base de datos
--    (regla: DROP DATABASE)
DROP DATABASE db_rrhh_test;

-- 8) SENTENCIA DESTRUCTIVA: vacía una tabla completa sin posibilidad de rollback simple
--    (regla: TRUNCATE TABLE)
TRUNCATE TABLE logs_auditoria;

-- 9) PROBLEMA DE RENDIMIENTO: CROSS JOIN genera producto cartesiano
--    (regla: CROSS JOIN)
SELECT clientes.nombre, pedidos.total
FROM clientes
CROSS JOIN pedidos;
