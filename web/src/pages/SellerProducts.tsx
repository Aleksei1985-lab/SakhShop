import { Container, Typography, Box } from '@mui/material';
import useAuth from '../hooks/useAuth';

const SellerProducts = () => {
  const { userInn } = useAuth();

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" gutterBottom>
          Мои товары
        </Typography>
        <Typography variant="body1">
          ИНН продавца: {userInn}
        </Typography>
        {/* Здесь будет список товаров */}
      </Box>
    </Container>
  );
};

export default SellerProducts;