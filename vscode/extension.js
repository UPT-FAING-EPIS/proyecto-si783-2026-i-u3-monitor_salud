const vscode = require('vscode');
const child_process = require('child_process');
const path = require('path');
const fs = require('fs');
const sqlAnalyzer = require('./sql_analyzer');

// Helper to run python script commands
function runHelper(command, args = []) {
    return new Promise((resolve, reject) => {
        const config = vscode.workspace.getConfiguration('dbMonitor');
        const pythonPath = config.get('pythonPath') || 'python';
        const helperPath = path.join(__dirname, 'helper.py');
        
        const allArgs = [helperPath, command, ...args];
        
        // Cwd should be the workspace root or the extension folder
        const workspaceFolders = vscode.workspace.workspaceFolders;
        const workspacePath = workspaceFolders && workspaceFolders.length > 0 ? workspaceFolders[0].uri.fsPath : null;
        
        const cwd = workspacePath || __dirname;

        const env = { ...process.env };
        if (workspacePath) {
            env.WORKSPACE_ROOT = workspacePath;
        }

        child_process.execFile(pythonPath, allArgs, { cwd, env }, (error, stdout, stderr) => {
            if (error) {
                const errMsg = stderr.trim() || error.message;
                return reject(new Error(`Error ejecutando Python: ${errMsg}`));
            }
            try {
                const parsed = JSON.parse(stdout);
                if (parsed && parsed.error) {
                    return reject(new Error(parsed.error));
                }
                resolve(parsed);
            } catch (e) {
                reject(new Error(`Error parseando respuesta de helper.py: ${stdout}`));
            }
        });
    });
}

// Helper to perform HTTP/REST requests to the remote monitor server
function fetchApi(apiPath, method = 'GET', body = null) {
    return new Promise((resolve, reject) => {
        const config = vscode.workspace.getConfiguration('dbMonitor');
        const serverUrl = (config.get('serverUrl') || 'http://38.250.116.71:5000').trim().replace(/\/+$/, '');
        const apiKey = (config.get('apiKey') || '').trim();

        if (!serverUrl) {
            return reject(new Error('La URL del servidor del Monitor de Salud DB no está configurada.'));
        }

        // Handle path format
        const endpointUrl = apiPath.startsWith('http') ? apiPath : `${serverUrl}${apiPath}`;
        
        let parsedUrl;
        try {
            parsedUrl = new URL(endpointUrl);
        } catch (e) {
            return reject(new Error(`URL de servidor o API inválida: ${endpointUrl}`));
        }

        const isHttps = parsedUrl.protocol === 'https:';
        const client = isHttps ? require('https') : require('http');

        const headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) VSCode-DbMonitor/0.1.6'
        };

        if (apiKey) {
            headers['Authorization'] = `Bearer ${apiKey}`;
        }

        let postData = null;
        if (body) {
            postData = JSON.stringify(body);
            headers['Content-Type'] = 'application/json';
            headers['Content-Length'] = Buffer.byteLength(postData);
        }

        const options = {
            method: method,
            headers: headers,
            timeout: 10000 // 10s timeout
        };

        const req = client.request(parsedUrl, options, (res) => {
            let responseData = '';
            res.on('data', (chunk) => {
                responseData += chunk;
            });
            res.on('end', () => {
                let parsed;
                try {
                    parsed = JSON.parse(responseData);
                } catch (e) {
                    parsed = null;
                }

                if (res.statusCode >= 200 && res.statusCode < 300) {
                    resolve(parsed !== null ? parsed : responseData);
                } else {
                    let errMsg = `Error ${res.statusCode}`;
                    if (parsed && parsed.error) {
                        errMsg = parsed.error;
                    } else if (responseData && responseData.length < 100) {
                        errMsg = responseData;
                    }
                    reject(new Error(errMsg));
                }
            });
        });

        req.on('error', (err) => {
            reject(new Error(`Error de conexión: ${err.message}`));
        });

        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Tiempo de espera agotado al conectar con el servidor.'));
        });

        if (postData) {
            req.write(postData);
        }
        req.end();
    });
}

// Custom text document provider for configuration/log files
class DbMonitorFileProvider {
    provideTextDocumentContent(uri) {
        const dsId = uri.authority;
        const filePath = uri.path;

        return fetchApi(`/api/v1/files/read?datasource_id=${dsId}&path=${encodeURIComponent(filePath)}`)
            .then(res => {
                if (res && res.content !== undefined) {
                    return res.content;
                }
                return 'No se pudo leer el contenido del archivo o está vacío.';
            })
            .catch(err => {
                return `Error leyendo archivo desde el monitor remoto: ${err.message}`;
            });
    }
}

