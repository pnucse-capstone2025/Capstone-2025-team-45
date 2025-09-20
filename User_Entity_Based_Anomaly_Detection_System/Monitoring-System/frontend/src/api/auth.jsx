const API_URL = process.env.REACT_APP_API_URL;

export async function signIn({ manager_id, password }) {
  const form = new FormData();
  form.append('username', manager_id);
  form.append('password', password);

  const response = await fetch(`${API_URL}/auth/signin`, {
    method: 'POST',
    body: form, 
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData?.detail || '로그인 실패');
  }

  return await response.json();
}

export async function signUp(payload) {
  const response = await fetch(`${API_URL}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData?.detail || '회원가입 실패');
  }

  return await response.json();
}

export async function fetchMe() {
  const accessToken = localStorage.getItem('access_token');
  const response = await fetch(`${API_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error('사용자 정보를 가져오는 데 실패했습니다.');
  }

  return await response.json();
}