import { type KeyboardEvent, useEffect, useState } from 'react';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import CloseIcon from '@mui/icons-material/Close';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';
import Button from '@mui/material/Button';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import type { CardDTO, RunEventDTO } from '../../contracts';

export function CardDetail({ card, events = [], onClose, onResume, onDelete, onUpdate }: { card?: CardDTO; events?: RunEventDTO[]; onClose: () => void; onResume?: (card: CardDTO, note: string) => void; onDelete?: (card: CardDTO) => void; onUpdate?: (card: CardDTO, patch: Partial<Pick<CardDTO, 'title' | 'instructions'>>) => Promise<void> | void }) {
  const [copyState, setCopyState] = useState('Copy');
  const [logExpanded, setLogExpanded] = useState(true);
  const [editing, setEditing] = useState<'title' | 'instructions' | undefined>();
  const [titleDraft, setTitleDraft] = useState('');
  const [instructionsDraft, setInstructionsDraft] = useState('');
  const visualArtifacts = events.map(toVisualArtifact).filter((artifact) => artifact !== undefined);
  const hasVisualEvidence = visualArtifacts.length > 0;

  useEffect(() => {
    setLogExpanded(!hasVisualEvidence);
    setEditing(undefined);
  }, [card?.id]);

  useEffect(() => {
    setTitleDraft(card?.title ?? '');
    setInstructionsDraft(card?.instructions ?? '');
  }, [card?.id, card?.title, card?.instructions]);

  if (!card) return null;
  const editable = card.status === 'Inbox' && Boolean(onUpdate);
  const prUrl = latestPrUrl(events);
  const eventLines = events.slice(-12).map(formatEvent);
  const blockerLine = card.status === 'Blocked' && card.blockerSummary ? `Blocker: ${card.blockerSummary}` : undefined;
  const logLines = blockerLine ? [...eventLines, blockerLine] : eventLines;
  const logText = logLines.length > 0 ? logLines.join('\n') : card.status === 'Blocked' ? card.blockerSummary : 'Waiting for runner events...';
  return (
    <Drawer anchor="right" open={Boolean(card)} onClose={onClose} ModalProps={{ keepMounted: true }} slotProps={{ paper: { className: 'detail', 'aria-label': 'Card detail' } }}>
      <IconButton className="detail__close" aria-label="Close card detail" onClick={onClose}>
        <CloseIcon fontSize="small" />
      </IconButton>
      {editable && editing === 'title' ? (
        <input
          className="detail__title-input"
          aria-label="Task title"
          autoFocus
          value={titleDraft}
          onChange={(event) => setTitleDraft(event.target.value)}
          onBlur={() => void saveTitle(card, titleDraft, onUpdate, setEditing)}
          onKeyDown={(event) => handleTitleKey(event, card, titleDraft, onUpdate, setEditing, setTitleDraft)}
        />
      ) : (
        <h1 className={editable ? 'detail__editable' : undefined} tabIndex={editable ? 0 : undefined} role={editable ? 'button' : undefined} onClick={() => editable && setEditing('title')} onKeyDown={(event) => { if (editable && (event.key === 'Enter' || event.key === ' ')) setEditing('title'); }}>{card.title}</h1>
      )}
      {editable && editing === 'instructions' ? (
        <textarea
          className="detail__instructions-input"
          aria-label="Task instructions"
          autoFocus
          value={instructionsDraft}
          onChange={(event) => setInstructionsDraft(event.target.value)}
          onBlur={() => void saveInstructions(card, instructionsDraft, onUpdate, setEditing)}
          onKeyDown={(event) => handleInstructionsKey(event, card, instructionsDraft, onUpdate, setEditing, setInstructionsDraft)}
        />
      ) : (
        <p className={`detail__instructions ${editable ? 'detail__editable' : ''}`} tabIndex={editable ? 0 : undefined} role={editable ? 'button' : undefined} onClick={() => editable && setEditing('instructions')} onKeyDown={(event) => { if (editable && (event.key === 'Enter' || event.key === ' ')) setEditing('instructions'); }}>{card.instructions}</p>
      )}
      <dl>
        <dt>Status</dt><dd>{prUrl ? <Link href={prUrl} target="_blank" rel="noreferrer">{card.status}</Link> : card.status}</dd>
        <dt>Branch</dt><dd>{card.branch ?? 'pending worktree'}</dd>
        {card.blockerReason || card.blockerSummary ? <><dt>Blocker</dt><dd>{card.blockerSummary ?? card.blockerReason}</dd></> : null}
      </dl>
      <div className={`logbox ${logExpanded ? '' : 'logbox--collapsed'}`}>
        <div className="logbox__header">
          <button className="logbox__toggle" type="button" aria-expanded={logExpanded} onClick={() => setLogExpanded((current) => !current)}>
            {logExpanded ? <KeyboardArrowDownIcon fontSize="small" /> : <KeyboardArrowRightIcon fontSize="small" />}
            <span>live log</span>
          </button>
          {logExpanded ? (
            <IconButton className="logbox__copy" type="button" size="small" aria-label="Copy live log" title={copyState} onClick={() => copyLog(logText, setCopyState)}>
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          ) : null}
        </div>
        {logExpanded ? <code>{logText}</code> : null}
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

async function saveTitle(card: CardDTO, title: string, onUpdate: ((card: CardDTO, patch: Partial<Pick<CardDTO, 'title' | 'instructions'>>) => Promise<void> | void) | undefined, setEditing: (field: undefined) => void): Promise<void> {
  setEditing(undefined);
  const nextTitle = title.trim();
  if (!onUpdate || !nextTitle || nextTitle === card.title) return;
  await onUpdate(card, { title: nextTitle });
}

async function saveInstructions(card: CardDTO, instructions: string, onUpdate: ((card: CardDTO, patch: Partial<Pick<CardDTO, 'title' | 'instructions'>>) => Promise<void> | void) | undefined, setEditing: (field: undefined) => void): Promise<void> {
  setEditing(undefined);
  const nextInstructions = instructions.trim();
  if (!onUpdate || nextInstructions === card.instructions) return;
  await onUpdate(card, { instructions: nextInstructions });
}

function handleTitleKey(event: KeyboardEvent<HTMLInputElement>, card: CardDTO, title: string, onUpdate: ((card: CardDTO, patch: Partial<Pick<CardDTO, 'title' | 'instructions'>>) => Promise<void> | void) | undefined, setEditing: (field: undefined) => void, setTitleDraft: (title: string) => void): void {
  if (event.key === 'Escape') {
    setTitleDraft(card.title);
    setEditing(undefined);
    return;
  }
  if (event.key === 'Enter') {
    event.currentTarget.blur();
  }
}

function handleInstructionsKey(event: KeyboardEvent<HTMLTextAreaElement>, card: CardDTO, instructions: string, onUpdate: ((card: CardDTO, patch: Partial<Pick<CardDTO, 'title' | 'instructions'>>) => Promise<void> | void) | undefined, setEditing: (field: undefined) => void, setInstructionsDraft: (instructions: string) => void): void {
  if (event.key === 'Escape') {
    setInstructionsDraft(card.instructions);
    setEditing(undefined);
    return;
  }
  if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
    event.currentTarget.blur();
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
