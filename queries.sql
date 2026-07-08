EXECUTE 'SELECT * FROM usuarios WHERE id = ' || id_usuario;

CREATE USER admin_temporal IDENTIFIED BY 'SuperSecret123';

SET PASSWORD = 'Monitor2026!@#';

SET API_KEY = 'dhm_QLv99H_y50yQD0WT_xZOKG5';

GRANT ALL PRIVILEGES ON db_ventas_prod.* TO 'admin_temporal'@'%';

GRANT SELECT ON clientes TO PUBLIC;

DROP DATABASE db_rrhh_test;

TRUNCATE TABLE logs_auditoria;

SELECT clientes.nombre, pedidos.total
FROM clientes
CROSS JOIN pedidos;
