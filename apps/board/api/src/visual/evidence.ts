import { mkdirSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { CardDTO } from '@prime-board/shared';

export interface VisualArtifact {
  kind: 'screenshot' | 'video';
  name: string;
  path: string;
  viewport?: { width: number; height: number };
  url?: string;
}

export interface VisualEvidenceResult {
  required: boolean;
  artifacts: VisualArtifact[];
  error?: string;
}

const boardRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const frontendExtensions = /\.(css|scss|sass|less|tsx|jsx|svg|png|jpe?g|webp|gif)$/i;
const frontendPathMarkers = [
  /(^|\/)app\//,
  /(^|\/)pages\//,
  /(^|\/)components\//,
  /(^|\/)web\/src\//,
  /(^|\/)src\/components\//,
  /(^|\/)src\/app\//,
  /(^|\/)src\/pages\//
];
const nonEvidenceMarkers = [
  /(^|\/)__tests__\//,
  /(^|\/)tests?\//,
  /\.test\.[jt]sx?$/i,
  /\.spec\.[jt]sx?$/i
];

export function requiresVisualEvidence(changedFiles: string[]): boolean {
  return changedFiles.some((file) => {
    if (nonEvidenceMarkers.some((pattern) => pattern.test(file))) return false;
    return frontendExtensions.test(file) && frontendPathMarkers.some((pattern) => pattern.test(file));
  });
}

export function captureVisualEvidence(card: CardDTO, changedFiles: string[]): VisualEvidenceResult {
  if (!requiresVisualEvidence(changedFiles)) return { required: false, artifacts: [] };
  if (!card.worktreePath) return { required: true, artifacts: [], error: 'Frontend files changed but the card has no worktree path.' };
  if (process.env.BOARD_VISUAL_EVIDENCE_MODE === 'fake') return fakeArtifacts(card);

  const result = spawnSync(process.execPath, [
    resolve(boardRoot, 'scripts/capture-visual-evidence.mjs'),
    '--worktree',
    card.worktreePath,
    '--card-id',
    card.id
  ], { cwd: boardRoot, encoding: 'utf8', timeout: Number(process.env.BOARD_VISUAL_EVIDENCE_TIMEOUT_MS ?? 120000) });

  if (result.status !== 0) {
    const output = `${result.stderr}\n${result.stdout}`.trim();
    return { required: true, artifacts: [], error: output || `visual evidence capture exited ${result.status}` };
  }

  try {
    const parsed = JSON.parse(result.stdout) as { artifacts?: VisualArtifact[] };
    const artifacts = parsed.artifacts ?? [];
    if (artifacts.length === 0) return { required: true, artifacts: [], error: 'Frontend files changed but no visual artifacts were produced.' };
    return { required: true, artifacts };
  } catch {
    return { required: true, artifacts: [], error: 'Visual evidence capture returned invalid JSON.' };
  }
}

function fakeArtifacts(card: CardDTO): VisualEvidenceResult {
  const dir = resolve(process.env.BOARD_VISUAL_EVIDENCE_ARTIFACT_ROOT ?? resolve(boardRoot, 'artifacts/cards'), card.id, 'visual');
  mkdirSync(dir, { recursive: true });
  const desktop = resolve(dir, 'desktop.txt');
  const mobile = resolve(dir, 'mobile.txt');
  writeFileSync(desktop, 'fake desktop visual evidence\n');
  writeFileSync(mobile, 'fake mobile visual evidence\n');
  return {
    required: true,
    artifacts: [
      { kind: 'screenshot', name: 'desktop', path: desktop, viewport: { width: 1440, height: 900 } },
      { kind: 'screenshot', name: 'mobile', path: mobile, viewport: { width: 390, height: 844 } }
    ]
  };
}