// Webview View Provider for the Sidebar Panel
class DbMonitorSidebarWebviewProvider {
    constructor(context) {
        this._context = context;
    }

    resolveWebviewView(webviewView, context, token) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._context.extensionUri]
        };

        const htmlPath = path.join(this._context.extensionPath, 'sidebar.html');
        let htmlContent = '';
        try {
            htmlContent = fs.readFileSync(htmlPath, 'utf8');
        } catch (err) {
            webviewView.webview.html = `<h3>Error cargando el panel lateral: ${err.message}</h3>`;
            return;
        }

        webviewView.webview.html = htmlContent;

        // Manage sidebar events
        webviewView.webview.onDidReceiveMessage(async (message) => {
            try {
                if (message.command === 'getDbList') {
                    const datasources = await fetchApi('/api/v1/datasources');
                    webviewView.webview.postMessage({ command: 'dbListResult', data: datasources });
                } else if (message.command === 'getConfig') {
                    const config = vscode.workspace.getConfiguration('dbMonitor');
                    const apiKey = config.get('apiKey') || '';
                    webviewView.webview.postMessage({ command: 'configResult', apiKey });
                } else if (message.command === 'saveToken') {
                    const config = vscode.workspace.getConfiguration('dbMonitor');
                    await config.update('apiKey', message.token.trim(), vscode.ConfigurationTarget.Global);
                    vscode.window.showInformationMessage('API Token del Monitor de Salud guardado correctamente.');
                    sidebarProvider.refresh();
                } else if (message.command === 'scanSqlFiles') {
                    const files = await vscode.workspace.findFiles('**/*.{sql,ddl,mysql,pgsql,sqlserver}', '**/node_modules/**');
                    const results = [];
                    
                    for (const fileUri of files) {
                        try {
                            const doc = await vscode.workspace.openTextDocument(fileUri);
                            const text = doc.getText();
                            const findings = sqlAnalyzer.analyze(text);
                            
                            const workspaceFolders = vscode.workspace.workspaceFolders;
                            const rootPath = workspaceFolders && workspaceFolders.length > 0 ? workspaceFolders[0].uri.fsPath : '';
                            const relativePath = path.relative(rootPath, fileUri.fsPath);
                            
                            results.push({
                                uriString: fileUri.toString(),
                                fileName: path.basename(fileUri.fsPath),
                                relativePath,
                                findings
                            });
                        } catch (e) {
                            console.error(`Error al analizar ${fileUri.fsPath}:`, e);
                        }
                    }
                    
                    // Sort so files with findings are shown first
                    results.sort((a, b) => b.findings.length - a.findings.length);
                    webviewView.webview.postMessage({ command: 'scanSqlResult', data: results });
                } else if (message.command === 'openFile') {
                    const uri = vscode.Uri.parse(message.uriString);
                    const doc = await vscode.workspace.openTextDocument(uri);
                    await vscode.window.showTextDocument(doc);
                } else if (message.command === 'openFinding') {
                    const uri = vscode.Uri.parse(message.uriString);
                    const doc = await vscode.workspace.openTextDocument(uri);
                    const editor = await vscode.window.showTextDocument(doc);
                    const posStart = new vscode.Position(message.line, message.startChar);
                    const posEnd = new vscode.Position(message.line, message.endChar);
                    editor.selection = new vscode.Selection(posStart, posEnd);
                    editor.revealRange(new vscode.Range(posStart, posEnd), vscode.TextEditorRevealType.InCenter);
                } else if (message.command === 'viewDashboard') {
                    vscode.commands.executeCommand('db-monitor.viewDashboard', {
                        dsId: message.dsId,
                        dsName: message.dsName
                    });
                }
            } catch (err) {
                if (message.command === 'getDbList') {
                    webviewView.webview.postMessage({ command: 'dbListError', message: err.message });
                } else if (message.command === 'scanSqlFiles') {
                    webviewView.webview.postMessage({ command: 'scanSqlError', message: err.message });
                }
            }
        });
    }

    refresh() {
        if (this._view) {
            this._view.webview.postMessage({ command: 'refresh' });
        }
    }
}

let lastSeenAlertIds = new Set();
let alertInterval = null;

