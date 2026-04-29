import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import type { CardDTO, RepoDTO, RunEventDTO } from '@prime-board/shared';
import { schemaSql } from './schema.js';

export interface BoardData {
  repos: RepoDTO[];
  cards: CardDTO[];
  events: RunEventDTO[];
  runs: StoredRun[];
  worktrees: StoredWorktree[];
  pullRequests: StoredPullRequest[];
  integrationJobs: StoredIntegrationJob[];
}

export interface StoredRun { id: string; cardId: string; attempt: number; phase: string; status: string; runnerPid?: number; runnerLease?: string; exitCode?: number | null; error?: string }
export interface StoredWorktree { id: string; cardId: string; repoId: string; path: string; branch: string; status: string }
export interface StoredPullRequest { id: string; cardId: string; repoId: string; number: number; url: string; state: string; headRefOid?: string; checksState?: string }
export interface StoredIntegrationJob { id: string; cardId: string; repoId: string; type: string; status: string; lockKey: string; attempts: number }

export class SqliteStore {
  private readonly db: DatabaseSync;

  constructor(private readonly filePath: string) {
    mkdirSync(dirname(filePath), { recursive: true });
    this.db = new DatabaseSync(filePath);
    this.db.exec(schemaSql);
  }

  read(): BoardData {
    return {
      repos: this.db.prepare('SELECT * FROM repo ORDER BY created_at').all().map(rowToRepo),
      cards: this.db.prepare('SELECT * FROM card ORDER BY created_at DESC').all().map(rowToCard),
      events: this.db.prepare('SELECT * FROM run_event ORDER BY timestamp, id').all().map(rowToEvent),
      runs: this.db.prepare('SELECT * FROM run ORDER BY started_at, id').all().map(rowToRun),
      worktrees: this.db.prepare('SELECT * FROM worktree ORDER BY created_at, id').all().map(rowToWorktree),
      pullRequests: this.db.prepare('SELECT * FROM pull_request ORDER BY created_at, id').all().map(rowToPullRequest),
      integrationJobs: this.db.prepare('SELECT * FROM integration_job ORDER BY created_at, id').all().map(rowToIntegrationJob)
    };
  }

  findRepo(id: string): RepoDTO | undefined {
    const row = this.db.prepare('SELECT * FROM repo WHERE id = ?').get(id);
    return row ? rowToRepo(row) : undefined;
  }

  findCard(id: string): CardDTO | undefined {
    const row = this.db.prepare('SELECT * FROM card WHERE id = ?').get(id);
    return row ? rowToCard(row) : undefined;
  }

  countCardsForRepo(repoId: string): number {
    const row = this.db.prepare('SELECT COUNT(*) AS count FROM card WHERE repo_id = ?').get(repoId) as { count: number };
    return Number(row.count);
  }

  deleteRepo(id: string): void {
    this.db.prepare('DELETE FROM repo WHERE id = ?').run(id);
  }

  deleteCard(id: string): void {
    this.db.prepare('DELETE FROM integration_job WHERE card_id = ?').run(id);
    this.db.prepare('DELETE FROM pull_request WHERE card_id = ?').run(id);
    this.db.prepare('DELETE FROM worktree WHERE card_id = ?').run(id);
    this.db.prepare('DELETE FROM run_event WHERE card_id = ?').run(id);
    this.db.prepare('DELETE FROM run WHERE card_id = ?').run(id);
    this.db.prepare('DELETE FROM card WHERE id = ?').run(id);
  }

  upsertRepo(repo: RepoDTO): void {
    const now = new Date().toISOString();
    this.db.prepare(`
      INSERT INTO repo (id, name, path, default_branch, remote_url, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET name = excluded.name, path = excluded.path, default_branch = excluded.default_branch, remote_url = excluded.remote_url, updated_at = excluded.updated_at
    `).run(repo.id, repo.name, repo.path, repo.defaultBranch, repo.remoteUrl ?? null, now, now);
  }

  upsertCard(card: CardDTO): void {
    const now = new Date().toISOString();
    this.db.prepare(`
      INSERT INTO card (id, repo_id, title, instructions, task_type, auto_merge, status, branch, worktree_path, blocker_reason, blocker_summary, override_paused, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET repo_id = excluded.repo_id, title = excluded.title, instructions = excluded.instructions, task_type = excluded.task_type, auto_merge = excluded.auto_merge, status = excluded.status, branch = excluded.branch, worktree_path = excluded.worktree_path, blocker_reason = excluded.blocker_reason, blocker_summary = excluded.blocker_summary, override_paused = excluded.override_paused, updated_at = excluded.updated_at
    `).run(card.id, card.repoId, card.title, card.instructions, card.taskType, card.autoMerge ? 1 : 0, card.status, card.branch ?? null, card.worktreePath ?? null, card.blockerReason ?? null, card.blockerSummary ?? null, card.overridePaused ? 1 : 0, now, card.updatedAt ?? now);
  }

  upsertRun(run: StoredRun): void {
    const now = new Date().toISOString();
    this.db.prepare(`
      INSERT INTO run (id, card_id, attempt, phase, status, runner_pid, runner_lease, started_at, ended_at, exit_code, error)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET phase = excluded.phase, status = excluded.status, runner_pid = excluded.runner_pid, runner_lease = excluded.runner_lease, ended_at = excluded.ended_at, exit_code = excluded.exit_code, error = excluded.error
    `).run(run.id, run.cardId, run.attempt, run.phase, run.status, run.runnerPid ?? null, run.runnerLease ?? null, now, run.status === 'running' ? null : now, run.exitCode ?? null, run.error ?? null);
  }

