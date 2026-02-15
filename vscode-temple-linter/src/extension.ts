import * as vscode from 'vscode';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import * as crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { DEFAULT_TEMPLE_EXTENSIONS } from './defaults';
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
const EXTENSION_NAME = 'Temple Language Server';
const TEMPLE_GET_DEFAULTS_METHOD = 'temple/getDefaults';
const MIRROR_GHOST_DIRNAME = '.temple-base-lint';
const cleanedContentMap = new Map<string, string>();
const cleanedContentVersionMap = new Map<string, number>();
const tempBaseLintFileMap = new Map<string, string>();
const tempBaseLintDirectories = new Set<string>();
let baseLintStorageRoot: string | undefined;

let client: LanguageClient | undefined;

type BaseDiagnosticsRequest = {
  uri: string;
  content: string;
  detectedFormat?: string;
};

type CreateVirtualDocumentParams = {
  uri: string;
  content: string;
};

type PublishNodeDiagnosticsParams = {
  uri: string;
  diagnostics: LspDiagnostic[];
};

type TempleDefaultsResponse = {
  templeExtensions?: string[];
};

type JsonObject = Record<string, unknown>;
type BaseLintFocusMode = 'all' | 'activeTemplate';
type BaseLintStrategyMode = 'auto' | 'embedded' | 'vscode';
type BaseLintTransportStrategy = 'embedded' | 'virtual' | 'mirror-file';
type BaseLintLogLevel = 'error' | 'warn' | 'info' | 'debug' | 'trace';

type BaseLintCapabilities = {
  hasEmbeddedAdapter: boolean;
  supportsVirtualDocument: boolean;
  supportsMirrorFile: boolean;
};

type BaseLintStrategyDecision = {
  strategy: BaseLintTransportStrategy;
  reason: string;
};

type ResolveBaseLintStrategyParams = {
  mode: BaseLintStrategyMode;
  detectedFormat: string;
  capabilities: BaseLintCapabilities;
};

const LOG_LEVEL_ORDER: Record<BaseLintLogLevel, number> = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3,
  trace: 4,
};

const FORMATS_WITHOUT_RELIABLE_VIRTUAL_LINT = new Set(['md', 'markdown']);

interface BaseLintCapabilityRegistry {
  capabilitiesForFormat(format: string): BaseLintCapabilities;
}

type LanguageSuffixAssociation = {
  suffix: string;
  languageId: string;
};

class DefaultBaseLintCapabilityRegistry implements BaseLintCapabilityRegistry {
  private readonly embeddedFormatSet: Set<string>;

  constructor(embeddedFormats: string[]) {
    this.embeddedFormatSet = new Set(
      embeddedFormats.map((format) => normalizeDetectedFormat(format))
    );
  }

  capabilitiesForFormat(format: string): BaseLintCapabilities {
    const normalizedFormat = normalizeDetectedFormat(format);
    return {
      hasEmbeddedAdapter: this.embeddedFormatSet.has(normalizedFormat),
      supportsVirtualDocument:
        !FORMATS_WITHOUT_RELIABLE_VIRTUAL_LINT.has(normalizedFormat),
      supportsMirrorFile: true,
    };
  }
}

let cachedLanguageSuffixAssociations: LanguageSuffixAssociation[] | undefined;

function fileExists(filePath: string): boolean {
  try {
    return fs.statSync(filePath).isFile();
  } catch {
    return false;
  }
}

function directoryExists(dirPath: string): boolean {
  try {
    return fs.statSync(dirPath).isDirectory();
  } catch {
    return false;
  }
}

function dedupe(items: string[]): string[] {
  return [...new Set(items)];
}

function normalizeTempleExtension(extension: string): string {
  const trimmed = extension.trim();
  if (!trimmed) {
    return '';
  }
  return trimmed.startsWith('.') ? trimmed : `.${trimmed}`;
}

function hasUserConfiguredTempleExtensions(
  templeConfig: vscode.WorkspaceConfiguration
): boolean {
  const inspection = templeConfig.inspect<string[]>('fileExtensions');
  return (
    inspection?.workspaceFolderValue !== undefined ||
    inspection?.workspaceValue !== undefined ||
    inspection?.globalValue !== undefined
  );
}

function normalizeTempleExtensionsList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return dedupe(
    value
      .filter((entry): entry is string => typeof entry === 'string')
      .map((entry) => normalizeTempleExtension(entry))
      .filter(Boolean)
  );
}

function isTempleDefaultsResponse(value: unknown): value is TempleDefaultsResponse {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const maybe = value as { templeExtensions?: unknown };
  return (
    maybe.templeExtensions === undefined ||
    (Array.isArray(maybe.templeExtensions) &&
      maybe.templeExtensions.every((entry) => typeof entry === 'string'))
  );
}

