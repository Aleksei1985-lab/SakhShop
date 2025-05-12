import { Typography, Container } from '@mui/material';
import useAuth from '../hooks/useAuth';

const HomePage = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Container maxWidth="lg">
      <Typography variant="h3" gutterBottom>
        Добро пожаловать в SakhShop!
      </Typography>
      <Typography paragraph>
        {isAuthenticated
          ? 'Вы успешно вошли в систему. Теперь вы можете просматривать товары и услуги.'
          : 'Пожалуйста, войдите или зарегистрируйтесь для доступа к полному функционалу.'}
      </Typography>
    </Container>
  );
};

export default HomePage;