function startAlertMonitoring(sidebarProvider) {
    if (alertInterval) clearInterval(alertInterval);

    const checkAlerts = async () => {
        try {
            // Fetch global alerts for all databases (no dsId arg passed)
            const alerts = await fetchApi('/api/v1/alerts');
            if (!Array.isArray(alerts)) return;

            let newAlerts = [];
            for (const alert of alerts) {
                if (!lastSeenAlertIds.has(alert.id)) {
                    newAlerts.push(alert);
                    lastSeenAlertIds.add(alert.id);
                }
            }

            // Only notify on active warning/critical alerts, avoid toast spam on first load
            if (lastSeenAlertIds.size > alerts.length) {
                newAlerts.forEach(alert => {
                    const message = `[Alerta DB] ${alert.severity}: ${alert.message}`;
                    if (alert.severity === 'CRITICAL') {
                        vscode.window.showErrorMessage(message);
                    } else if (alert.severity === 'WARNING') {
                        vscode.window.showWarningMessage(message);
                    }
                });
                
                // Refresh list if DB status might have changed
                if (sidebarProvider) sidebarProvider.refresh();
            } else {
                alerts.forEach(alert => lastSeenAlertIds.add(alert.id));
            }
        } catch (e) {
            console.error('Error al verificar alertas del monitor remoto:', e);
        }
    };

    // Run first immediately, then poll every 30 seconds
    checkAlerts();
    alertInterval = setInterval(checkAlerts, 30000);
}

// SQL static analysis engine
let diagnosticCollection;

function runSqlAnalysis(document) {
    if (document.languageId !== 'sql') return;

    const text = document.getText();
    const findings = sqlAnalyzer.analyze(text);
    
    const diagnostics = findings.map(finding => {
        const range = new vscode.Range(
            finding.line, 
            finding.startChar, 
            finding.line, 
            finding.endChar
        );
        
        let severity = vscode.DiagnosticSeverity.Information;
        if (finding.severity === 'error') {
            severity = vscode.DiagnosticSeverity.Error;
        } else if (finding.severity === 'warning') {
            severity = vscode.DiagnosticSeverity.Warning;
        }

        return new vscode.Diagnostic(range, finding.message, severity);
    });

    diagnosticCollection.set(document.uri, diagnostics);
    return diagnostics.length;
}

