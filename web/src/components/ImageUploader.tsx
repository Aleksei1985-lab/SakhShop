import { useState, useCallback } from 'react';
import { Button, Box, Avatar, CircularProgress, Typography } from '@mui/material';
import axios from 'axios';

interface ImageUploaderProps {
  onUploadSuccess: (filename: string) => void;
  initialImage?: string;
}

const ImageUploader = ({ onUploadSuccess, initialImage = '' }: ImageUploaderProps) => {
  const [preview, setPreview] = useState(initialImage);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      // Проверка размера файла (макс. 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('Файл слишком большой (макс. 5MB)');
        return;
      }

      // Проверка типа файла
      if (!file.type.match('image.*')) {
        setError('Пожалуйста, загрузите изображение');
        return;
      }

      setPreview(URL.createObjectURL(file));
      setError('');
      setIsUploading(true);

      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post('/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        onUploadSuccess(response.data.filename);
      } catch (err) {
        setError('Ошибка загрузки изображения');
        console.error(err);
      } finally {
        setIsUploading(false);
      }
    }
  }, [onUploadSuccess]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Avatar 
        src={preview || '/placeholder.jpg'} 
        sx={{ width: 200, height: 200, mb: 2 }}
        variant="rounded"
      />
      
      <Button 
        variant="contained" 
        component="label"
        disabled={isUploading}
      >
        {isUploading ? <CircularProgress size={24} /> : 'Загрузить изображение'}
        <input 
          type="file" 
          hidden 
          accept="image/jpeg,image/png,image/webp" 
          onChange={handleChange} 
        />
      </Button>
      
      {error && (
        <Typography color="error" sx={{ mt: 1 }}>
          {error}
        </Typography>
      )}
      
      <Typography variant="caption" sx={{ mt: 1 }}>
        JPG, PNG или WEBP, не более 5MB
      </Typography>
    </Box>
  );
};

export default ImageUploader;