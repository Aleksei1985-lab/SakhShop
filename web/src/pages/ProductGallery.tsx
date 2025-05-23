import { useTheme } from '@mui/material/styles';
import { 
  Container, 
  Typography, 
  Card, 
  CardContent, 
  CardMedia, 
  Chip,
  Grid
} from '@mui/material';
import { products } from '../data/mockProducts';

const ProductGallery = () => {
  const theme = useTheme();

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" gutterBottom sx={{ 
        color: theme.palette.sakhalinAccent.main,
        mb: 4,
        textAlign: 'center'
      }}>
        Товары Сахалина
      </Typography>
      
      <Grid container spacing={4}>
        {products.map((product) => (
          <Grid 
            key={product.id}
            item
            xs={12}
            sm={6}
            md={4}
            lg={3}
          >
            <Card sx={{ 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              '&:hover': {
                boxShadow: 6,
                transform: 'translateY(-4px)',
                transition: 'all 0.3s ease'
              }
            }}>
              <CardMedia
                component="img"
                image={product.image}
                alt={product.title}
                sx={{ 
                  height: 200,
                  objectFit: 'cover',
                  bgcolor: theme.palette.background.paper
                }}
              />
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography gutterBottom variant="h5">
                  {product.title}
                </Typography>
                <Typography paragraph>
                  {product.description}
                </Typography>
                <Chip 
                  label={`${product.price} ₽`} 
                  color="primary"
                  sx={{ 
                    fontWeight: 'bold',
                    fontSize: '1.1rem',
                    bgcolor: theme.palette.sakhalinAccent.light
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default ProductGallery;