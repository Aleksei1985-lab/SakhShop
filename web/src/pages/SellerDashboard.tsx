import { Box, Typography, Card, CardContent, Grid } from '@mui/material';
import { useAuth } from '../hooks/useAuth';

const SellerDashboard = () => {
  const { userInn } = useAuth();

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Панель продавца
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Ваш ИНН</Typography>
              <Typography>{userInn}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Статистика</Typography>
              <Typography>Товаров: 15</Typography>
              <Typography>Заказов: 42</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SellerDashboard;