import { useState } from 'react';
import CloseIcon from '@mui/icons-material/Close';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';
import Button from '@mui/material/Button';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import type { CardDTO, RunEventDTO } from '../../contracts';

export function CardDetail({ card, events = [], onClose, onResume, onDelete }: { card?: CardDTO; events?: RunEventDTO[]; onClose: () => void; onResume?: (card: CardDTO, note: string) => void; onDelete?: (card: CardDTO) => void }) {
  const [copyState, setCopyState] = useState('Copy');

  if (!card) return null;
  const prUrl = latestPrUrl(events);
  const visualArtifacts = events.map(toVisualArtifact).filter((artifact) => artifact !== undefined);
  const eventLines = events.slice(-12).map(formatEvent);
  const blockerLine = card.status === 'Blocked' && card.blockerSummary ? `Blocker: ${card.blockerSummary}` : undefined;
  const logLines = blockerLine ? [...eventLines, blockerLine] : eventLines;
  const logText = logLines.length > 0 ? logLines.join('\n') : card.status === 'Blocked' ? card.blockerSummary : 'Waiting for runner events...';
  return (
    <Drawer anchor="right" open={Boolean(card)} onClose={onClose} ModalProps={{ keepMounted: true, hideBackdrop: true }} slotProps={{ paper: { className: 'detail', 'aria-label': 'Card detail' } }}>
      <IconButton className="detail__close" aria-label="Close card detail" onClick={onClose}>
        <CloseIcon fontSize="small" />
      </IconButton>
      <h2>{card.title}</h2>
      <div className="detail__track-pill">{card.taskType} track</div>
      <p>{card.instructions}</p>
      <dl>
        <dt>Status</dt><dd>{prUrl ? <Link href={prUrl} target="_blank" rel="noreferrer">{card.status}</Link> : card.status}</dd>
        <dt>Branch</dt><dd>{card.branch ?? 'pending worktree'}</dd>
        <dt>Worktree</dt><dd>{card.worktreePath ?? 'pending'}</dd>
        <dt>Blocker</dt><dd>{card.blockerReason ?? 'none'}</dd>
      </dl>
      <div className="logbox">
        <div className="logbox__header">
          <span>live log</span>
          <Button className="logbox__copy" type="button" size="small" startIcon={<ContentCopyIcon fontSize="inherit" />} onClick={() => copyLog(logText, setCopyState)}>{copyState}</Button>
        </div>
        <code>{logText}</code>
      </div>
      {visualArtifacts.length > 0 ? (
        <div className="visual-evidence">
          <span>visual evidence</span>
          {visualArtifacts.map((artifact) => (
            <figure key={`${artifact.name}-${artifact.path}`}>
              {artifact.kind === 'screenshot' ? <img src={`/api/artifacts?path=${encodeURIComponent(artifact.path)}`} alt={`${artifact.name} screenshot`} /> : null}
              <figcaption>{artifact.name}</figcaption>
            </figure>
          ))}
        </div>
      ) : null}
      <div className="detail__actions">
        {card.status === 'Blocked' ? <Button className="primary" variant="contained" onClick={() => onResume?.(card, window.prompt('Resume note') ?? '')}>Resume with note</Button> : null}
        <IconButton className="danger" aria-label="Close PR, delete branch, and delete workspace" title="Close PR, delete branch, and delete workspace" onClick={() => onDelete?.(card)}><DeleteIcon fontSize="small" /></IconButton>
      </div>
    </Drawer>
  );
}

async function copyLog(logText: string, setCopyState: (state: string) => void): Promise<void> {
  try {
    await navigator.clipboard.writeText(logText);
    setCopyState('Copied');
    window.setTimeout(() => setCopyState('Copy'), 1200);
  } catch {
    setCopyState('Failed');
    window.setTimeout(() => setCopyState('Copy'), 1200);
  }
}

interface VisualArtifactView {
  kind: 'screenshot' | 'video';
  name: string;
  path: string;
}

function toVisualArtifact(event: RunEventDTO): VisualArtifactView | undefined {
  if (event.type !== 'visual_artifact') return undefined;
  const metadata = event.metadata;
  if (!metadata || typeof metadata.path !== 'string' || typeof metadata.name !== 'string') return undefined;
  const kind = metadata.kind === 'video' ? 'video' : 'screenshot';
  return { kind, name: metadata.name, path: metadata.path };
}

function latestPrUrl(events: RunEventDTO[]): string | undefined {
  for (const event of [...events].reverse()) {
    if (event.type !== 'pr') continue;
    if (typeof event.metadata?.url === 'string') return event.metadata.url;
    if (/^https?:\/\//.test(event.message)) return event.message;
  }
  return undefined;
}

function formatEvent(event: RunEventDTO): string {
  const time = new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const stream = typeof event.metadata?.stream === 'string' ? ` ${event.metadata.stream}` : '';
  const message = event.message.replace(/\s+/g, ' ').trim();
  return `[${time}] ${event.type}${stream}: ${message}`;
}
