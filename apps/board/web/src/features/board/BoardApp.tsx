import { useEffect, useMemo, useState } from 'react';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';
import PlaylistAddIcon from '@mui/icons-material/PlaylistAdd';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import IconButton from '@mui/material/IconButton';
import MenuItem from '@mui/material/MenuItem';
import Select, { type SelectChangeEvent } from '@mui/material/Select';
import TextField from '@mui/material/TextField';
import type { CardDTO, CardStatus, RepoDTO, RunEventDTO } from '../../contracts';
import { CardComposer, type DraftCard } from '../cards/CardComposer';
import { CardDetail } from '../card-detail/CardDetail';
import { BoardCard } from './BoardCard';

const columns: Array<{ title: string; statuses: CardStatus[] }> = [
  { title: 'Inbox', statuses: ['Inbox'] },
  { title: 'Running', statuses: ['Queued', 'Running'] },
  { title: 'WOW', statuses: ['Blocked'] },
  { title: 'Review', statuses: ['PR Ready', 'Checks Pending', 'Merging'] },
  { title: 'Done', statuses: ['Merged', 'Done'] }
];

export function BoardApp() {
  const [cards, setCards] = useState<CardDTO[]>([]);
  const [events, setEvents] = useState<RunEventDTO[]>([]);
  const [repos, setRepos] = useState<RepoDTO[]>([]);
  const [selected, setSelected] = useState<CardDTO | undefined>();
  const [selectedRepoId, setSelectedRepoId] = useState('primedirective');
  const [repoDraft, setRepoDraft] = useState({ name: '', path: '' });
  const [repoError, setRepoError] = useState('');
  const [repoModalOpen, setRepoModalOpen] = useState(false);
  const [repoSwitcherOpen, setRepoSwitcherOpen] = useState(false);
  const [composerOpen, setComposerOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    async function loadSnapshot() {
      try {
        const response = await fetch('/api/snapshot');
        if (!response.ok) throw new Error('snapshot failed');
        const snapshot = await response.json() as { cards: CardDTO[]; repos: RepoDTO[]; events?: RunEventDTO[] };
        if (!alive) return;
        const nextCards = snapshot.cards;
        const nextRepos = snapshot.repos;
        setCards(nextCards);
        setEvents(snapshot.events ?? []);
        setRepos(nextRepos);
        setSelectedRepoId((current) => nextRepos.some((repo) => repo.id === current) ? current : nextRepos[0]?.id ?? 'primedirective');
        setSelected((current) => current ? nextCards.find((card) => card.id === current.id) ?? current : current);
      } catch {
        if (!alive) return;
      }
    }
    void loadSnapshot();
    const timer = window.setInterval(loadSnapshot, 1000);
    return () => { alive = false; window.clearInterval(timer); };
  }, []);

  useEffect(() => {
    void fetch('/api/repos', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        id: 'primedirective',
        name: 'primedirective',
        path: '/Volumes/Code/primedirective',
        defaultBranch: 'main'
      })
    }).catch(() => undefined);
  }, []);

  async function createDraft(draft: DraftCard) {
    const optimistic: CardDTO = { id: crypto.randomUUID(), status: 'Inbox', updatedAt: new Date().toISOString(), ...draft };
    setCards((current) => [optimistic, ...current]);
    setComposerOpen(false);
    try {
      const response = await fetch('/api/cards', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(optimistic) });
      if (!response.ok) throw new Error('card create failed');
      const payload = await response.json() as { card: CardDTO };
      setCards((current) => current.map((card) => card.id === optimistic.id ? payload.card : card));
    } catch {
      setCards((current) => current.map((card) => card.id === optimistic.id ? { ...card, status: 'Blocked', blockerReason: 'runner_failed', blockerSummary: 'API unavailable; card is local only.' } : card));
    }
  }

  async function addRepo() {
    const name = repoDraft.name.trim();
    const path = repoDraft.path.trim();
    if (!name || !path) {
      setRepoError('Name and local path are required.');
      return;
    }
    const id = name.toLowerCase().replace(/[^a-z0-9._-]+/g, '-').replace(/^-|-$/g, '');
    if (!id) {
      setRepoError('Use a repo name with letters or numbers.');
      return;
    }
    if (repos.some((repo) => repo.id === id)) {
      setRepoError('Repo already exists.');
      return;
    }
    const response = await fetch('/api/repos', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ id, name, path, defaultBranch: 'main' })
    });
    if (!response.ok) {
      setRepoError('Could not register repo.');
      return;
    }
    const payload = await response.json() as { repo: RepoDTO };
    setRepos((current) => [...current.filter((repo) => repo.id !== payload.repo.id), payload.repo].sort((a, b) => a.name.localeCompare(b.name)));
    setSelectedRepoId(payload.repo.id);
    setRepoDraft({ name: '', path: '' });
    setRepoError('');
    setRepoModalOpen(false);
  }

  async function removeSelectedRepo() {
    if (selectedRepoId === 'primedirective') {
      setRepoError('The default repo cannot be removed.');
      return;
    }
    if (cards.some((card) => card.repoId === selectedRepoId)) {
      setRepoError('Remove or finish this repo’s cards before removing the repo.');
      return;
    }
    const response = await fetch(`/api/repos/${encodeURIComponent(selectedRepoId)}`, { method: 'DELETE' });
    if (!response.ok) {
      const payload = await response.json().catch(() => undefined) as { message?: string } | undefined;
      setRepoError(payload?.message ?? 'Could not remove repo.');
      return;
    }
    setRepos((current) => current.filter((repo) => repo.id !== selectedRepoId));
    setSelectedRepoId('primedirective');
    setRepoError('');
  }

  const repoOptions = useMemo(() => repos.length > 0 ? repos : [{ id: 'primedirective', name: 'primedirective', path: '/Volumes/Code/primedirective', defaultBranch: 'main' }], [repos]);
  const selectedRepo = repoOptions.find((repo) => repo.id === selectedRepoId);
  const visibleCards = useMemo(() => cards.filter((card) => card.repoId === selectedRepoId), [cards, selectedRepoId]);
  const selectedEvents = useMemo(() => selected ? events.filter((event) => event.cardId === selected.id) : [], [events, selected]);
  return (
    <main className="shell">
      <section className="topbar">
        <Button className="repo-name-trigger" type="button" onClick={() => { setRepoSwitcherOpen(true); setRepoError(''); }}>{selectedRepo?.name ?? selectedRepoId}</Button>
        {repoError ? <p className="repo-error">{repoError}</p> : null}
      </section>
      <div className="board" aria-label="Agent Kanban board">
        {columns.map((column) => (
          <section className="column" key={column.title}>
            <header>
              <span>{column.title}</span>
              {column.title === 'Inbox' ? (
                <IconButton className="icon-action icon-action--primary column-new-card-action" type="button" aria-label="New agent card" title="New agent card" onClick={() => setComposerOpen(true)}>
                  <AddIcon fontSize="small" />
                </IconButton>
              ) : null}
            </header>
            {visibleCards.filter((card) => column.statuses.includes(card.status)).map((card) => <BoardCard card={card} onOpen={setSelected} key={card.id} />)}
          </section>
        ))}
      </div>
      <Dialog open={composerOpen} onClose={() => setComposerOpen(false)} aria-label="New agent card" slotProps={{ paper: { className: 'dialog-paper' } }}>
        <CardComposer repoId={selectedRepoId} onCreate={createDraft} onCancel={() => setComposerOpen(false)} />
      </Dialog>
      <Dialog open={repoSwitcherOpen} onClose={() => setRepoSwitcherOpen(false)} aria-label="Repo controls" slotProps={{ paper: { className: 'dialog-paper' } }}>
        <div className="repo-switcher-modal">
          <IconButton className="detail__close" type="button" aria-label="Close repo controls" onClick={() => setRepoSwitcherOpen(false)}>
            <CloseIcon fontSize="small" />
          </IconButton>
          <div className="repo-cluster">
            <label className="repo-picker">
              <Select className="repo-select" value={selectedRepoId} onChange={(event: SelectChangeEvent) => { setSelectedRepoId(event.target.value); setRepoError(''); }} displayEmpty MenuProps={{ PaperProps: { className: 'repo-menu' } }}>
                {repoOptions.map((repo) => <MenuItem value={repo.id} key={repo.id}>{repo.name}</MenuItem>)}
              </Select>
            </label>
            <div className="repo-actions">
              <IconButton className="icon-action" type="button" aria-label="Add repo" title="Add repo" onClick={() => { setRepoSwitcherOpen(false); setRepoModalOpen(true); setRepoError(''); }}>
                <PlaylistAddIcon fontSize="small" />
              </IconButton>
              <IconButton className="icon-action" type="button" aria-label="Remove repo" title="Remove repo" onClick={removeSelectedRepo}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </div>
          </div>
          {repoError ? <p className="repo-error repo-error--modal">{repoError}</p> : null}
        </div>
      </Dialog>
      <Dialog open={repoModalOpen} onClose={() => setRepoModalOpen(false)} aria-label="Add repo" slotProps={{ paper: { className: 'dialog-paper' } }}>
          <Box component="form" className="repo-modal" onSubmit={(event) => { event.preventDefault(); addRepo(); }}>
            <div className="composer__header">
              <span>Add repo</span>
              <IconButton className="detail__close" type="button" aria-label="Close add repo" onClick={() => setRepoModalOpen(false)}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </div>
            <TextField className="board-field" aria-label="Name" placeholder="Name, e.g. sortinghat" value={repoDraft.name} onChange={(event) => setRepoDraft({ ...repoDraft, name: event.target.value })} />
            <TextField className="board-field" aria-label="Local path" placeholder="/Volumes/Code/sortinghat" value={repoDraft.path} onChange={(event) => setRepoDraft({ ...repoDraft, path: event.target.value })} />
            <Button className="primary" variant="contained" type="submit">Add repo</Button>
          </Box>
      </Dialog>
      <CardDetail card={selected} events={selectedEvents} onClose={() => setSelected(undefined)} onResume={async (card, note) => {
        await fetch(`/api/cards/${card.id}/resume`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ note }) });
      }} onDelete={async (card) => {
        if (!window.confirm('Close the PR, delete the branch, delete the workspace, and remove this card?')) return;
        const response = await fetch(`/api/cards/${card.id}/discard`, { method: 'POST' });
        if (!response.ok) return;
        setCards((current) => current.filter((item) => item.id !== card.id));
        setSelected(undefined);
      }} />
    </main>
  );
}
