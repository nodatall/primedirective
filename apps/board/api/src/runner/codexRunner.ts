import { spawn, type ChildProcessByStdio } from 'node:child_process';
import type { Readable } from 'node:stream';
import { assertCodexCwd } from '../worktrees/manager.js';

export interface RunnerEvent { type: 'stdout' | 'stderr' | 'json' | 'exit'; payload: unknown }
export type RunnerSink = (event: RunnerEvent) => void;

export class CodexRunner {
  run(prompt: string, worktreePath: string, sink: RunnerSink): ChildProcessByStdio<null, Readable, Readable> {
    assertCodexCwd(worktreePath, worktreePath);
    const child = spawn('codex', ['exec', '--json', '--full-auto', '--sandbox', 'workspace-write', prompt], { cwd: worktreePath, shell: false, stdio: ['ignore', 'pipe', 'pipe'] });
    child.stdout.on('data', (chunk: Buffer) => {
      for (const line of String(chunk).split('\n').filter(Boolean)) {
        try { sink({ type: 'json', payload: JSON.parse(line) }); }
        catch { sink({ type: 'stdout', payload: line }); }
      }
    });
    child.stderr.on('data', (chunk: Buffer) => sink({ type: 'stderr', payload: String(chunk) }));
    child.on('exit', (code: number | null) => sink({ type: 'exit', payload: { code } }));
    return child;
  }
}

export class FakeRunner {
  async runScript(lines: string[], sink: RunnerSink): Promise<number> {
    for (const line of lines) sink({ type: 'stdout', payload: line });
    sink({ type: 'exit', payload: { code: 0 } });
    return 0;
  }
}
