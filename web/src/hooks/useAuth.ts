import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

interface UserData {
  token: string;
  role: 'buyer' | 'seller';
  inn: string;
}

const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState<'buyer' | 'seller'>('buyer');
  const [userInn, setUserInn] = useState('');
  const navigate = useNavigate();

  const login = async (inn: string, password: string) => {
    try {
      const response = await axios.post<UserData>('/api/auth/login', { inn, password });
      localStorage.setItem('token', response.data.token);
      setUserRole(response.data.role);
      setUserInn(response.data.inn);
      setIsAuthenticated(true);
      navigate(response.data.role === 'seller' ? '/seller/dashboard' : '/');
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const register = async (inn: string, isSeller: boolean) => {
    try {
      const response = await axios.post<{ message: string }>('/api/auth/register', { 
        inn, 
        is_seller: isSeller 
      });
      navigate('/login', { state: { registrationSuccess: true } });
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setUserRole('buyer');
    navigate('/login');
  };

  return { isAuthenticated, userRole, userInn, login, register, logout };
};

export default useAuth;