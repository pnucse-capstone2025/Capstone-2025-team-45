const API_URL = process.env.REACT_APP_API_URL;

// OID 를 사용해 조직 정보를 가져오는 함수 
export async function fetchOrganizationInformation({ OID }) {
  const response = await fetch(`${API_URL}/organizations/${OID}/name&description`);
  if (!response.ok) {
    throw new Error('조직 정보를 가져오는 데 실패했습니다.');
  }
  return await response.json();
} 

//OID 및 인증 코드를 사용해 조직 인증을 수행하는 함수
export async function verifyOrganization({ OID, authentication_code }) {
  const response = await fetch(`${API_URL}/organizations/${OID}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ authentication_code }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData?.detail || '조직 인증에 실패했습니다.');
  }

  return await response.json();
}