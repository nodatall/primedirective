export const schemaSql = `
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS repo (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  path TEXT NOT NULL UNIQUE,
  default_branch TEXT NOT NULL,
  remote_url TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS card (
  id TEXT PRIMARY KEY,
  repo_id TEXT NOT NULL,
  title TEXT NOT NULL,
  instructions TEXT NOT NULL,
  task_type TEXT NOT NULL,
  auto_merge INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  branch TEXT UNIQUE,
  worktree_path TEXT UNIQUE,
  blocker_reason TEXT,
  blocker_summary TEXT,
  override_paused INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS run (
  id TEXT PRIMARY KEY,
  card_id TEXT NOT NULL,
  attempt INTEGER NOT NULL,
  phase TEXT NOT NULL,
  status TEXT NOT NULL,
  command_summary TEXT,
  prompt_summary TEXT,
  runner_pid INTEGER,
  runner_lease TEXT,
  started_at TEXT,
  ended_at TEXT,
  exit_code INTEGER,
  error TEXT
);
CREATE TABLE IF NOT EXISTS run_event (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  card_id TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  event_type TEXT NOT NULL,
  message TEXT NOT NULL,
  metadata_json TEXT
);
CREATE TABLE IF NOT EXISTS worktree (
  id TEXT PRIMARY KEY,
  card_id TEXT NOT NULL UNIQUE,
  repo_id TEXT NOT NULL,
  path TEXT NOT NULL UNIQUE,
  branch TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  cleaned_at TEXT
);
CREATE TABLE IF NOT EXISTS pull_request (
  id TEXT PRIMARY KEY,
  card_id TEXT NOT NULL UNIQUE,
  repo_id TEXT NOT NULL,
  number INTEGER NOT NULL,
  url TEXT NOT NULL,
  state TEXT NOT NULL,
  head_ref_oid TEXT,
  mergeability TEXT,
  checks_state TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS integration_job (
  id TEXT PRIMARY KEY,
  card_id TEXT NOT NULL,
  repo_id TEXT NOT NULL,
  type TEXT NOT NULL,
  status TEXT NOT NULL,
  lock_key TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS workflow_override (
  repo_id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  parsed_json TEXT,
  parse_status TEXT NOT NULL,
  errors_json TEXT,
  loaded_at TEXT NOT NULL
);
`;
