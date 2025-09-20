const API_URL = process.env.REACT_APP_API_URL;

export const fetchTopologyData = async () => {
  try {
    const token = localStorage.getItem("access_token");

    const headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };

    const response = await fetch(`${API_URL}/network_topology`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  } catch (error) {
    console.error('There was a problem with the fetch operation:', error);
  }
};
