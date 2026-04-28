import React from 'react';
import { createRoot } from 'react-dom/client';
import { BoardApp } from './features/board/BoardApp';
import './styles.css';

createRoot(document.getElementById('root')!).render(<BoardApp />);
