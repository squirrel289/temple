import * as vscode from 'vscode';
import * as fs from 'node:fs';
import * as path from 'node:path';
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
} from 'vscode-languageclient/node';
import {
  Diagnostic as LspDiagnostic,
  Range as LspRange,
} from 'vscode-languageserver/node';

const VIRTUAL_SCHEME = 'temple-cleaned';
const cleanedContentMap = new Map<string, string>();

let client: LanguageClient | undefined;

type BaseDiagnosticsRequest = {
  uri: string;
  content: string;
};

type CreateVirtualDocumentParams = {
  uri: string;
  content: string;
};

type PublishNodeDiagnosticsParams = {
  uri: string;
  diagnostics: LspDiagnostic[];
};

type JsonObject = Record<string, unknown>;

function isBaseDiagnosticsRequest(value: unknown): value is BaseDiagnosticsRequest {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const maybe = value as Partial<BaseDiagnosticsRequest>;
  return typeof maybe.uri === 'string' && typeof maybe.content === 'string';
}

function isCreateVirtualDocumentParams(
  value: unknown
): value is CreateVirtualDocumentParams {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const maybe = value as Partial<CreateVirtualDocumentParams>;
  return typeof maybe.uri === 'string' && typeof maybe.content === 'string';
}

function isPublishNodeDiagnosticsParams(
  value: unknown
): value is PublishNodeDiagnosticsParams {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const maybe = value as Partial<PublishNodeDiagnosticsParams>;
  return (
    typeof maybe.uri === 'string' &&
    Array.isArray(maybe.diagnostics)
  );
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function asJsonObject(value: unknown): JsonObject | undefined {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return undefined;
  }
  return value as JsonObject;
}

function resolveWorkspacePath(rawPath: string): string {
  if (path.isAbsolute(rawPath)) {
    return rawPath;
  }
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    return rawPath;
  }
  return path.join(workspaceFolder.uri.fsPath, rawPath);
}

function loadSemanticSchema(schemaPath: string): JsonObject | undefined {
  const resolved = resolveWorkspacePath(schemaPath);
  try {
    const schemaText = fs.readFileSync(resolved, 'utf-8');
    const parsed = JSON.parse(schemaText) as unknown;
    return asJsonObject(parsed);
  } catch (error) {
    console.warn(`Failed to load temple semantic schema from '${resolved}':`, error);
    return undefined;
  }
}

function toVsRange(range: LspRange): vscode.Range {
  return new vscode.Range(
    new vscode.Position(range.start.line, range.start.character),
    new vscode.Position(range.end.line, range.end.character)
  );
}

function normalizeCode(code: unknown): string | number | undefined {
  if (typeof code === 'string' || typeof code === 'number') {
    return code;
  }
  if (code && typeof code === 'object' && 'value' in code) {
    const value = (code as { value?: unknown }).value;
    if (typeof value === 'string' || typeof value === 'number') {
      return value;
    }
  }
  return undefined;
}

function mapSeverity(
  severity: vscode.DiagnosticSeverity | undefined
): LspDiagnostic['severity'] | undefined {
  if (severity === undefined) {
    return undefined;
  }

  switch (severity) {
    case vscode.DiagnosticSeverity.Error:
      return 1;
    case vscode.DiagnosticSeverity.Warning:
      return 2;
    case vscode.DiagnosticSeverity.Information:
      return 3;
    case vscode.DiagnosticSeverity.Hint:
      return 4;
    default:
      return undefined;
  }
}

function vscDiagToLspDiag(diag: vscode.Diagnostic): LspDiagnostic {
  const relatedInformation = diag.relatedInformation?.map((ri) => ({
    location: {
      uri: ri.location.uri.toString(),
      range: ri.location.range,
    },
    message: ri.message,
  }));

  return {
    range: diag.range,
    message: diag.message,
    severity: mapSeverity(diag.severity),
    code: normalizeCode(diag.code),
    source: diag.source,
    relatedInformation,
    tags: diag.tags,
  };
}

function lspDiagToVscDiag(diag: LspDiagnostic): vscode.Diagnostic {
  const range = toVsRange(diag.range as unknown as LspRange);
  const severity =
    diag.severity === 1
      ? vscode.DiagnosticSeverity.Error
      : diag.severity === 2
      ? vscode.DiagnosticSeverity.Warning
      : diag.severity === 3
      ? vscode.DiagnosticSeverity.Information
      : vscode.DiagnosticSeverity.Hint;

  const vscodeDiagnostic = new vscode.Diagnostic(
    range,
    diag.message || '',
    severity
  );

  if (diag.source) {
    vscodeDiagnostic.source = diag.source;
  }
  if (diag.code !== undefined) {
    vscodeDiagnostic.code = normalizeCode(diag.code);
  }
  if (diag.tags) {
    vscodeDiagnostic.tags = diag.tags;
  }

  return vscodeDiagnostic;
}

