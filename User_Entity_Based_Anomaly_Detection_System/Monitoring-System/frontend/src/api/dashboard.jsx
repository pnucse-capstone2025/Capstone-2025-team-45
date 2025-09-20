const API_URL = process.env.REACT_APP_API_URL;

export async function get_pc_counts(organization_id) {
    try {
        const response = await fetch(`${API_URL}/pcs/get_pc_logon_percent/${organization_id}/`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching PC counts:', error);
        throw error;
    }
}

export async function get_anomaly_count_by_week(organization_id){
    try {
        const response = await fetch(`${API_URL}/anomalydetect/get-anomaly-user-counts-by-week/${organization_id}/`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching anomaly counts by week:', error);
        throw error;
    }   
}
export async function fetchNetworkBlockingLogs(organization_id) {
    try {
        const response = await fetch(`${API_URL}/network_access_control/${organization_id}/blocking-network-histories`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching network blocking logs:', error);
        throw error;
    }
}