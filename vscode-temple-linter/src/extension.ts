import * as vscode from 'vscode';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { createConnection, ProposedFeatures, Diagnostic as LspDiagnostic, Range as LspRange } from 'vscode-languageserver/node';
import { LanguageClient, LanguageClientOptions, ServerOptions } from 'vscode-languageclient/node';

const VIRTUAL_SCHEME = 'temple-cleaned';
const cleanedContentMap = new Map<string, string>();

// Register a content provider for virtual documents
vscode.workspace.registerTextDocumentContentProvider(VIRTUAL_SCHEME, {
  provideTextDocumentContent(uri) {
    return cleanedContentMap.get(uri.toString()) || '';
  }
});

// Handler for the custom notification from the Python LSP server
function handleCreateVirtualDocument(params: { uri: string, content: string, originalUri: string }) {
  cleanedContentMap.set(params.uri, params.content);
  // Optionally, open the document to trigger diagnostics
  vscode.workspace.openTextDocument(vscode.Uri.parse(params.uri));
}

// LSP connection setup
const connection = createConnection(ProposedFeatures.all);

// Listen for the custom notification
connection.onNotification('temple/createVirtualDocument', handleCreateVirtualDocument);

// Handler for standard LSP diagnostic requests
connection.onRequest('textDocument/diagnostic', async (params) => {
  const { textDocument } = params;
  const uri = vscode.Uri.parse(textDocument.uri);
  // Wait for diagnostics to be available
  await new Promise(resolve => setTimeout(resolve, 100));
  const diagnostics = vscode.languages.getDiagnostics(uri);

  // Convert VS Code diagnostics to LSP diagnostics
  return { diagnostics: diagnostics.map(vscDiagToLspDiag) };
});

async function getDiagnosticsForCleanedContent(cleanedContent: string, originalUri: vscode.Uri, ext: string): Promise<vscode.Diagnostic[]> {
  // 1. Try virtual document approach
  const virtualUri = vscode.Uri.parse(`${VIRTUAL_SCHEME}:/cleaned/${path.basename(originalUri.fsPath)}${ext}`);
  cleanedContentMap.set(virtualUri.toString(), cleanedContent);
  await vscode.workspace.openTextDocument(virtualUri);
  await new Promise(resolve => setTimeout(resolve, 100)); // Wait for diagnostics

  let diagnostics = vscode.languages.getDiagnostics(virtualUri);

  // 2. Fallback to temp file if no diagnostics or user triggers fallback
  if (diagnostics.length === 0 || process.env.TEMPLE_LINTER_FORCE_TEMP === '1') {
    const tempFilePath = path.join(os.tmpdir(), `temple-cleaned-${Date.now()}${ext}`);
    fs.writeFileSync(tempFilePath, cleanedContent);

    const tempUri = vscode.Uri.file(tempFilePath);
    await vscode.workspace.openTextDocument(tempUri);
    await new Promise(resolve => setTimeout(resolve, 100)); // Wait for diagnostics

    diagnostics = vscode.languages.getDiagnostics(tempUri);

    fs.unlinkSync(tempFilePath);
  }

  return diagnostics;
}

// Map VS Code DiagnosticSeverity to LSP DiagnosticSeverity (1: Error, 2: Warning, 3: Information, 4: Hint)
function mapSeverity(sev: vscode.DiagnosticSeverity | undefined): LspDiagnostic['severity'] | undefined {
  if (sev === undefined) return undefined;
  switch (sev) {
    case vscode.DiagnosticSeverity.Error: return 1;
    case vscode.DiagnosticSeverity.Warning: return 2;
    case vscode.DiagnosticSeverity.Information: return 3;
    case vscode.DiagnosticSeverity.Hint: return 4;
    default: return undefined;
  }
}

// Convert VS Code Diagnostic to LSP Diagnostic
function vscDiagToLspDiag(diag: vscode.Diagnostic): LspDiagnostic {
  return {
    range: diag.range,
    message: diag.message,
    severity: mapSeverity(diag.severity),
    code: mapCode(diag.code),
    source: diag.source,
    relatedInformation: mapRelatedInformation(diag.relatedInformation),
    tags: diag.tags,
  };

  function mapRelatedInformation(relatedInformation: vscode.DiagnosticRelatedInformation[] | undefined) {
    return relatedInformation
      ? relatedInformation.map(ri => ({
        location: {
          uri: ri.location.uri.toString(),
          range: ri.location.range
        },
        message: ri.message
      }))
      : undefined;
  }

  function mapCode(code: string | number | { value: string | number; target: vscode.Uri; } | undefined): string | number | undefined {
    return typeof code === 'object' && code !== null && 'value' in code
      ? code.value
      : code;
  }
}

