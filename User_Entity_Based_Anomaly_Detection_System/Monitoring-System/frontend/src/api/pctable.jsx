const API_URL = process.env.REACT_APP_API_URL;

export async function getPcsStatus({ organizationid }) {
  const response = await fetch(`${API_URL}/pcs/pc_state/${organizationid}`, {
    method: 'GET',
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData?.detail || 'PC 상태 조회 실패');
  }

  return await response.json();
}

export async function ControlPCNetwork({ organization_id, pc_id, access_flag }) {
  try {
    const response = await fetch(
      `${API_URL}/network_access_control/${organization_id}/${pc_id}/${access_flag}`,
      {
        method: 'GET',
      }
    );
    if (!response.ok) throw new Error('PC 네트워크 제어 실패');
    return await response.json();
  } catch (err) {
    console.error(err);
    throw err;
  }
}