function sameStringArray(left: string[], right: string[]): boolean {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((value, index) => value === right[index]);
}

async function resolveServerDefaultTempleExtensions(
  languageClient: LanguageClient,
  fallbackExtensions: string[],
  outputChannel: vscode.OutputChannel
): Promise<string[]> {
  try {
    const response = await languageClient.sendRequest(TEMPLE_GET_DEFAULTS_METHOD);
    if (!isTempleDefaultsResponse(response)) {
      outputChannel.appendLine(
        `[${EXTENSION_NAME}] '${TEMPLE_GET_DEFAULTS_METHOD}' returned invalid payload; using local defaults.`
      );
      return fallbackExtensions;
    }

    const normalized = normalizeTempleExtensionsList(response.templeExtensions);
    if (normalized.length === 0) {
      return fallbackExtensions;
    }
    return normalized;
  } catch (error) {
    outputChannel.appendLine(
      `[${EXTENSION_NAME}] Failed to resolve defaults from language server: ${String(error)}`
    );
    return fallbackExtensions;
  }
}

function buildDocumentSelector(
  templeExtensions: string[]
): Array<{ scheme: 'file'; language?: string; pattern?: string }> {
  const selector: Array<{ scheme: 'file'; language?: string; pattern?: string }> = [
    { scheme: 'file', language: 'templated-any' },
  ];

  for (const extension of templeExtensions) {
    const normalized = normalizeTempleExtension(extension);
    if (!normalized) {
      continue;
    }
    selector.push({
      scheme: 'file',
      pattern: `**/*${normalized}`,
    });
  }

  return selector;
}

