import type { DragEvent } from 'react';
import ButtonBase from '@mui/material/ButtonBase';
import type { CardDTO } from '../../contracts';

export function BoardCard({ card, onOpen, onDragStart }: { card: CardDTO; onOpen: (card: CardDTO) => void; onDragStart?: (card: CardDTO, event: DragEvent<HTMLElement>) => void }) {
  return (
    <ButtonBase className={`card card--${card.status.toLowerCase().replaceAll(' ', '-')}`} draggable onClick={() => onOpen(card)} onDragStart={(event) => onDragStart?.(card, event)}>
      <div className="card__rail" />
      <div className="card__topline"><span>{card.taskType}</span>{card.autoMerge ? <span className="pill">auto-merge</span> : <span className="pill muted">manual PR</span>}</div>
      <strong>{card.title}</strong>
      <p>{card.blockerSummary ?? card.instructions}</p>
      <div className="card__meta"><span>{card.branch ?? 'branch pending'}</span><span>{card.status}</span></div>
    </ButtonBase>
  );
}
