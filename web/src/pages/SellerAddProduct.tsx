import { useState } from 'react';
import { Container, TextField, Button, Typography, Box } from '@mui/material';
import ImageUploader from '../components/ImageUploader';

const SellerAddProduct = () => {
  const [product, setProduct] = useState({
    title: '',
    description: '',
    price: '',
    image: ''
  });

  const handleImageUpload = (filename: string) => {
    setProduct(prev => ({ ...prev, image: filename }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Отправка данных товара на сервер
  };

  return (
    <Container maxWidth="md">
      <Typography variant="h4" gutterBottom>Добавить товар</Typography>
      
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
        <ImageUploader 
          onUploadSuccess={handleImageUpload} 
          initialImage={product.image}
        />
        
        <TextField
          label="Название товара"
          fullWidth
          margin="normal"
          value={product.title}
          onChange={(e) => setProduct({ ...product, title: e.target.value })}
        />
        
        <TextField
          label="Описание"
          fullWidth
          multiline
          rows={4}
          margin="normal"
          value={product.description}
          onChange={(e) => setProduct({ ...product, description: e.target.value })}
        />
        
        <TextField
          label="Цена"
          type="number"
          fullWidth
          margin="normal"
          value={product.price}
          onChange={(e) => setProduct({ ...product, price: e.target.value })}
        />
        
        <Button 
          type="submit" 
          variant="contained" 
          size="large" 
          sx={{ mt: 3 }}
        >
          Добавить товар
        </Button>
      </Box>
    </Container>
  );
};

export default SellerAddProduct;