function isTempleTemplateDocument(
  doc: vscode.TextDocument,
  templeExtensions: string[]
): boolean {
  const lowerPath = doc.uri.fsPath.toLowerCase();
  for (const extension of templeExtensions) {
    const normalized = normalizeTempleExtension(extension).toLowerCase();
    if (normalized && lowerPath.endsWith(normalized)) {
      return true;
    }
  }
  return false;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function workspaceRoots(): string[] {
  return (vscode.workspace.workspaceFolders || []).map(
    (folder) => folder.uri.fsPath
  );
}

function expandWorkspaceVariables(rawValue: string): string {
  let value = rawValue;
  const folders = vscode.workspace.workspaceFolders || [];

  for (const folder of folders) {
    const namedPattern = new RegExp(
      `\\$\\{workspaceFolder:${escapeRegExp(folder.name)}\\}`,
      'g'
    );
    value = value.replace(namedPattern, folder.uri.fsPath);
  }

  if (folders.length > 0) {
    value = value.replace(/\$\{workspaceFolder\}/g, folders[0].uri.fsPath);
  }

  return value;
}

function isPathLike(value: string): boolean {
  return (
    value.startsWith('~') ||
    value.startsWith('.') ||
    value.includes('/') ||
    value.includes('\\')
  );
}

function normalizePathValue(rawValue: string): string {
  const expanded = expandWorkspaceVariables(rawValue.trim());
  if (!expanded) {
    return expanded;
  }
  if (expanded === '~') {
    return os.homedir();
  }
  if (expanded.startsWith('~/')) {
    return path.join(os.homedir(), expanded.slice(2));
  }
  if (path.isAbsolute(expanded)) {
    return expanded;
  }
  if (isPathLike(expanded)) {
    const firstWorkspace = vscode.workspace.workspaceFolders?.[0];
    if (!firstWorkspace) {
      return expanded;
    }
    return path.join(firstWorkspace.uri.fsPath, expanded);
  }
  return expanded;
}

function resolvePythonCommand(
  templeConfig: vscode.WorkspaceConfiguration,
  outputChannel: vscode.OutputChannel,
  probeEnv: NodeJS.ProcessEnv
): string {
  const pythonConfig = vscode.workspace.getConfiguration('python');
  const configuredTemplePython = templeConfig.get<string>('pythonPath', '');
  const configuredDefaultPython =
    pythonConfig.get<string>('defaultInterpreterPath', '');
  const configuredLegacyPython = pythonConfig.get<string>('pythonPath', '');

  const roots = workspaceRoots();
  const searchRoots = dedupe([...roots, ...roots.map((root) => path.dirname(root))]);
  const discoveredPaths: string[] = [];
  const suffixes = [
    path.join('.ci-venv', 'bin', 'python'),
    path.join('.venv', 'bin', 'python'),
    path.join('venv', 'bin', 'python'),
    path.join('.ci-venv', 'Scripts', 'python.exe'),
    path.join('.venv', 'Scripts', 'python.exe'),
    path.join('venv', 'Scripts', 'python.exe'),
    path.join('temple-linter', '.ci-venv', 'bin', 'python'),
    path.join('temple-linter', '.venv', 'bin', 'python'),
    path.join('temple-linter', 'venv', 'bin', 'python'),
    path.join('temple-linter', '.ci-venv', 'Scripts', 'python.exe'),
    path.join('temple-linter', '.venv', 'Scripts', 'python.exe'),
    path.join('temple-linter', 'venv', 'Scripts', 'python.exe'),
  ];
  for (const root of searchRoots) {
    for (const suffix of suffixes) {
      discoveredPaths.push(path.join(root, suffix));
    }
  }

  const rawCandidates = dedupe([
    configuredTemplePython,
    ...discoveredPaths,
    configuredDefaultPython,
    configuredLegacyPython,
    'python3',
    'python',
  ]);

  let firstExistingCandidate: string | undefined;

  for (const rawCandidate of rawCandidates) {
    if (!rawCandidate || !rawCandidate.trim()) {
      continue;
    }
    const normalizedCandidate = normalizePathValue(rawCandidate);
    if (!normalizedCandidate) {
      continue;
    }

    if (isPathLike(normalizedCandidate) && !fileExists(normalizedCandidate)) {
      outputChannel.appendLine(
        `[${EXTENSION_NAME}] Skipping missing Python interpreter candidate: ${normalizedCandidate}`
      );
      continue;
    }

    if (!firstExistingCandidate) {
      firstExistingCandidate = normalizedCandidate;
    }

    const probeResult = spawnSync(
      normalizedCandidate,
      [
        '-c',
        [
          'import importlib.util as util',
          'import sys',
          'required = ("lsprotocol", "pygls", "temple_linter")',
          'missing = [name for name in required if util.find_spec(name) is None]',
          'sys.exit(0 if not missing else 1)',
        ].join('; '),
      ],
      {
        env: probeEnv,
        encoding: 'utf-8',
      }
    );

    if (probeResult.error) {
      outputChannel.appendLine(
        `[${EXTENSION_NAME}] Skipping interpreter '${normalizedCandidate}': ${probeResult.error.message}`
      );
      continue;
    }

    if (probeResult.status !== 0) {
      const probeDetails =
        probeResult.stderr?.trim() ||
        probeResult.stdout?.trim() ||
        `exit code ${String(probeResult.status)}`;
      outputChannel.appendLine(
        `[${EXTENSION_NAME}] Skipping interpreter '${normalizedCandidate}' because required modules are missing (${probeDetails}).`
      );
      continue;
    }

    outputChannel.appendLine(
      `[${EXTENSION_NAME}] Using Python interpreter: ${normalizedCandidate}`
    );
    return normalizedCandidate;
  }

  if (firstExistingCandidate) {
    outputChannel.appendLine(
      `[${EXTENSION_NAME}] No interpreter satisfied module checks; falling back to: ${firstExistingCandidate}`
    );
    return firstExistingCandidate;
  }

  outputChannel.appendLine(
    `[${EXTENSION_NAME}] No Python interpreter candidates found; falling back to: python`
  );
  return 'python';
}

function resolveServerCwd(
  context: vscode.ExtensionContext,
  templeConfig: vscode.WorkspaceConfiguration,
  outputChannel: vscode.OutputChannel
): string | undefined {
  const configuredServerRoot = templeConfig.get<string>('serverRoot', '');
  const roots = workspaceRoots();
  const candidates: string[] = [];
  if (configuredServerRoot && configuredServerRoot.trim()) {
    candidates.push(normalizePathValue(configuredServerRoot));
  }

  for (const root of roots) {
    candidates.push(root);
    candidates.push(path.join(root, 'temple-linter'));
  }
  candidates.push(path.resolve(context.extensionPath, '..', 'temple-linter'));

  const uniqueCandidates = dedupe(candidates.filter(Boolean));

  for (const candidate of uniqueCandidates) {
    const hasProjectMarkers =
      fileExists(path.join(candidate, 'pyproject.toml')) &&
      directoryExists(path.join(candidate, 'src', 'temple_linter'));
    if (hasProjectMarkers) {
      outputChannel.appendLine(`[${EXTENSION_NAME}] Using server cwd: ${candidate}`);
      return candidate;
    }
  }

  for (const candidate of uniqueCandidates) {
    if (directoryExists(candidate)) {
      outputChannel.appendLine(
        `[${EXTENSION_NAME}] Using fallback server cwd: ${candidate}`
      );
      return candidate;
    }
  }

  outputChannel.appendLine(`[${EXTENSION_NAME}] No server cwd resolved; using default process cwd`);
  return undefined;
}

function buildServerEnv(
  serverCwd: string | undefined
): NodeJS.ProcessEnv {
  const env = { ...process.env };
  const pythonPathEntries: string[] = [];

  if (serverCwd) {
    const serverSrc = path.join(serverCwd, 'src');
    if (directoryExists(serverSrc)) {
      pythonPathEntries.push(serverSrc);
    }
  }

  for (const root of workspaceRoots()) {
    const linterSrc = path.join(root, 'temple-linter', 'src');
    const coreSrc = path.join(root, 'temple', 'src');
    if (directoryExists(linterSrc)) {
      pythonPathEntries.push(linterSrc);
    }
    if (directoryExists(coreSrc)) {
      pythonPathEntries.push(coreSrc);
    }
  }

  const uniqueEntries = dedupe(pythonPathEntries);
  if (uniqueEntries.length === 0) {
    return env;
  }

  const existingPythonPath = env.PYTHONPATH;
  env.PYTHONPATH = existingPythonPath
    ? `${uniqueEntries.join(path.delimiter)}${path.delimiter}${existingPythonPath}`
    : uniqueEntries.join(path.delimiter);
  return env;
}

function isBaseDiagnosticsRequest(value: unknown): value is BaseDiagnosticsRequest {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const maybe = value as Partial<BaseDiagnosticsRequest>;
  const formatOk =
    maybe.detectedFormat === undefined || typeof maybe.detectedFormat === 'string';
  return (
    typeof maybe.uri === 'string' &&
    typeof maybe.content === 'string' &&
    formatOk
  );
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

function asJsonObject(value: unknown): JsonObject | undefined {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return undefined;
  }
  return value as JsonObject;
}

function normalizeSemanticContext(
  value: JsonObject | undefined
): JsonObject | undefined {
  if (!value) {
    return undefined;
  }
  return Object.keys(value).length > 0 ? value : undefined;
}

function stripTempleSuffixFromPath(
  fsPath: string,
  templeExtensions: string[]
): string {
  const lowerPath = fsPath.toLowerCase();
  for (const extension of templeExtensions) {
    const normalized = normalizeTempleExtension(extension).toLowerCase();
    if (!normalized) {
      continue;
    }
    if (lowerPath.endsWith(normalized)) {
      return fsPath.slice(0, fsPath.length - normalized.length);
    }
  }
  return fsPath;
}

function getLanguageSuffixAssociations(): LanguageSuffixAssociation[] {
  if (cachedLanguageSuffixAssociations) {
    return cachedLanguageSuffixAssociations;
  }

  const associations: LanguageSuffixAssociation[] = [];
  const seen = new Set<string>();

  for (const extension of vscode.extensions.all) {
    const packageJson = extension.packageJSON as
      | {
          contributes?: {
            languages?: Array<{
              id?: unknown;
              extensions?: unknown;
            }>;
          };
        }
      | undefined;
    const contributedLanguages = packageJson?.contributes?.languages ?? [];
    for (const language of contributedLanguages) {
      if (typeof language.id !== 'string') {
        continue;
      }
      const languageId = language.id;
      if (!Array.isArray(language.extensions)) {
        continue;
      }
      for (const ext of language.extensions) {
        if (typeof ext !== 'string') {
          continue;
        }
        const suffix = ext.trim().toLowerCase();
        if (!suffix.startsWith('.')) {
          continue;
        }
        const key = `${languageId}::${suffix}`;
        if (seen.has(key)) {
          continue;
        }
        seen.add(key);
        associations.push({ suffix, languageId });
      }
    }
  }

  associations.sort((a, b) => b.suffix.length - a.suffix.length);
  cachedLanguageSuffixAssociations = associations;
  return associations;
}

function preferredBaseLanguageIdForTemplatePath(
  fsPath: string,
  templeExtensions: string[]
): string | undefined {
  const strippedPath = stripTempleSuffixFromPath(fsPath, templeExtensions);
  const lowerPath = strippedPath.toLowerCase();
  for (const association of getLanguageSuffixAssociations()) {
    if (lowerPath.endsWith(association.suffix)) {
      return association.languageId;
    }
  }
  return undefined;
}

async function ensurePreferredTemplateLanguage(
  doc: vscode.TextDocument,
  templeExtensions: string[],
  outputChannel: vscode.OutputChannel
): Promise<void> {
  if (doc.uri.scheme !== 'file') {
    return;
  }
  if (!isTempleTemplateDocument(doc, templeExtensions)) {
    return;
  }

  const preferredLanguage = preferredBaseLanguageIdForTemplatePath(
    doc.uri.fsPath,
    templeExtensions
  );
  if (!preferredLanguage || doc.languageId === preferredLanguage) {
    return;
  }

  try {
    await vscode.languages.setTextDocumentLanguage(doc, preferredLanguage);
    outputChannel.appendLine(
      `[${EXTENSION_NAME}] Re-associated '${doc.uri.fsPath}' to '${preferredLanguage}' for base-language highlighting.`
    );
  } catch (error) {
    outputChannel.appendLine(
      `[${EXTENSION_NAME}] Failed to re-associate '${doc.uri.fsPath}' to '${preferredLanguage}': ${String(error)}`
    );
  }
}

function resolveWorkspacePath(rawPath: string): string {
  const normalized = normalizePathValue(rawPath);
  if (path.isAbsolute(normalized)) {
    return normalized;
  }
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    return normalized;
  }
  return path.join(workspaceFolder.uri.fsPath, normalized);
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
  virtualUri: vscode.Uri,
  expectedVersion: number
): Promise<vscode.Diagnostic[]> {
  const uriKey = virtualUri.toString();
  if ((cleanedContentVersionMap.get(uriKey) ?? 0) !== expectedVersion) {
    return [];
  }

  await vscode.workspace.openTextDocument(virtualUri);

  await new Promise<void>((resolve) => {
    let settled = false;
    let settleTimer: NodeJS.Timeout | undefined;

    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      if (settleTimer) {
        clearTimeout(settleTimer);
      }
      clearTimeout(timeoutTimer);
      diagnosticsSub.dispose();
      resolve();
    };

    const diagnosticsSub = vscode.languages.onDidChangeDiagnostics((event) => {
      if (!event.uris.some((uri) => uri.toString() === uriKey)) {
        return;
      }
      if ((cleanedContentVersionMap.get(uriKey) ?? 0) !== expectedVersion) {
        finish();
        return;
      }
      if (settleTimer) {
        clearTimeout(settleTimer);
      }
      settleTimer = setTimeout(finish, 25);
    });

    const timeoutTimer = setTimeout(finish, 350);
  });

  if ((cleanedContentVersionMap.get(uriKey) ?? 0) !== expectedVersion) {
    return [];
  }

  return vscode.languages.getDiagnostics(virtualUri);
}

