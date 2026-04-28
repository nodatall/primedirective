import { useState } from 'react';
import type { TaskType } from '../../contracts';

export interface DraftCard { title: string; repoId: string; instructions: string; taskType: TaskType; autoMerge: boolean }

export function CardComposer({ onCreate }: { onCreate: (card: DraftCard) => void }) {
  const [draft, setDraft] = useState<DraftCard>({ title: '', repoId: 'prime', instructions: '', taskType: 'Quick', autoMerge: false });
  return (
    <form className="composer" onSubmit={(event) => { event.preventDefault(); onCreate(draft); setDraft({ ...draft, title: '', instructions: '', autoMerge: false }); }}>
      <div className="composer__header">New agent card</div>
      <input aria-label="Title" placeholder="Title" value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} />
      <input aria-label="Repo" placeholder="Repo" value={draft.repoId} onChange={(event) => setDraft({ ...draft, repoId: event.target.value })} />
      <textarea aria-label="Instructions" placeholder="Instructions" value={draft.instructions} onChange={(event) => setDraft({ ...draft, instructions: event.target.value })} />
      <div className="segmented" role="radiogroup" aria-label="Task type">
        {(['Quick', 'Planned'] as TaskType[]).map((type) => <button type="button" className={draft.taskType === type ? 'active' : ''} onClick={() => setDraft({ ...draft, taskType: type })} key={type}>{type}</button>)}
      </div>
      <label className="toggle"><input type="checkbox" checked={draft.autoMerge} onChange={(event) => setDraft({ ...draft, autoMerge: event.target.checked })} /> Auto-merge PR</label>
      <button className="primary" type="submit">Queue card</button>
    </form>
  );
}