function lspDiagToVscDiag(d: LspDiagnostic): vscode.Diagnostic {
  const range = toVsRange(d.range as unknown as LspRange);
  const message = d.message || '';
  const severityNum: number | undefined = d.severity;
  const severity = severityNum === 1 ? vscode.DiagnosticSeverity.Error :
    severityNum === 2 ? vscode.DiagnosticSeverity.Warning :
    severityNum === 3 ? vscode.DiagnosticSeverity.Information :
    vscode.DiagnosticSeverity.Hint;

  const diag = new vscode.Diagnostic(range, message, severity);
  if (d.source) diag.source = d.source;
  if (d.code !== undefined) diag.code = normalizeCode(d.code);
  if (d.tags) diag.tags = d.tags;
  return diag;
}

function toVsRange(range: LspRange): vscode.Range {
  return new vscode.Range(
    new vscode.Position(range.start.line, range.start.character),
    new vscode.Position(range.end.line, range.end.character)
  );
}

function normalizeCode(code: LspDiagnostic['code']): string | number | undefined {
  if (code && typeof code === 'object' && 'value' in code) {
    return code.value as string | number;
  }
  return code as string | number | undefined;
}

let client: LanguageClient;

export function activate(context: vscode.ExtensionContext) {
  // Determine Python interpreter from workspace settings
  const config = vscode.workspace.getConfiguration('python');
  // VS Code 2022+ uses 'python.defaultInterpreterPath', fallback to 'pythonPath', then 'python'
  const pythonCommand = 
    config.get<string>('defaultInterpreterPath') ||
    config.get<string>('pythonPath') ||
    'python';

  // Read temple file extensions from configuration
  const templeConfig = vscode.workspace.getConfiguration('temple');
  const templeExtensions = templeConfig.get<string[]>('fileExtensions', ['.tmpl', '.template']);

  // Path to the temple-linter package root (adjust if needed)
  const linterRoot = context.asAbsolutePath('../temple-linter');
  const serverOptions: ServerOptions = {
    command: pythonCommand,
    args: ['-m', 'temple_linter.lsp_server'],
    options: { cwd: linterRoot }
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [
      { scheme: 'file', language: 'templated-any' }
    ],
    synchronize: {
      fileEvents: vscode.workspace.createFileSystemWatcher('**/*.tmpl')
    },
    initializationOptions: {
      templeExtensions: templeExtensions
    }
  };

  client = new LanguageClient(
    'templeLsp',
    'Temple LSP',
    serverOptions,
    clientOptions
  );

  client.start().then(() => {
    // Register handler for 'temple/requestBaseDiagnostics' requests from the server
    client.onRequest('temple/requestBaseDiagnostics', async (params: { uri: string, content: string }) => {
      const { uri, content } = params;
      const virtualUri = vscode.Uri.parse(uri);
      // Register content in the cleanedContentMap for the virtual scheme
      cleanedContentMap.set(virtualUri.toString(), content);
      // Open the virtual document (triggers diagnostics)
      let doc = vscode.workspace.textDocuments.find(d => d.uri.toString() === virtualUri.toString());
      if (!doc) {
        doc = await vscode.workspace.openTextDocument(virtualUri);
      }
      // Wait for diagnostics to be available
      await new Promise(resolve => setTimeout(resolve, 100));
      // Get diagnostics for the virtual document
      const diagnostics = vscode.languages.getDiagnostics(virtualUri);
      // Convert VS Code diagnostics to LSP diagnostics
      const lspDiagnostics = diagnostics.map(vscDiagToLspDiag);
      return { diagnostics: lspDiagnostics };
    });
    // Diagnostic collection for node-attached diagnostics published by the server
    const nodeDiagCollection = vscode.languages.createDiagnosticCollection('temple-node');
    context.subscriptions.push(nodeDiagCollection);

    // Handle optional server notification to publish node-attached diagnostics
      client.onNotification('temple/publishNodeDiagnostics', (params: { uri: string; diagnostics: LspDiagnostic[] }) => {
      try {
        const uri = vscode.Uri.parse(params.uri);
        const diags = (params.diagnostics || []).map(lspDiagToVscDiag);
        nodeDiagCollection.set(uri, diags);
      } catch (e) {
        console.error('Failed to publish node diagnostics', e);
      }
    });

    context.subscriptions.push({ dispose: () => client.stop() });
  });

  // In your LSP connection setup:
  const connection = createConnection(ProposedFeatures.all);

  connection.onRequest('textDocument/diagnostic', async (params) => {
    const { textDocument, content } = params;
    const originalUri = vscode.Uri.parse(textDocument.uri);
    const ext = path.extname(originalUri.fsPath) || '.json'; // or detect from content
    const diagnostics = await getDiagnosticsForCleanedContent(content, originalUri, ext);

    return { diagnostics: diagnostics.map(vscDiagToLspDiag) };
  });
}

export function deactivate(): Thenable<void> | undefined {
  if (!client) {
    return undefined;
  }
  return client.stop();
}
