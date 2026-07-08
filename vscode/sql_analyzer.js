/**
 * Módulo analizador estático para scripts y consultas SQL.
 * Detecta problemas de seguridad, rendimiento y buenas prácticas mediante expresiones regulares.
 */

function analyze(text) {
    const findings = [];
    const lines = text.split('\n');

    const rules = [
        {
            // Detect dynamic SQL string concatenation (often vulnerable to SQL Injection)
            // e.g. EXECUTE 'SELECT * FROM users WHERE id = ' || var_id;
            // e.g. EXEC('SELECT * FROM ' + @table)
            regex: /\b(EXEC|EXECUTE)\s*\(?\s*['"][^'"]*['"]\s*(\+|\|\|)/i,
            severity: 'error',
            message: 'Riesgo de Inyección SQL: Concatenación detectada en consulta dinámica. Usa consultas parametrizadas.'
        },
        {
            // e.g. CREATE USER admin IDENTIFIED BY 'SuperSecret123';
            regex: /\bIDENTIFIED\s+BY\s+['"]([^'"]+)['"]/i,
            severity: 'error',
            message: 'Seguridad: Credencial expuesta en texto plano (IDENTIFIED BY).'
        },
        {
            // e.g. SET PASSWORD = 'mypassword';
            regex: /\bPASSWORD\s*=\s*['"]([^'"]+)['"]/i,
            severity: 'error',
            message: 'Seguridad: Asignación de contraseña expuesta en texto plano.'
        },
        {
            // e.g. SET API_KEY = 'dhm_abc123';
            regex: /\b(SECRET|API_KEY|TOKEN)\s*=\s*['"]([^'"]{4,})['"]/i,
            severity: 'error',
            message: 'Seguridad: Llave secreta o token de autenticación expuesto en texto plano.'
        },
        {
            // e.g. GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost';
            regex: /\bGRANT\s+ALL(\s+PRIVILEGES)?\b/i,
            severity: 'warning',
            message: 'Buenas Prácticas: Se recomienda otorgar privilegios específicos en lugar de GRANT ALL.'
        },
        {
            // e.g. GRANT SELECT ON my_table TO PUBLIC;
            regex: /\bTO\s+PUBLIC\b/i,
            severity: 'warning',
            message: 'Seguridad: Evita otorgar privilegios de acceso al rol global PUBLIC.'
        },
        {
            // e.g. DROP DATABASE production;
            regex: /\bDROP\s+DATABASE\b/i,
            severity: 'warning',
            message: 'Peligro: Operación altamente destructiva detectada (DROP DATABASE). Úsese con precaución.'
        },
        {
            // e.g. TRUNCATE TABLE users;
            regex: /\bTRUNCATE\s+TABLE\b/i,
            severity: 'info',
            message: 'Info: Sentencia destructiva (TRUNCATE TABLE) vacía todo el contenido de la tabla de forma irreversible.'
        },
        {
            // e.g. SELECT * FROM users CROSS JOIN logs;
            regex: /\bCROSS\s+JOIN\b/i,
            severity: 'info',
            message: 'Rendimiento: CROSS JOIN genera un producto cartesiano. Asegúrate de que sea la operación deseada.'
        }
    ];

    lines.forEach((line, lineIdx) => {
        rules.forEach(rule => {
            // Reset regex index (in case of flags, though we aren't using /g here)
            rule.regex.lastIndex = 0;
            const match = rule.regex.exec(line);
            if (match) {
                findings.push({
                    line: lineIdx,
                    startChar: match.index,
                    endChar: match.index + match[0].length,
                    severity: rule.severity,
                    message: rule.message
                });
            }
        });
    });

    return findings;
}

module.exports = {
    analyze
};
