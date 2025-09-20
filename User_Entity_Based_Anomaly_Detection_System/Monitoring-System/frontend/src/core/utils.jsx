export const handleApiError = async (
    response,
    fallbackMessage = 'An error occurred',
) => {
    if (!response.ok) {
        let errorData;
        let message = fallbackMessage;
        
        try {
            errorData = await response.json();
            
            /**
             * errorData.detail이 객체인 경우:
             * JSON.stringify로 객체를 문자열로 변환
             * null, 2 옵션으로 가독성 있게 포맷팅
             * errorData.detail이 객체가 아닌 경우:
             * detail 값을 그대로 사용
             * detail이 없는 경우 fallbackMessage 사용
             */
            message =
                errorData.detail && typeof errorData.detail === 'object'
                    ? JSON.stringify(errorData.detail, null, 2)
                    : errorData.detail || errorData.message || fallbackMessage;
        } catch (parseError) {
            // If we can't parse the response as JSON, use the status text or fallback
            message = response.statusText || `${fallbackMessage} (Status: ${response.status})`;
        }
        
        throw {
            message,
            type: response.status === 404 ? 'warning' : 'error',
            status: response.status,
        };
    }
    return response;
};
