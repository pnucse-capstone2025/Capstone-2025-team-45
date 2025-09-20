const API_URL = process.env.REACT_APP_API_URL;

export const fetchRefresh = () => {
  const refresh_token = localStorage.getItem('refresh_token');
  return fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${refresh_token}`,
      'Content-Type': 'application/json',
    },
  });
};
