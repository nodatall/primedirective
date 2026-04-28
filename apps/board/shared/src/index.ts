export const CARD_STATUSES = ['Inbox', 'Queued', 'Running', 'Blocked', 'PR Ready', 'Checks Pending', 'Merging', 'Merged', 'Done', 'Abandoned'] as const;
export type CardStatus = (typeof CARD_STATUSES)[number];

export const TASK_TYPES = ['Quick', 'Planned'] as const;
export type TaskType = (typeof TASK_TYPES)[number];

export const BLOCKER_REASONS = [
  'no_changes_detected',
  'collision_detected',
  'existing_pr_ambiguous',
  'checks_absent',
  'protected_risk',
  'runner_failed',
  'approval_required',
  'cleanup_blocked',
  'restart_quarantined',
  'origin_rejected',
  'planned_skill_unavailable'
] as const;
export type BlockerReason = (typeof BLOCKER_REASONS)[number];

export const RUN_EVENT_TYPES = ['status_transition', 'log', 'blocker', 'prompt_preview', 'runner_json', 'pr', 'system'] as const;
export type RunEventType = (typeof RUN_EVENT_TYPES)[number];

export interface RepoDTO {
  id: string;
  name: string;
  path: string;
  defaultBranch: string;
  remoteUrl?: string;
}

export interface CardDTO {
  id: string;
  repoId: string;
  title: string;
  instructions: string;
  taskType: TaskType;
  autoMerge: boolean;
  status: CardStatus;
  branch?: string;
  worktreePath?: string;
  pr?: PullRequestDTO;
  blockerReason?: BlockerReason;
  blockerSummary?: string;
  overridePaused?: boolean;
  updatedAt: string;
}

export interface RunDTO {
  id: string;
  cardId: string;
  attempt: number;
  phase: string;
  status: 'ready' | 'running' | 'succeeded' | 'failed' | 'blocked' | 'stalled' | 'canceled';
  startedAt?: string;
  endedAt?: string;
  exitCode?: number | null;
  promptPreview?: string;
}

export interface PullRequestDTO {
  number: number;
  url: string;
  state: 'OPEN' | 'CLOSED' | 'MERGED';
  headRefOid?: string;
  mergeable?: 'MERGEABLE' | 'CONFLICTING' | 'UNKNOWN';
  mergeStateStatus?: string;
  checksState?: 'pending' | 'passed' | 'failed' | 'absent';
  isDraft?: boolean;
  mergedAt?: string | null;
}

export interface RunEventDTO {
  id: string;
  runId: string;
  cardId: string;
  type: RunEventType;
  timestamp: string;
  message: string;
  metadata?: Record<string, unknown>;
}

export interface StatusTransitionEvent extends RunEventDTO {
  type: 'status_transition';
  metadata: { from: CardStatus; to: CardStatus; reason?: string };
}

export interface LogEvent extends RunEventDTO {
  type: 'log';
  metadata: { stream: 'stdout' | 'stderr' | 'system' };
}

export interface BlockerEvent extends RunEventDTO {
  type: 'blocker';
  metadata: { reason: BlockerReason; exitCode?: number | null; excerpt?: string };
}

export interface PromptPreviewEvent extends RunEventDTO {
  type: 'prompt_preview';
  metadata: { promptPreview: string };
}

export interface StreamCursor {
  afterEventId?: string;
}

export interface WorkflowOverride {
  allowQuickNoCheckAutomerge?: boolean;
  maxActiveRuns?: number;
  maxActiveCardsPerRepo?: number;
  protectedRiskExtraPatterns?: string[];
}

export interface BoardSettings {
  workspaceRoot: string;
  maxActiveRuns: number;
  maxActiveCardsPerRepo: number;
  apiHost: string;
  apiPort: number;
}

export const DEFAULT_SETTINGS: BoardSettings = {
  workspaceRoot: 'apps/board/worktrees',
  maxActiveRuns: 5,
  maxActiveCardsPerRepo: 5,
  apiHost: '127.0.0.1',
  apiPort: 4782
};
