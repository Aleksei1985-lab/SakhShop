import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { 
  TextField, Button, Container, Typography, Box, 
  Alert, CircularProgress, Link
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import * as yup from 'yup';
import { useFormik } from 'formik';

const loginSchema = yup.object({
  inn: yup.string().required('ИНН обязателен').matches(/^\d{10,12}$/, 'ИНН должен содержать 10-12 цифр'),
  password: yup.string().required('Пароль обязателен').min(6, 'Пароль должен быть не менее 6 символов')
});

const LoginPage = () => {
  const { login } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const formik = useFormik({
    initialValues: { inn: '', password: '' },
    validationSchema: loginSchema,
    onSubmit: async (values) => {
      try {
        await login(values.inn, values.password);
        navigate(location.state?.from || '/');
      } catch (err) {
        setError('Неверный ИНН или пароль');
      }
    }
  });

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography variant="h4" gutterBottom>Вход в SakhShop</Typography>
        
        {location.state?.registrationSuccess && (
          <Alert severity="success" sx={{ mb: 3, width: '100%' }}>
            Регистрация прошла успешно! Подтвердите email для входа.
          </Alert>
        )}

        {error && <Alert severity="error" sx={{ mb: 3, width: '100%' }}>{error}</Alert>}

        <Box component="form" onSubmit={formik.handleSubmit} sx={{ mt: 3, width: '100%' }}>
          <TextField
            fullWidth
            id="inn"
            name="inn"
            label="ИНН"
            value={formik.values.inn}
            onChange={formik.handleChange}
            error={formik.touched.inn && Boolean(formik.errors.inn)}
            helperText={formik.touched.inn && formik.errors.inn}
            margin="normal"
          />
          
          <TextField
            fullWidth
            id="password"
            name="password"
            label="Пароль"
            type="password"
            value={formik.values.password}
            onChange={formik.handleChange}
            error={formik.touched.password && Boolean(formik.errors.password)}
            helperText={formik.touched.password && formik.errors.password}
            margin="normal"
          />

          <Button 
            type="submit" 
            fullWidth 
            variant="contained" 
            sx={{ mt: 3, mb: 2 }}
            disabled={formik.isSubmitting}
          >
            {formik.isSubmitting ? <CircularProgress size={24} /> : 'Войти'}
          </Button>

          <Link href="/forgot-password" variant="body2">Забыли пароль?</Link>
        </Box>
      </Box>
    </Container>
  );
};
export default LoginPage;