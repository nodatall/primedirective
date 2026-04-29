import { useState } from 'react';
import CloseIcon from '@mui/icons-material/Close';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import type { TaskType } from '../../contracts';

export interface DraftCard { title: string; repoId: string; instructions: string; taskType: TaskType; autoMerge: boolean }

export function CardComposer({ repoId, onCancel, onCreate }: { repoId: string; onCancel: () => void; onCreate: (card: DraftCard) => void }) {
  const [draft, setDraft] = useState<DraftCard>({ title: '', repoId, instructions: '', taskType: 'Quick', autoMerge: false });
  return (
    <Box component="form" className="composer" onSubmit={(event) => { event.preventDefault(); onCreate({ ...draft, repoId }); setDraft({ ...draft, repoId, title: '', instructions: '', autoMerge: false }); }}>
      <IconButton className="detail__close" type="button" aria-label="Close card composer" onClick={onCancel}>
        <CloseIcon fontSize="small" />
      </IconButton>
      <p className="composer__repo">Repo: {repoId}</p>
      <TextField className="board-field" aria-label="Title" placeholder="Title" value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} />
      <TextField className="board-field" aria-label="Instructions" placeholder="Instructions" value={draft.instructions} multiline minRows={8} onChange={(event) => setDraft({ ...draft, instructions: event.target.value })} />
      <ToggleButtonGroup className="segmented" exclusive value={draft.taskType} aria-label="Task type" onChange={(_, value: TaskType | null) => { if (value) setDraft({ ...draft, taskType: value }); }}>
        {(['Quick', 'Planned'] as TaskType[]).map((type) => <ToggleButton value={type} key={type}>{type}</ToggleButton>)}
      </ToggleButtonGroup>
      <div className="composer__actions">
        <FormControlLabel className="toggle" control={<Switch checked={draft.autoMerge} onChange={(event) => setDraft({ ...draft, autoMerge: event.target.checked })} />} label="Auto-merge PR" />
        <Button className="primary composer__submit" type="submit" variant="contained" size="small">Begin</Button>
      </div>
    </Box>
  );
}