function normalizeDetectedFormat(format: string | undefined): string {
  return (format || '').trim().toLowerCase();
}

function normalizeBaseLintStrategyMode(
  mode: string | undefined
): BaseLintStrategyMode {
  if (mode === 'embedded' || mode === 'vscode') {
    return mode;
  }
  return 'auto';
}

function normalizeBaseLintLogLevel(
  level: string | undefined
): BaseLintLogLevel {
  if (
    level === 'error' ||
    level === 'warn' ||
    level === 'info' ||
    level === 'debug' ||
    level === 'trace'
  ) {
    return level;
  }
  return 'warn';
}

function shouldLogBaseLint(
  configuredLevel: BaseLintLogLevel,
  messageLevel: BaseLintLogLevel
): boolean {
  return LOG_LEVEL_ORDER[messageLevel] <= LOG_LEVEL_ORDER[configuredLevel];
}

export function resolveBaseLintStrategy(
  params: ResolveBaseLintStrategyParams
): BaseLintStrategyDecision {
  const { mode, detectedFormat, capabilities } = params;
  const formatLabel = detectedFormat || 'unknown';
  const preferEmbedded = mode === 'auto' || mode === 'embedded';

  if (preferEmbedded && capabilities.hasEmbeddedAdapter) {
    return {
      strategy: 'embedded',
      reason: `embedded adapter registered for ${formatLabel}`,
    };
  }

  if (capabilities.supportsVirtualDocument) {
    return {
      strategy: 'virtual',
      reason:
        mode === 'vscode'
          ? `vscode mode selected virtual strategy for ${formatLabel}`
          : `no embedded adapter available for ${formatLabel}; using virtual strategy`,
    };
  }

  if (capabilities.supportsMirrorFile) {
    return {
      strategy: 'mirror-file',
      reason: `virtual strategy unsupported for ${formatLabel}; using mirror-file fallback`,
    };
  }

  return {
    strategy: 'virtual',
    reason: `no explicit capabilities for ${formatLabel}; using virtual fallback`,
  };
}

