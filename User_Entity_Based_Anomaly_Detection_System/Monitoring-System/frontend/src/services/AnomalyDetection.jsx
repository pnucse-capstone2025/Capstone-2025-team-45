const API_URL = process.env.REACT_APP_API_URL;

/**
 * 기간을 받아 이상 사용자 탐지 결과를 조회합니다.
 */
export async function fetchAnomalyDetection({ organizationId, startDate, endDate }) {
  const token = localStorage.getItem('access_token');
  const url = `${API_URL}/anomalydetect/${organizationId}/?start_dt=${startDate}T00:00:00&end_dt=${endDate}T00:00:00`;
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('이상 탐지 데이터를 가져오는 데 실패했습니다.');
  return await response.json();
}

export async function fetchAnomalyDetectionDetails(userId, startDate, endDate) {
  const token = localStorage.getItem('access_token');
  const url = `${API_URL}/behavior-log/user?employee_id=${userId}&date_from=${startDate}&date_to=${endDate}`;
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('사용자 행동 로그 데이터를 가져오는 데 실패했습니다.');
  return await response.json();
}

export async function fetchAnomalyDetectionHistories(organizationId) {
  const token = localStorage.getItem('access_token');
  const url = `${API_URL}/anomalydetect/get-histories/${organizationId}/`;
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('탐지 히스토리를 가져오는 데 실패했습니다.');
  return await response.json();
}

export async function fetchAnomalyEmployees(organizationId) {
  const token = localStorage.getItem('access_token');
  const url = `${API_URL}/anomalydetect/${organizationId}/anomaly_employees`;
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('이상 사용자 목록 데이터를 가져오는 데 실패했습니다.');
  return await response.json();
}