import { useMessage } from '../contexts/MessageContext.jsx';
import { handleApiError } from './utils';

export const useApi = () => {
    const { showError, showWarning, showSuccess } = useMessage();

    const callApi = async (
        apiCall, successMessage = true) => {
        try {
            const response = await apiCall();

            await handleApiError(response);
            const data = await response.json();
            if (successMessage) {
                showSuccess(data.detail || data.message || 'Success');
            }
            return data;
        } catch (error) {
            console.log('API error', error);
            
            // Handle different types of errors
            let errorMessage = 'An unexpected error occurred';
            let errorType = 'error';
            
            if (error && typeof error === 'object') {
                if (error.message) {
                    errorMessage = error.message;
                    errorType = error.type || 'error';
                } else if (error.status) {
                    // This is likely a Response object
                    errorMessage = `Request failed with status ${error.status}`;
                } else {
                    // Try to get message from various possible properties
                    errorMessage = error.detail || error.toString() || errorMessage;
                }
            } else if (typeof error === 'string') {
                errorMessage = error;
            }
            
            const showMsg = errorType === 'warning' ? showWarning : showError;
            showMsg(errorMessage);
            throw { message: errorMessage, type: errorType };
        }
    };

    return { callApi };
};
