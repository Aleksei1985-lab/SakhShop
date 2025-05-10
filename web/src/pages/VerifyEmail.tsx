import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Container, Box, Typography, Button, 
  CircularProgress, Alert 
} from '@mui/material';
import axios from 'axios';

const VerifyEmail = () => {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const location = useLocation();
  const navigate = useNavigate();
  const token = new URLSearchParams(location.search).get('token');

  useEffect(() => {
    if (token) {
      verifyToken();
    }
  }, [token]);

  const verifyToken = async () => {
    setStatus('loading');
    try {
      await axios.post('/api/auth/verify-email', { token });
      setStatus('success');
      setMessage('Email успешно подтверждён!');
      setTimeout(() => navigate('/'), 3000);
    } catch (error) {
      setStatus('error');
      setMessage('Ошибка подтверждения email. Ссылка недействительна или истекла.');
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ 
        mt: 8,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center'
      }}>
        {status === 'loading' && (
          <>
            <CircularProgress size={60} />
            <Typography variant="h6" sx={{ mt: 3 }}>
              Подтверждение email...
            </Typography>
          </>
        )}
        
        {status === 'success' && (
          <Alert severity="success" sx={{ width: '100%' }}>
            {message}
          </Alert>
        )}
        
        {status === 'error' && (
          <>
            <Alert severity="error" sx={{ width: '100%', mb: 3 }}>
              {message}
            </Alert>
            <Button 
              variant="contained" 
              onClick={() => navigate('/register')}
            >
              Зарегистрироваться снова
            </Button>
          </>
        )}
      </Box>
    </Container>
  );
};

export default VerifyEmail;