import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { 
  TextField, Button, Container, Typography, Box, 
  Paper, Tabs, Tab, Divider, Alert, CircularProgress
} from '@mui/material';
import BusinessIcon from '@mui/icons-material/Business';
import PersonIcon from '@mui/icons-material/Person';

const INN_REGEX = {
  individual: /^\d{12}$/, // ИНН физлица
  legal: /^\d{10}$/      // ИНН юрлица
};

const RegisterPage = () => {
  const [inn, setInn] = useState('');
  const [innError, setInnError] = useState('');
  const [userType, setUserType] = useState<'buyer' | 'seller'>('buyer');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register } = useAuth();

  useEffect(() => {
    if (!inn) {
      setInnError('');
      return;
    }
    
    const isValid = userType === 'seller' 
      ? INN_REGEX.legal.test(inn)
      : INN_REGEX.individual.test(inn);
    
    setInnError(isValid ? '' : 'Некорректный ИНН');
  }, [inn, userType]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (innError) return;
    
    setIsSubmitting(true);
    try {
      await register(inn, userType === 'seller');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Paper elevation={3} sx={{ 
        mt: 8, 
        p: 4,
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: 6
        }
      }}>
        {/* ... остальной код ... */}
        <TextField
          label="ИНН"
          value={inn}
          onChange={(e) => setInn(e.target.value)}
          fullWidth
          margin="normal"
          required
          error={!!innError}
          helperText={innError || (
            userType === 'seller' 
              ? 'Для продавцов требуется 10-значный ИНН юридического лица' 
              : 'Для физических лиц используйте 12-значный ИНН'
          )}
        />
        {/* ... */}
        <Button 
          type="submit" 
          fullWidth 
          variant="contained" 
          size="large"
          disabled={!!innError || isSubmitting}
          sx={{ 
            mt: 3,
            height: 48,
            transition: 'all 0.3s ease',
          }}
        >
          {isSubmitting ? (
            <CircularProgress size={24} color="inherit" />
          ) : (
            `Зарегистрироваться как ${userType === 'seller' ? 'продавец' : 'покупатель'}`
          )}
        </Button>
      </Paper>
    </Container>
  );
};

export default RegisterPage;