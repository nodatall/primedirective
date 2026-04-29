import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';
import type { CardDTO, RepoDTO, RunEventDTO } from '@prime-board/shared';

export interface BoardData {
  repos: RepoDTO[];
  cards: CardDTO[];
  events: RunEventDTO[];
}

const empty = (): BoardData => ({ repos: [], cards: [], events: [] });

export class JsonStore {
  constructor(private readonly filePath: string) {}

  read(): BoardData {
    try {
      return JSON.parse(readFileSync(this.filePath, 'utf8')) as BoardData;
    } catch {
      return empty();
    }
  }

  write(data: BoardData): void {
    mkdirSync(dirname(this.filePath), { recursive: true });
    writeFileSync(this.filePath, `${JSON.stringify(data, null, 2)}\n`);
  }

  upsertRepo(repo: RepoDTO): void {
    const data = this.read();
    data.repos = [...data.repos.filter((r) => r.id !== repo.id), repo];
    this.write(data);
  }

  upsertCard(card: CardDTO): void {
    const data = this.read();
    data.cards = [...data.cards.filter((c) => c.id !== card.id), card];
    this.write(data);
  }

  appendEvent(event: RunEventDTO): void {
    const data = this.read();
    data.events.push(event);
    this.write(data);
  }
}
