import React from 'react';
import { createRoot } from 'react-dom/client';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Agentation } from 'agentation';
import { BoardApp } from './features/board/BoardApp';
import './styles.css';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#7bd5e5' },
    secondary: { main: '#7bd5e5' },
    error: { main: '#ff776d' },
    background: { default: '#0a0f12', paper: '#11181d' },
    text: { primary: '#e6edf3', secondary: '#8f9faa' }
  },
  shape: { borderRadius: 7 },
  typography: {
    fontFamily: "'Space Grotesk Board', Inter, ui-sans-serif, system-ui, sans-serif",
    button: { textTransform: 'none', fontWeight: 800 }
  }
});

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <BoardApp />
      {import.meta.env.DEV ? <Agentation className="agentation-layer" /> : null}
    </ThemeProvider>
  </React.StrictMode>
);
