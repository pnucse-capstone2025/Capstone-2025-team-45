// SignUp.jsx (단계별 회원가입 기반)
'use client';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, TextField, Button, Typography, Box } from '@mui/material';
import { useTheme } from '@emotion/react';
import { fetchOrganizationInformation, verifyOrganization } from '../api/organization';
import { signUp } from '../api/auth';

import SentraLogo from '../assets/sentra_logo.svg';
import CommonCard from '../components/common/card/CommonCard';

const SignUp = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  const [step, setStep] = useState(1);
  const [organizationId, setOrganizationId] = useState('');
  const [organizationInfo, setOrganizationInfo] = useState(null);
  const [authenticationCode, setAuthenticationCode] = useState('');
  const [orgVerified, setOrgVerified] = useState(false);

  const [formData, setFormData] = useState({
    manager_id: '',
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleOrgSubmit = async () => {
    try {
      const data = await fetchOrganizationInformation({ OID: organizationId });
      setOrganizationInfo(data);
      setStep(2);
    } catch (error) {
      alert('유효하지 않은 조직 ID입니다.');
    }
  };

  const handleAuthCodeSubmit = async () => {
    try {
      const res = verifyOrganization({ OID: organizationId, authentication_code: authenticationCode });
      if (!res) throw new Error('인증 실패');
      const data = await res;
      setOrgVerified(true);
      setStep(3);
      alert('조직 인증이 완료되었습니다.');
    } catch (error) {
      alert('인증 코드가 일치하지 않습니다.');
    }
  };

  const handleFinalSubmit = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      alert('비밀번호가 일치하지 않습니다.');
      return;
    }

    const payload = {
      ...formData,
      organization_id: organizationId,
    };
    delete payload.confirmPassword;

    try {
      const response = await signUp(payload);
      console.log('회원가입 성공:', response);
      if (response.msg === 'Signed up successfully') {
        alert('회원 가입이 완료되었습니다.');
        navigate('/');
      }
    } catch (error) {
      console.error('회원가입 중 오류 발생:', error);
      alert('회원가입에 실패했습니다.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Container maxWidth="sm" className="py-16">
        {step === 1 && (
          <CommonCard
            title="조직 인증"
            header={<Box display="flex" alignItems="center" justifyContent="center">
              <img src={SentraLogo} alt="Sentra Logo" style={{ height: 24, marginRight: 8 }} />
              <Typography variant="subtitle1" fontWeight="bold" color="text.black">
                Sentra
              </Typography>
            </Box>}
            footer={
              <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                <Button variant="contained" onClick={handleOrgSubmit}>
                  조직 확인
                </Button>
              </Box>
            }
          >
            <Typography variant="subtitle2" sx={{ mb: 2, textAlign: 'center' }}>
              보안 관리자로 가입하려면, 귀하가 속한 조직의 ID를 입력해야 합니다.
            </Typography>
            <Typography variant="body2" sx={{ mb: 2, textAlign: 'center', color: theme.palette.text.secondary }}>
              조직 ID는 조직 관리자에게 문의하여 확인할 수 있습니다.
            </Typography>
            <TextField
              label="조직 ID"
              value={organizationId}
              onChange={(e) => setOrganizationId(e.target.value)}
              fullWidth
            />
          </CommonCard>
        )}


        {step === 2 && organizationInfo && (
          <CommonCard
            title="조직 정보를 확인한 후, 인증코드를 입력하세요."
            header={<Box display="flex" alignItems="center" justifyContent="center">
              <img src={SentraLogo} alt="Sentra Logo" style={{ height: 24, marginRight: 8 }} />
              <Typography variant="subtitle1" fontWeight="bold" color="text.black">
                Sentra
              </Typography>
            </Box>}
            footer={
              <Box display="flex" justifyContent="center">
                <Button variant="contained" onClick={handleAuthCodeSubmit}>
                  코드 인증
                </Button>
              </Box>
            }
          >
            <Box>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                이름: <Typography component="span">{organizationInfo.organization_name}</Typography>
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ whiteSpace: 'pre-line', mb: 2 }}
              >
                설명: {organizationInfo.description || '설명 없음'}
              </Typography>

              <TextField
                label="인증 코드"
                value={authenticationCode}
                onChange={(e) => setAuthenticationCode(e.target.value)}
                fullWidth
                sx={{ mt: 1, mb: 2 }}
              />
            </Box>
          </CommonCard>

        )}


        {step === 3 && orgVerified && (
          <CommonCard
            title="관리자 정보를 입력하세요."
            header={
              <Box display="flex" alignItems="center" justifyContent="center">
                <img src={SentraLogo} alt="Sentra Logo" style={{ height: 24, marginRight: 8 }} />
                <Typography variant="subtitle1" fontWeight="bold" color="text.black">
                  Sentra
                </Typography>
              </Box>
            }
            footer={
              <Box display="flex" justifyContent="center">
                <Button type="submit" variant="contained" form="manager-register-form">
                  확인
                </Button>
              </Box>
            }
          >
            <Box
              id="manager-register-form"
              component="form"
              onSubmit={handleFinalSubmit}
              className="flex flex-col gap-4"
            >
              <TextField
                label="ID"
                name="manager_id"
                value={formData.manager_id}
                onChange={handleChange}
                required
                fullWidth
              />
              <TextField
                label="비밀번호"
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                fullWidth
              />
              <TextField
                label="비밀번호 확인"
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                fullWidth
              />
              <TextField
                label="이름"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                fullWidth
              />
              <TextField
                label="이메일"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                fullWidth
              />
            </Box>
          </CommonCard>
        )}

      </Container>
    </div>
  );
};

export default SignUp;