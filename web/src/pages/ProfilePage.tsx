import { useState, useEffect } from 'react';
import { 
  Container, Typography, Box, Avatar, TextField, 
  Button, CircularProgress, Alert 
} from '@mui/material';
import useAuth from '../hooks/useAuth';
import axios from 'axios';

// Явно определяем тип профиля
interface UserProfile {
  email: string;
  phone: string;
  name: string;
  avatar: string;
  email_verified: boolean; // Добавляем обязательное поле
}

const ProfilePage = () => {
  const { userInn, userRole, logout } = useAuth();
  const [profile, setProfile] = useState<UserProfile>({
    email: '',
    phone: '',
    name: '',
    avatar: '',
    email_verified: false // Инициализируем значение
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await axios.get<UserProfile>('/api/user/profile'); // Указываем тип ответа
        setProfile(response.data);
      } catch (err) {
        setError('Ошибка загрузки профиля');
      } finally {
        setIsLoading(false);
      }
    };
    fetchProfile();
  }, []);

  if (isLoading) return <CircularProgress />;

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

        {error && <Alert severity="error" sx={{ mb: 3, width: '100%' }}>{error}</Alert>}

        <Box component="form" sx={{ mt: 3, width: '100%' }}>
          <TextField
            label="Email"
            value={profile.email}
            fullWidth
            margin="normal"
            disabled={!profile.email_verified}
            InputProps={{
              endAdornment: !profile.email_verified && (
                <Button size="small" color="warning">
                  Подтвердить
                </Button>
              )
            }}
          />

          <TextField
            label="Телефон"
            value={profile.phone}
            fullWidth
            margin="normal"
          />

          <TextField
            label="ФИО"
            value={profile.name}
            fullWidth
            margin="normal"
          />

          <Button 
            variant="contained" 
            sx={{ mt: 3, mr: 2 }}
          >
            Сохранить
          </Button>
          
          <Button 
            color="error" 
            sx={{ mt: 3 }}
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