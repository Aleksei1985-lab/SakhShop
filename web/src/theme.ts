import { createTheme } from '@mui/material/styles';

// Уникальная цветовая палитра (вдохновлена природой Сахалина)
const sakhshopColors = {
  primary: {
    main: '#2E7D32', // Зеленый (цвет сахалинских лесов)
    dark: '#1B5E20',
    light: '#4CAF50',
  },
  secondary: {
    main: '#0277BD', // Голубой (цвет океана)
    dark: '#01579B',
    light: '#0288D1',
  },
  sakhalinAccent: {
    main: '#FF8F00', // Оранжевый (цвет икры)
    dark: '#FF6F00',
    light: '#FFA000',
  },
};

export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    ...sakhshopColors,
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    ...sakhshopColors,
    background: {
      default: '#121212',
      paper: '#1E1E1E',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});