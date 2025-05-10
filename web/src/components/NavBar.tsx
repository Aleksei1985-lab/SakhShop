import { AppBar, Toolbar, Button, Box, Typography } from '@mui/material';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const NavBar = () => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <AppBar position="static">
      <Toolbar>
        {/* ... */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>

          <Button color="inherit" component={Link} to="/">
            Главная
          </Button>
          {isAuthenticated ? (
            <>
              <Button color="inherit" onClick={() => navigate('/profile')}>
                Профиль
              </Button>
              <Button color="inherit" onClick={logout}>
                Выйти
              </Button>
            </>
          ) : (
            <>
              <Button color="inherit" component={Link} to="/login">
                Войти
              </Button>
              <Button color="inherit" component={Link} to="/register">
                Регистрация
              </Button>
            </>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default NavBar;