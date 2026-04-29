import type { CardDTO, RunEventDTO } from '../../contracts';

export function CardDetail({ card, events = [], onClose, onResume, onDelete }: { card?: CardDTO; events?: RunEventDTO[]; onClose: () => void; onResume?: (card: CardDTO, note: string) => void; onDelete?: (card: CardDTO) => void }) {
  if (!card) return null;
  const visualArtifacts = events.map(toVisualArtifact).filter((artifact) => artifact !== undefined);
  const eventLines = events.slice(-12).map(formatEvent);
  const blockerLine = card.status === 'Blocked' && card.blockerSummary ? `Blocker: ${card.blockerSummary}` : undefined;
  const logLines = blockerLine ? [...eventLines, blockerLine] : eventLines;
  const logText = logLines.length > 0 ? logLines.join('\n') : card.status === 'Blocked' ? card.blockerSummary : 'Waiting for runner events...';
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
      {card.status === 'Blocked' ? <button className="primary" onClick={() => onResume?.(card, window.prompt('Resume note') ?? '')}>Resume with note</button> : null}
      <button className="danger" onClick={() => onDelete?.(card)}>Delete card</button>
    </aside>
  );
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

function formatEvent(event: RunEventDTO): string {
  const time = new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const stream = typeof event.metadata?.stream === 'string' ? ` ${event.metadata.stream}` : '';
  const message = event.message.replace(/\s+/g, ' ').trim();
  return `[${time}] ${event.type}${stream}: ${message}`;
}