function activate(context) {
    // Register the custom Sidebar Webview Provider
    const sidebarProvider = new DbMonitorSidebarWebviewProvider(context);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('db-monitor-sidebar-webview', sidebarProvider)
    );

    // Register URI text document provider
    const fileProvider = new DbMonitorFileProvider();
    context.subscriptions.push(
        vscode.workspace.registerTextDocumentContentProvider('db-monitor-file', fileProvider)
    );

    // Register Diagnostics collection for SQL files
    diagnosticCollection = vscode.languages.createDiagnosticCollection('db-monitor-sql');
    context.subscriptions.push(diagnosticCollection);

    // Run analysis on document events
    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument(doc => runSqlAnalysis(doc))
    );
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(doc => runSqlAnalysis(doc))
    );
    context.subscriptions.push(
        vscode.workspace.onDidCloseTextDocument(doc => diagnosticCollection.delete(doc.uri))
    );

    // Run SQL analysis on currently visible text editors on startup
    vscode.window.visibleTextEditors.forEach(editor => {
        if (editor.document) runSqlAnalysis(editor.document);
    });

    // Command: DHM: Analizar archivo SQL (manual trigger)
    context.subscriptions.push(
        vscode.commands.registerCommand('db-monitor.analyzeSql', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'sql') {
                vscode.window.showWarningMessage('Abre un archivo SQL en el editor activo para poder analizarlo.');
                return;
            }
            const count = runSqlAnalysis(editor.document);
            if (count > 0) {
                vscode.window.showWarningMessage(`Análisis SQL completado. Se encontraron ${count} problemas. Revisa el panel de Problemas.`);
            } else {
                vscode.window.showInformationMessage('Análisis SQL completado. ¡No se encontraron problemas!');
            }
            // Trigger refresh in sidebar linter view
            sidebarProvider.refresh();
        })
    );

    // Command to open file and focus on exact finding line/column (invoked by sidebar webview clicks)
    context.subscriptions.push(
        vscode.commands.registerCommand('db-monitor.openAuditFile', async (uri, line, startChar, endChar) => {
            const doc = await vscode.workspace.openTextDocument(uri);
            const editor = await vscode.window.showTextDocument(doc);
            const posStart = new vscode.Position(line, startChar);
            const posEnd = new vscode.Position(line, endChar);
            editor.selection = new vscode.Selection(posStart, posEnd);
            editor.revealRange(new vscode.Range(posStart, posEnd), vscode.TextEditorRevealType.InCenter);
        })
    );

    // Command: view configuration / log files
    context.subscriptions.push(
        vscode.commands.registerCommand('db-monitor.viewFile', async (dsId, filePath) => {
            const uri = vscode.Uri.from({
                scheme: 'db-monitor-file',
                authority: String(dsId),
                path: filePath
            });
            try {
                const doc = await vscode.workspace.openTextDocument(uri);
                await vscode.window.showTextDocument(doc, { preview: false });
            } catch (err) {
                vscode.window.showErrorMessage(`Error al abrir archivo de base de datos: ${err.message}`);
            }
        })
    );

    // Command: Force refresh database tree
    context.subscriptions.push(
        vscode.commands.registerCommand('db-monitor.refresh', () => {
            sidebarProvider.refresh();
            vscode.window.showInformationMessage('Panel del monitor actualizado.');
        })
    );

    // Command: Config connection
    context.subscriptions.push(
        vscode.commands.registerCommand('db-monitor.connect', async () => {
            const config = vscode.workspace.getConfiguration('dbMonitor');

            const currentServerUrl = config.get('serverUrl') || 'http://38.250.116.71:5000';
            const serverUrl = await vscode.window.showInputBox({
                prompt: 'URL del servidor del Monitor de Salud DB',
                value: currentServerUrl,
                placeHolder: 'ej: http://38.250.116.71:5000'
            });

            if (serverUrl === undefined) return; // User cancelled

            const currentApiKey = config.get('apiKey') || '';
            const apiKey = await vscode.window.showInputBox({
                prompt: 'API Key del Monitor (generada desde el panel web en Integraciones > API Keys)',
                value: currentApiKey,
                placeHolder: 'ej: dhm_...'
            });

            if (apiKey === undefined) return; // User cancelled

            await config.update('serverUrl', serverUrl.trim(), vscode.ConfigurationTarget.Global);
            await config.update('apiKey', apiKey.trim(), vscode.ConfigurationTarget.Global);

            vscode.window.showInformationMessage('Configuración de conexión del Monitor de Salud DB actualizada.');
            sidebarProvider.refresh();
        })
    );

    // Command: open detailed dashboard webview
    context.subscriptions.push(
        vscode.commands.registerCommand('db-monitor.viewDashboard', (item) => {
            if (!item || !item.dsId) {
                vscode.window.showErrorMessage('Selecciona una base de datos válida.');
                return;
            }

            const panel = vscode.window.createWebviewPanel(
                'dbMonitorDashboard',
                `Monitor: ${item.dsName}`,
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true
                }
            );

            const htmlPath = path.join(context.extensionPath, 'webview.html');
            let htmlContent = '';
            try {
                htmlContent = fs.readFileSync(htmlPath, 'utf8');
            } catch (err) {
                panel.webview.html = `<h3>Error al cargar la interfaz del dashboard: ${err.message}</h3>`;
                return;
            }

            htmlContent = htmlContent
                .replace('{{DATASOURCE_ID}}', String(item.dsId))
                .replace('{{DATASOURCE_NAME}}', item.dsName);

            panel.webview.html = htmlContent;

            panel.webview.onDidReceiveMessage(
                async (message) => {
                    try {
                        if (message.command === 'getMetrics') {
                            const res = await fetchApi(`/api/v1/metrics?datasource_id=${item.dsId}`);
                            panel.webview.postMessage({ command: 'metricsResult', data: res });
                        } else if (message.command === 'getFiles') {
                            const res = await fetchApi(`/api/v1/files?datasource_id=${item.dsId}`);
                            panel.webview.postMessage({ command: 'filesResult', data: res });
                        } else if (message.command === 'getAlerts') {
                            const res = await fetchApi(`/api/v1/alerts?datasource_id=${item.dsId}`);
                            panel.webview.postMessage({ command: 'alertsResult', data: res });
                        } else if (message.command === 'getHistory') {
                            const res = await fetchApi(`/api/v1/history?datasource_id=${item.dsId}`);
                            panel.webview.postMessage({ command: 'historyResult', data: res });
                        } else if (message.command === 'openFile') {
                            vscode.commands.executeCommand('db-monitor.viewFile', item.dsId, message.filePath);
                        }
                    } catch (err) {
                        panel.webview.postMessage({ command: 'error', message: err.message });
                    }
                },
                undefined,
                context.subscriptions
            );
        })
    );

    // Start background alert monitoring
    startAlertMonitoring(sidebarProvider);

    // Re-check alerts when config changes
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('dbMonitor')) {
                startAlertMonitoring(sidebarProvider);
                sidebarProvider.refresh();
            }
        })
    );
}

function deactivate() {
    if (alertInterval) clearInterval(alertInterval);
}

module.exports = {
    activate,
    deactivate
};
