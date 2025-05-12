import { createContext, useContext, useState, ReactNode } from 'react';
import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import { 
  Container, Typography, Box, Avatar, TextField, 
  Button, CircularProgress, Alert 
} from '@mui/material';
import useAuth from '../hooks/useAuth';
import axios from 'axios';


type ThemeMode = 'light' | 'dark';

interface ThemeContextType {
  toggleTheme: () => void;
  mode: ThemeMode;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [mode, setMode] = useState<ThemeMode>('light');
  
  const theme = createTheme({
    palette: {
      mode,
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#9c27b0',
      },
    },
  });

  const toggleTheme = () => {
    setMode(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ toggleTheme, mode }}>
      <MuiThemeProvider theme={theme}>
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};


interface Profile {
  email: string;
  phone: string;
  name: string;
  avatar: string;
  email_verified?: boolean;
}

const ProfilePage = () => {
  const { userInn, userRole, logout } = useAuth();
  const [profile, setProfile] = useState<Profile>({
    email: '',
    phone: '',
    name: '',
    avatar: '',
    email_verified: false
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [tempProfile, setTempProfile] = useState<Profile>({...profile});

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await axios.get<Profile>('/api/user/profile');
        setProfile(response.data);
        setTempProfile(response.data);
      } catch (err) {
        setError('Ошибка загрузки профиля');
        console.error('Profile load error:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleSave = async () => {
    try {
      setIsLoading(true);
      const response = await axios.put<Profile>('/api/user/profile', tempProfile);
      setProfile(response.data);
      setEditMode(false);
    } catch (err) {
      setError('Ошибка сохранения профиля');
      console.error('Profile save error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setTempProfile(prev => ({ ...prev, [name]: value }));
  };

  const handleVerifyEmail = async () => {
    try {
      await axios.post('/api/auth/send-verification-email');
      setError('');
      alert('Письмо с подтверждением отправлено на ваш email');
    } catch (err) {
      setError('Ошибка отправки письма подтверждения');
      console.error('Email verification error:', err);
    }
  };

  if (isLoading) return (
    <Box display="flex" justifyContent="center" mt={4}>
      <CircularProgress />
    </Box>
  );

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Avatar 
          src={profile.avatar} 
          sx={{ width: 120, height: 120, mb: 3 }} 
        />
        
        <Typography variant="h4">Мой профиль</Typography>
        <Typography color="textSecondary" gutterBottom>
          {userRole === 'seller' ? 'Продавец' : 'Покупатель'} | ИНН: {userInn}
        </Typography>

        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 3, width: '100%' }}
            onClose={() => setError('')}
          >
            {error}
          </Alert>
        )}

        <Box component="form" sx={{ mt: 3, width: '100%' }}>
          <TextField
            name="email"
            label="Email"
            value={editMode ? tempProfile.email : profile.email}
            onChange={handleChange}
            fullWidth
            margin="normal"
            disabled={!editMode || profile.email_verified}
            InputProps={{
              endAdornment: !profile.email_verified && (
                <Button 
                  size="small" 
                  color="warning"
                  onClick={handleVerifyEmail}
                  disabled={!editMode}
                >
                  Подтвердить
                </Button>
              )
            }}
          />

          <TextField
            name="phone"
            label="Телефон"
            value={editMode ? tempProfile.phone : profile.phone}
            onChange={handleChange}
            fullWidth
            margin="normal"
            disabled={!editMode}
          />

          <TextField
            name="name"
            label="ФИО"
            value={editMode ? tempProfile.name : profile.name}
            onChange={handleChange}
            fullWidth
            margin="normal"
            disabled={!editMode}
          />

          {editMode ? (
            <>
              <Button 
                variant="contained" 
                sx={{ mt: 3, mr: 2 }}
                onClick={handleSave}
                disabled={isLoading}
              >
                {isLoading ? <CircularProgress size={24} /> : 'Сохранить'}
              </Button>
              <Button 
                sx={{ mt: 3 }}
                onClick={() => {
                  setTempProfile({...profile});
                  setEditMode(false);
                }}
              >
                Отмена
              </Button>
            </>
          ) : (
            <Button 
              variant="contained" 
              sx={{ mt: 3, mr: 2 }}
              onClick={() => setEditMode(true)}
            >
              Редактировать
            </Button>
          )}
          
          <Button 
            color="error" 
            sx={{ mt: 3, float: 'right' }}
            onClick={logout}
          >
            Выйти
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default ProfilePage;