function extensionForDetectedFormat(format: string): string {
  switch (format) {
    case 'md':
    case 'markdown':
      return '.md';
    case 'json':
      return '.json';
    case 'yaml':
      return '.yaml';
    case 'xml':
      return '.xml';
    case 'html':
      return '.html';
    case 'toml':
      return '.toml';
    default:
      return '.txt';
  }
}

function stableTempPathFor(originalUri: vscode.Uri, fileExtension: string): string {
  const hash = crypto
    .createHash('sha1')
    .update(originalUri.toString())
    .digest('hex')
    .slice(0, 16);
  const root = baseLintStorageRoot ?? path.join(os.tmpdir(), MIRROR_GHOST_DIRNAME);
  fs.mkdirSync(root, { recursive: true });
  tempBaseLintDirectories.add(root);
  return path.join(root, `${hash}${fileExtension}`);
}

function resolveMirrorFileTargetUri(
  originalUri: vscode.Uri,
  detectedFormat: string
): vscode.Uri {
  const existing = tempBaseLintFileMap.get(originalUri.toString());
  if (existing) {
    return vscode.Uri.file(existing);
  }

  const ext = extensionForDetectedFormat(detectedFormat);
  const hash = crypto
    .createHash('sha1')
    .update(originalUri.toString())
    .digest('hex')
    .slice(0, 16);
  let mirrorPath: string;
  if (originalUri.scheme === 'file') {
    const sourceDir = path.dirname(originalUri.fsPath);
    const mirrorDir = path.join(sourceDir, MIRROR_GHOST_DIRNAME);
    fs.mkdirSync(mirrorDir, { recursive: true });
    tempBaseLintDirectories.add(mirrorDir);
    mirrorPath = path.join(mirrorDir, `${hash}${ext}`);
  } else {
    mirrorPath = stableTempPathFor(originalUri, ext);
  }

  tempBaseLintFileMap.set(originalUri.toString(), mirrorPath);
  return vscode.Uri.file(mirrorPath);
}

