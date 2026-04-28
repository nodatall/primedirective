import type { CardDTO } from '../../contracts';

export function CardDetail({ card, onClose, onResume }: { card?: CardDTO; onClose: () => void; onResume?: (card: CardDTO, note: string) => void }) {
  if (!card) return null;
  return (
    <aside className="detail" aria-label="Card detail">
      <button className="detail__close" onClick={onClose}>Close</button>
      <div className="eyebrow">{card.taskType} track</div>
      <h2>{card.title}</h2>
      <p>{card.instructions}</p>
      <dl>
        <dt>Status</dt><dd>{card.status}</dd>
        <dt>Branch</dt><dd>{card.branch ?? 'pending worktree'}</dd>
        <dt>Worktree</dt><dd>{card.worktreePath ?? 'pending'}</dd>
        <dt>Blocker</dt><dd>{card.blockerReason ?? 'none'}</dd>
      </dl>
      <div className="logbox">
        <span>live log</span>
        <code>{card.status === 'Blocked' ? card.blockerSummary : 'Waiting for runner events...'}</code>
      </div>
      {card.status === 'Blocked' ? <button className="primary" onClick={() => onResume?.(card, window.prompt('Resume note') ?? '')}>Resume with note</button> : null}
    </aside>
  );
}