async function collectDiagnosticsForVirtualUri(
  virtualUri: vscode.Uri
): Promise<vscode.Diagnostic[]> {
  await vscode.workspace.openTextDocument(virtualUri);
  await wait(100);
  return vscode.languages.getDiagnostics(virtualUri);
}

export async function activate(
  context: vscode.ExtensionContext
): Promise<void> {
  const providerDisposable = vscode.workspace.registerTextDocumentContentProvider(
    VIRTUAL_SCHEME,
    {
      provideTextDocumentContent(uri) {
        return cleanedContentMap.get(uri.toString()) || '';
      },
    }
  );
  context.subscriptions.push(providerDisposable);

  const pythonConfig = vscode.workspace.getConfiguration('python');
  const pythonCommand =
    pythonConfig.get<string>('defaultInterpreterPath') ||
    pythonConfig.get<string>('pythonPath') ||
    'python';

  const templeConfig = vscode.workspace.getConfiguration('temple');
  const templeExtensions = templeConfig.get<string[]>(
    'fileExtensions',
    ['.tmpl', '.template']
  );
  const semanticContext = asJsonObject(
    templeConfig.get<unknown>('semanticContext')
  );
  const semanticSchemaPathRaw = templeConfig.get<string>(
    'semanticSchemaPath',
    ''
  );
  const semanticSchemaPath = semanticSchemaPathRaw
    ? resolveWorkspacePath(semanticSchemaPathRaw)
    : undefined;
  const semanticSchema = semanticSchemaPath
    ? loadSemanticSchema(semanticSchemaPath)
    : undefined;

  const fileWatchers = templeExtensions.map((extension) =>
    vscode.workspace.createFileSystemWatcher(`**/*${extension}`)
  );
  context.subscriptions.push(...fileWatchers);

  const linterRoot = context.asAbsolutePath('../temple-linter');
  const serverOptions: ServerOptions = {
    command: pythonCommand,
    args: ['-m', 'temple_linter.lsp_server'],
    options: { cwd: linterRoot },
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [{ scheme: 'file', language: 'templated-any' }],
    synchronize: { fileEvents: fileWatchers },
    initializationOptions: {
      templeExtensions,
      semanticContext,
      semanticSchema,
      semanticSchemaPath,
    },
  };

  client = new LanguageClient(
    'templeLsp',
    'Temple LSP',
    serverOptions,
    clientOptions
  );

  const nodeDiagCollection =
    vscode.languages.createDiagnosticCollection('temple-node');
  context.subscriptions.push(nodeDiagCollection);

  await client.start();

  client.onRequest(
    'temple/requestBaseDiagnostics',
    async (params: unknown): Promise<{ diagnostics: LspDiagnostic[] }> => {
      if (!isBaseDiagnosticsRequest(params)) {
        return { diagnostics: [] };
      }

      const originalUri = vscode.Uri.parse(params.uri);
      const virtualUri = originalUri.with({ scheme: VIRTUAL_SCHEME });
      cleanedContentMap.set(virtualUri.toString(), params.content);

      const diagnostics = await collectDiagnosticsForVirtualUri(virtualUri);
      return { diagnostics: diagnostics.map(vscDiagToLspDiag) };
    }
  );

  client.onNotification('temple/createVirtualDocument', async (params: unknown) => {
    if (!isCreateVirtualDocumentParams(params)) {
      return;
    }

    const uri = vscode.Uri.parse(params.uri);
    cleanedContentMap.set(uri.toString(), params.content);
    await vscode.workspace.openTextDocument(uri);
  });

  client.onNotification(
    'temple/publishNodeDiagnostics',
    (params: unknown) => {
      if (!isPublishNodeDiagnosticsParams(params)) {
        return;
      }

      const uri = vscode.Uri.parse(params.uri);
      const diagnostics = params.diagnostics.map(lspDiagToVscDiag);
      nodeDiagCollection.set(uri, diagnostics);
    }
  );
}

export function deactivate(): Thenable<void> | undefined {
  if (!client) {
    return undefined;
  }
  return client.stop();
}
