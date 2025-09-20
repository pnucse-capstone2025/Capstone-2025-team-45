import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Box, Container } from '@mui/material';

const  Home = () =>{
  const navigate = useNavigate();

  const handleStartClick = () => {
    navigate('./signup'); //회원가입
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <Container maxWidth="md" className="flex flex-col items-center justify-center py-20 text-center">
        <Typography variant="h4" component="h2" gutterBottom className="font-semibold">
          Sentra 보안 플랫폼에 가입하세요.<br />
          조직 행동을 실시간으로 감시하세요.
        </Typography>
        <Typography variant="body1" className="text-gray-600 mb-6">
          실시간 모니터링과 이상 탐지를 통해 조직의 보안을 강화하세요.<br />
          언제든지 시작하고, 언제든지 해지할 수 있습니다.
        </Typography>
        <Box className="flex gap-4 justify-center mt-4">
          <Button
            variant="contained"
            color="primary"
            onClick={handleStartClick}
            className="px-6"
          >
            시작하기
          </Button>
          <Button
            variant="outlined"
            color="primary"
            className="px-6"
          >
            요금제 보기
          </Button>
        </Box>
      </Container>
    </div>
  );
}

export default Home;