  upsertWorktree(worktree: StoredWorktree): void {
    const now = new Date().toISOString();
    this.db.prepare(`
      INSERT INTO worktree (id, card_id, repo_id, path, branch, status, created_at, cleaned_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
      ON CONFLICT(id) DO UPDATE SET path = excluded.path, branch = excluded.branch, status = excluded.status
    `).run(worktree.id, worktree.cardId, worktree.repoId, worktree.path, worktree.branch, worktree.status, now);
  }

  markWorktreeCleaned(cardId: string): void {
    this.db.prepare('UPDATE worktree SET status = ?, cleaned_at = ? WHERE card_id = ?').run('cleaned', new Date().toISOString(), cardId);
  }

  upsertPullRequest(pr: StoredPullRequest): void {
    const now = new Date().toISOString();
    this.db.prepare(`
      INSERT INTO pull_request (id, card_id, repo_id, number, url, state, head_ref_oid, checks_state, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET number = excluded.number, url = excluded.url, state = excluded.state, head_ref_oid = excluded.head_ref_oid, checks_state = excluded.checks_state, updated_at = excluded.updated_at
    `).run(pr.id, pr.cardId, pr.repoId, pr.number, pr.url, pr.state, pr.headRefOid ?? null, pr.checksState ?? null, now, now);
  }

  upsertIntegrationJob(job: StoredIntegrationJob): void {
    const now = new Date().toISOString();
    this.db.prepare(`
      INSERT INTO integration_job (id, card_id, repo_id, type, status, lock_key, attempts, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET status = excluded.status, attempts = excluded.attempts, updated_at = excluded.updated_at
    `).run(job.id, job.cardId, job.repoId, job.type, job.status, job.lockKey, job.attempts, now, now);
  }

  setSetting(key: string, value: unknown): void {
    this.db.prepare('INSERT INTO setting (key, value_json) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json').run(key, JSON.stringify(value));
  }

  upsertWorkflowOverride(repoId: string, path: string, parsed: unknown, status: string, errors: string[]): void {
    this.db.prepare(`
      INSERT INTO workflow_override (repo_id, path, parsed_json, parse_status, errors_json, loaded_at)
      VALUES (?, ?, ?, ?, ?, ?)
      ON CONFLICT(repo_id) DO UPDATE SET path = excluded.path, parsed_json = excluded.parsed_json, parse_status = excluded.parse_status, errors_json = excluded.errors_json, loaded_at = excluded.loaded_at
    `).run(repoId, path, JSON.stringify(parsed), status, JSON.stringify(errors), new Date().toISOString());
  }

  appendEvent(event: RunEventDTO): void {
    this.db.prepare(`
      INSERT INTO run_event (id, run_id, card_id, timestamp, event_type, message, metadata_json)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `).run(event.id, event.runId, event.cardId, event.timestamp, event.type, event.message, JSON.stringify(event.metadata ?? {}));
  }
}

function asRecord(row: unknown): Record<string, unknown> { return row as Record<string, unknown>; }
function rowToRepo(row: unknown): RepoDTO { const r = asRecord(row); return { id: String(r.id), name: String(r.name), path: String(r.path), defaultBranch: String(r.default_branch), remoteUrl: r.remote_url ? String(r.remote_url) : undefined }; }
function rowToCard(row: unknown): CardDTO { const r = asRecord(row); return { id: String(r.id), repoId: String(r.repo_id), title: String(r.title), instructions: String(r.instructions), taskType: r.task_type === 'Planned' ? 'Planned' : 'Quick', autoMerge: Boolean(r.auto_merge), status: String(r.status) as CardDTO['status'], branch: r.branch ? String(r.branch) : undefined, worktreePath: r.worktree_path ? String(r.worktree_path) : undefined, blockerReason: r.blocker_reason ? String(r.blocker_reason) as CardDTO['blockerReason'] : undefined, blockerSummary: r.blocker_summary ? String(r.blocker_summary) : undefined, overridePaused: Boolean(r.override_paused), updatedAt: String(r.updated_at) }; }
function rowToEvent(row: unknown): RunEventDTO { const r = asRecord(row); return { id: String(r.id), runId: String(r.run_id), cardId: String(r.card_id), timestamp: String(r.timestamp), type: String(r.event_type) as RunEventDTO['type'], message: String(r.message), metadata: r.metadata_json ? JSON.parse(String(r.metadata_json)) as Record<string, unknown> : undefined }; }
function rowToRun(row: unknown): StoredRun { const r = asRecord(row); return { id: String(r.id), cardId: String(r.card_id), attempt: Number(r.attempt), phase: String(r.phase), status: String(r.status), runnerPid: r.runner_pid ? Number(r.runner_pid) : undefined, runnerLease: r.runner_lease ? String(r.runner_lease) : undefined, exitCode: r.exit_code === null || r.exit_code === undefined ? undefined : Number(r.exit_code), error: r.error ? String(r.error) : undefined }; }
function rowToWorktree(row: unknown): StoredWorktree { const r = asRecord(row); return { id: String(r.id), cardId: String(r.card_id), repoId: String(r.repo_id), path: String(r.path), branch: String(r.branch), status: String(r.status) }; }
function rowToPullRequest(row: unknown): StoredPullRequest { const r = asRecord(row); return { id: String(r.id), cardId: String(r.card_id), repoId: String(r.repo_id), number: Number(r.number), url: String(r.url), state: String(r.state), headRefOid: r.head_ref_oid ? String(r.head_ref_oid) : undefined, checksState: r.checks_state ? String(r.checks_state) : undefined }; }
function rowToIntegrationJob(row: unknown): StoredIntegrationJob { const r = asRecord(row); return { id: String(r.id), cardId: String(r.card_id), repoId: String(r.repo_id), type: String(r.type), status: String(r.status), lockKey: String(r.lock_key), attempts: Number(r.attempts) }; }
