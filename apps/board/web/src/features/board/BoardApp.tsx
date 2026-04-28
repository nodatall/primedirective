import { useEffect, useMemo, useState } from 'react';
import { CARD_STATUSES, type CardDTO } from '../../contracts';
import { CardComposer, type DraftCard } from '../cards/CardComposer';
import { CardDetail } from '../card-detail/CardDetail';
import { cards as seedCards } from './sampleData';
import { BoardCard } from './BoardCard';

const columns = CARD_STATUSES.filter((status) => !['Abandoned'].includes(status));

export function BoardApp() {
  const [cards, setCards] = useState<CardDTO[]>([]);
  const [selected, setSelected] = useState<CardDTO | undefined>();
  const [apiState, setApiState] = useState<'connecting' | 'live' | 'offline'>('connecting');

  useEffect(() => {
    let alive = true;
    async function loadSnapshot() {
      try {
        const response = await fetch('/api/snapshot');
        if (!response.ok) throw new Error('snapshot failed');
        const snapshot = await response.json() as { cards: CardDTO[] };
        if (!alive) return;
        const nextCards = snapshot.cards.length ? snapshot.cards : seedCards;
        setCards(nextCards);
        setSelected((current) => current ? nextCards.find((card) => card.id === current.id) ?? current : current);
        setApiState('live');
      } catch {
        if (!alive) return;
        setCards((current) => current.length ? current : seedCards);
        setApiState('offline');
      }
    }
    void loadSnapshot();
    const timer = window.setInterval(loadSnapshot, 1000);
    return () => { alive = false; window.clearInterval(timer); };
  }, []);

  async function createDraft(draft: DraftCard) {
    const optimistic: CardDTO = { id: crypto.randomUUID(), status: 'Inbox', updatedAt: new Date().toISOString(), ...draft };
    setCards((current) => [optimistic, ...current]);
    try {
      const response = await fetch('/api/cards', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(optimistic) });
      if (!response.ok) throw new Error('card create failed');
      const payload = await response.json() as { card: CardDTO };
      setCards((current) => current.map((card) => card.id === optimistic.id ? payload.card : card));
      setApiState('live');
    } catch {
      setCards((current) => current.map((card) => card.id === optimistic.id ? { ...card, status: 'Blocked', blockerReason: 'runner_failed', blockerSummary: 'API unavailable; card is local only.' } : card));
      setApiState('offline');
    }
  }

  const counts = useMemo(() => ({ active: cards.filter((card) => ['Queued', 'Running'].includes(card.status)).length, repoActive: cards.filter((card) => card.repoId === 'prime' && ['Queued', 'Running'].includes(card.status)).length }), [cards]);
  return (
    <main className="shell">
      <section className="hero">
        <div>
          <div className="eyebrow">Prime Directive cockpit</div>
          <h1>Agent Board</h1>
          <p>Run Quick and Planned Codex work in isolated worktrees, watch status move automatically, and keep PR merge/cleanup guarded.</p>
        </div>
        <div className="meters"><span>{counts.active}/5 active</span><span>{counts.repoActive}/5 repo slots</span><span>{apiState === 'live' ? 'loopback API live' : apiState}</span></div>
      </section>
      <section className="workspace">
        <CardComposer onCreate={createDraft} />
        <div className="board" aria-label="Agent Kanban board">
          {columns.map((status) => (
            <section className="column" key={status}>
              <header><span>{status}</span><b>{cards.filter((card) => card.status === status).length}</b></header>
              {cards.filter((card) => card.status === status).map((card) => <BoardCard card={card} onOpen={setSelected} key={card.id} />)}
            </section>
          ))}
        </div>
      </section>
      <CardDetail card={selected} onClose={() => setSelected(undefined)} onResume={async (card, note) => {
        await fetch(`/api/cards/${card.id}/resume`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ note }) });
      }} />
    </main>
  );
}
