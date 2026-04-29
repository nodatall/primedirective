export interface SchedulableCard { id: string; repoId: string }

export class Scheduler {
  private active = new Map<string, SchedulableCard>();
  constructor(private maxActiveRuns = 5, private maxActiveCardsPerRepo = 5) {}

  canStart(card: SchedulableCard): boolean {
    if (this.active.size >= this.maxActiveRuns) return false;
    const perRepo = [...this.active.values()].filter((active) => active.repoId === card.repoId).length;
    return perRepo < this.maxActiveCardsPerRepo;
  }

  start(card: SchedulableCard): boolean {
    if (!this.canStart(card)) return false;
    this.active.set(card.id, card);
    return true;
  }

  finish(cardId: string): void {
    this.active.delete(cardId);
  }
}