function cleanupMirrorFileTargetUri(targetUri: vscode.Uri): void {
  if (targetUri.scheme !== 'file') {
    return;
  }
  try {
    if (fileExists(targetUri.fsPath)) {
      fs.unlinkSync(targetUri.fsPath);
    }
  } catch {
    // Best effort cleanup.
  }
}

function cleanupMirrorDirectories(): void {
  const dirs = [...tempBaseLintDirectories].sort(
    (a, b) => b.length - a.length
  );
  for (const dirPath of dirs) {
    try {
      if (!directoryExists(dirPath)) {
        continue;
      }
      const entries = fs.readdirSync(dirPath);
      if (entries.length === 0) {
        fs.rmdirSync(dirPath);
      }
    } catch {
      // Best effort cleanup.
    }
  }
}

function resetBaseLintSessionCaches(): void {
  cleanedContentMap.clear();
  cleanedContentVersionMap.clear();
  tempBaseLintFileMap.clear();
  tempBaseLintDirectories.clear();
  cachedLanguageSuffixAssociations = undefined;
}

export async function activate(
  context: vscode.ExtensionContext
): Promise<{ __testing: typeof __testing }> {
  const outputChannel = vscode.window.createOutputChannel(EXTENSION_NAME);
  context.subscriptions.push(outputChannel);
  outputChannel.appendLine(`[${EXTENSION_NAME}] Activating extension`);

  const virtualDocumentChangeEmitter = new vscode.EventEmitter<vscode.Uri>();
  context.subscriptions.push(virtualDocumentChangeEmitter);

  const providerDisposable = vscode.workspace.registerTextDocumentContentProvider(
    VIRTUAL_SCHEME,
    {
      onDidChange: virtualDocumentChangeEmitter.event,
      provideTextDocumentContent(uri) {
        return cleanedContentMap.get(uri.toString()) || '';
      },
    }
  );
  context.subscriptions.push(providerDisposable);

  const templeConfig = vscode.workspace.getConfiguration('temple');
  const userConfiguredTempleExtensions =
    hasUserConfiguredTempleExtensions(templeConfig);
  const templeExtensions = templeConfig.get<string[]>(
    'fileExtensions',
    DEFAULT_TEMPLE_EXTENSIONS
  );
  const normalizedTempleExtensions = dedupe(
    templeExtensions.map((ext) => normalizeTempleExtension(ext)).filter(Boolean)
  );
  let effectiveTempleExtensions = [...normalizedTempleExtensions];
  const semanticContext = normalizeSemanticContext(
    asJsonObject(templeConfig.get<unknown>('semanticContext'))
  );
  const semanticSchemaPathRaw = templeConfig.get<string>(
    'semanticSchemaPath',
    ''
  );
  const baseLintDebounceSeconds = templeConfig.get<number>(
    'baseLintDebounceSeconds',
    0.8
  );
  const traceBaseLintDiagnosticsLegacy = templeConfig.get<boolean>(
    'traceBaseLintDiagnostics',
    false
  );
  const baseLintLogLevel = normalizeBaseLintLogLevel(
    templeConfig.get<string>('baseLintLogLevel', 'warn')
  );
  const effectiveBaseLintLogLevel: BaseLintLogLevel =
    traceBaseLintDiagnosticsLegacy && baseLintLogLevel !== 'trace'
      ? 'trace'
      : baseLintLogLevel;
  const baseLintStrategyMode = normalizeBaseLintStrategyMode(
    templeConfig.get<string>('baseLintStrategyMode', 'auto')
  );
  const embeddedBaseLintFormats = templeConfig.get<string[]>(
    'embeddedBaseLintFormats',
    []
  );
  const capabilityRegistry = new DefaultBaseLintCapabilityRegistry(
    embeddedBaseLintFormats
  );
  const baseLintFocusMode = templeConfig.get<BaseLintFocusMode>(
    'baseLintFocusMode',
    templeConfig.get<BaseLintFocusMode>(
      // Backward compatibility for prior setting name.
      'markdownBaseLintFocusMode',
      'all'
    )
  );
  resetBaseLintSessionCaches();
  const storageRootCandidate =
    context.storageUri?.fsPath ?? context.globalStorageUri?.fsPath;
  if (storageRootCandidate) {
    baseLintStorageRoot = path.join(storageRootCandidate, 'temple-base-lint');
    fs.mkdirSync(baseLintStorageRoot, { recursive: true });
  }
  outputChannel.appendLine(
    `[${EXTENSION_NAME}] Base lint mode=${baseLintStrategyMode} focus=${baseLintFocusMode} logLevel=${effectiveBaseLintLogLevel}`
  );
  const semanticSchemaPath = semanticSchemaPathRaw
    ? resolveWorkspacePath(semanticSchemaPathRaw)
    : undefined;
  const semanticSchema = semanticSchemaPath
    ? loadSemanticSchema(semanticSchemaPath)
    : undefined;

  const fileWatchers = effectiveTempleExtensions.map((extension) =>
    vscode.workspace.createFileSystemWatcher(`**/*${extension}`)
  );
  context.subscriptions.push(...fileWatchers);

  for (const doc of vscode.workspace.textDocuments) {
    void ensurePreferredTemplateLanguage(
      doc,
      effectiveTempleExtensions,
      outputChannel
    );
  }

  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument((doc) => {
      void ensurePreferredTemplateLanguage(
        doc,
        effectiveTempleExtensions,
        outputChannel
      );
      if (
        isTempleTemplateDocument(doc, effectiveTempleExtensions) &&
        doc.languageId !== 'templated-any'
      ) {
        outputChannel.appendLine(
          `[${EXTENSION_NAME}] '${doc.uri.fsPath}' opened as '${doc.languageId}'. Temple will still lint by filename pattern.`
        );
      }
    })
  );

  const linterRoot = resolveServerCwd(context, templeConfig, outputChannel);
  const serverEnv = buildServerEnv(linterRoot);
  const pythonCommand = resolvePythonCommand(
    templeConfig,
    outputChannel,
    serverEnv
  );
  outputChannel.appendLine(
    `[${EXTENSION_NAME}] Starting language server: ${pythonCommand} -m temple_linter.lsp_server`
  );
  const serverOptions: ServerOptions = {
    command: pythonCommand,
    args: ['-m', 'temple_linter.lsp_server'],
    options: { cwd: linterRoot, env: serverEnv },
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: buildDocumentSelector(effectiveTempleExtensions),
    synchronize: { fileEvents: fileWatchers },
    outputChannel,
    initializationOptions: {
      ...(userConfiguredTempleExtensions
        ? { templeExtensions: effectiveTempleExtensions }
        : {}),
      semanticContext: semanticContext ?? null,
      semanticSchema,
      semanticSchemaPath,
      baseLintDebounceSeconds,
      baseLintStrategyMode,
      embeddedBaseLintFormats,
    },
  };

  client = new LanguageClient(
    'templeLsp',
    EXTENSION_NAME,
    serverOptions,
    clientOptions
  );

  const nodeDiagCollection =
    vscode.languages.createDiagnosticCollection('temple-node');
  context.subscriptions.push(nodeDiagCollection);

  try {
    await client.start();
    outputChannel.appendLine(`[${EXTENSION_NAME}] Language server started`);
    if (!userConfiguredTempleExtensions) {
      const serverDefaultTempleExtensions = await resolveServerDefaultTempleExtensions(
        client,
        effectiveTempleExtensions,
        outputChannel
      );
      if (!sameStringArray(serverDefaultTempleExtensions, effectiveTempleExtensions)) {
        effectiveTempleExtensions = serverDefaultTempleExtensions;
        outputChannel.appendLine(
          `[${EXTENSION_NAME}] Using temple extensions from language server defaults: ${effectiveTempleExtensions.join(', ')}`
        );
        for (const doc of vscode.workspace.textDocuments) {
          void ensurePreferredTemplateLanguage(
            doc,
            effectiveTempleExtensions,
            outputChannel
          );
        }
      }
    }
  } catch (error) {
    outputChannel.appendLine(
      `[${EXTENSION_NAME}] Failed to start language server: ${String(error)}`
    );
    void vscode.window.showErrorMessage(
      `${EXTENSION_NAME} failed to start. See Output -> ${EXTENSION_NAME} for details.`
    );
    throw error;
  }

  client.onRequest(
    'temple/requestBaseDiagnostics',
    async (params: unknown): Promise<{ diagnostics: LspDiagnostic[] }> => {
      if (!isBaseDiagnosticsRequest(params)) {
        return { diagnostics: [] };
      }

      const originalUri = vscode.Uri.parse(params.uri);
      const normalizedFormat = normalizeDetectedFormat(params.detectedFormat);
      if (baseLintFocusMode === 'activeTemplate') {
        const activeUri = vscode.window.activeTextEditor?.document.uri.toString();
        if (!activeUri || activeUri !== originalUri.toString()) {
          return { diagnostics: [] };
        }
      }
      const strategyDecision = resolveBaseLintStrategy({
        mode: baseLintStrategyMode,
        detectedFormat: normalizedFormat,
        capabilities: capabilityRegistry.capabilitiesForFormat(normalizedFormat),
      });

      if (strategyDecision.strategy === 'embedded') {
        if (shouldLogBaseLint(effectiveBaseLintLogLevel, 'debug')) {
          outputChannel.appendLine(
            `[${EXTENSION_NAME}] Base lint strategy=embedded for ${originalUri.toString()} (${normalizedFormat || 'unknown'}): ${strategyDecision.reason}; expecting embedded diagnostics from linter`
          );
        }
        return { diagnostics: [] };
      }

      const targetUri =
        strategyDecision.strategy === 'mirror-file'
          ? resolveMirrorFileTargetUri(originalUri, normalizedFormat)
          : originalUri.with({ scheme: VIRTUAL_SCHEME });
      const uriKey = targetUri.toString();
      const nextVersion = (cleanedContentVersionMap.get(uriKey) ?? 0) + 1;
      cleanedContentVersionMap.set(uriKey, nextVersion);
      try {
        if (strategyDecision.strategy === 'mirror-file') {
          fs.writeFileSync(targetUri.fsPath, params.content, 'utf8');
        } else {
          cleanedContentMap.set(uriKey, params.content);
          virtualDocumentChangeEmitter.fire(targetUri);
        }

        const diagnostics = await collectDiagnosticsForVirtualUri(
          targetUri,
          nextVersion
        );
        if (shouldLogBaseLint(effectiveBaseLintLogLevel, 'trace')) {
          const sources = dedupe(
            diagnostics
              .map((diag) => (diag.source ?? '').trim())
              .filter((source) => source.length > 0)
          );
          outputChannel.appendLine(
            `[${EXTENSION_NAME}] Base lint strategy=${strategyDecision.strategy} target=${targetUri.toString()} (${normalizedFormat || 'unknown'}) -> ${diagnostics.length} diagnostics` +
              ` [reason: ${strategyDecision.reason}]` +
              ` [publish-uri: ${originalUri.toString()}]` +
              (sources.length ? ` [sources: ${sources.join(', ')}]` : '')
          );
        }
        return { diagnostics: diagnostics.map(vscDiagToLspDiag) };
      } finally {
        if (strategyDecision.strategy === 'mirror-file') {
          cleanupMirrorFileTargetUri(targetUri);
          cleanupMirrorDirectories();
        }
      }
    }
  );

  client.onNotification('temple/createVirtualDocument', async (params: unknown) => {
    if (!isCreateVirtualDocumentParams(params)) {
      return;
    }

    const uri = vscode.Uri.parse(params.uri);
    const uriKey = uri.toString();
    const nextVersion = (cleanedContentVersionMap.get(uriKey) ?? 0) + 1;
    cleanedContentVersionMap.set(uriKey, nextVersion);
    cleanedContentMap.set(uriKey, params.content);
    virtualDocumentChangeEmitter.fire(uri);
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

  return { __testing };
}

export const __testing = {
  normalizeDetectedFormat,
  resolveBaseLintStrategy,
  DefaultBaseLintCapabilityRegistry,
  resolveMirrorFileTargetUri,
  cleanupMirrorFileTargetUri,
  MIRROR_GHOST_DIRNAME,
};

export function deactivate(): Thenable<void> | undefined {
  for (const mirrorPath of tempBaseLintFileMap.values()) {
    cleanupMirrorFileTargetUri(vscode.Uri.file(mirrorPath));
  }
  cleanupMirrorDirectories();
  resetBaseLintSessionCaches();
  if (!client) {
    return undefined;
  }
  return client.stop();
}
