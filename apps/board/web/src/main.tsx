import React from 'react';
import { createRoot } from 'react-dom/client';
import { Agentation } from 'agentation';
import { BoardApp } from './features/board/BoardApp';
import './styles.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BoardApp />
    {import.meta.env.DEV ? <Agentation className="agentation-layer" /> : null}
  </React.StrictMode>
);
