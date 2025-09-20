import { useContext } from 'react';
import { AppBar, Toolbar, Typography, Button, Box, IconButton } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { useNavigate } from 'react-router-dom';
import SentraLogo from '../../../assets/sentra_logo_white.svg';
import { AuthContext } from '../../../contexts/authContext'; // 경로 맞게 수정

const Header = ({ handleToggleNavbar }) => {
  const navigate = useNavigate();
  const { authState, setAuthState } = useContext(AuthContext);

  const handleLogoClick = () => {
    navigate('/');
  };

  const handleLoginClick = () => {
    navigate('/signin');
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setAuthState({ isAuthenticated: false, isLoading: false });
    navigate('/');
  };

  return (
    <AppBar position="static" color="default" elevation={1}>
      <Toolbar className="flex justify-between items-center px-4">
        {/* 좌측: 햄버거 버튼 + 로고 */}
        <Box className="flex items-center space-x-3">
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleToggleNavbar}
            sx={{ mr: 1 }}
          >
            <MenuIcon />
          </IconButton>
          <Box
            className="flex items-center space-x-2 cursor-pointer"
            onClick={handleLogoClick}
          >
            <img
              src={SentraLogo}
              alt="Sentra Logo"
              className="h-8 w-auto"
            />
            <Typography variant="h5" color="#e4e4e7" className="font-bold">
              Sentra
            </Typography>
          </Box>
        </Box>

        {/* 우측: 버튼 영역 */}
        <Box className="space-x-4">
          <Button color="inherit">기능</Button>
          <Button color="inherit">지원</Button>
          {authState.isAuthenticated ? (
            <Button color="inherit" onClick={handleLogout}>
              로그아웃
            </Button>
          ) : (
            <Button color="inherit" onClick={handleLoginClick}>
              로그인
            </Button>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
