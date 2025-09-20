import React, { createContext, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { fetchRefresh } from '../services/AuthServices';
import SessionExpiredAlert from '../components/ui/SessionExpireAlert';

const AuthContext = createContext();

const AuthProvider = ({ children }) => {
    const [authState, setAuthState] = useState({
        isAuthenticated: false,
        isLoading: true,
    });
    const [showSessionExpired, setShowSessionExpired] = useState(false);

    const handleTokenExpired = () => {
        window.location.reload();
    };

    const handleSessionExpired = () => {
        setAuthState({ isAuthenticated: false, isLoading: false });
        setShowSessionExpired(true);
    };

    const handleConfirmSessionExpired = () => {
        setShowSessionExpired(false);
        window.location.href = '/SignIn';
    };

    const handleUnauthorized = () => {
        setAuthState({ isAuthenticated: false, isLoading: false });
    };

    const handleAuthError = (data) => {
        switch (data?.detail || data?.statusText) {
            case 'Unauthorized':
                handleUnauthorized();
                break;
            case 'Signature has expired':
                handleTokenExpired();
                break;
            case 'Refresh token has expired':
                handleTokenExpired();
                break;
            case 'Login session expired':
                handleSessionExpired();
                break;
            case 'Invalid Token':
                handleUnauthorized();
                break;
            default:
                handleUnauthorized();
        }
    };

    const checkAuth = async () => {
        try {
            const response = await fetchRefresh();
            console.log('Refresh response:', response);

            if (response.ok) {
                setAuthState({ isAuthenticated: true, isLoading: false });
            } else {
                const data = await response.json();
                handleAuthError(data);
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            setAuthState({ isAuthenticated: false, isLoading: false });
        }
    };

    useEffect(() => {
        checkAuth();
    }, []);

    useEffect(() => {
        console.log('Session expired state:', showSessionExpired);
    }, [showSessionExpired]);

    // 전역 API 에러 처리
    useEffect(() => {
        const interceptor = async (response) => {
            if (response.status === 401 || response.status === 422) {
                try {
                    const data = await response.json();
                    handleAuthError(data);
                } catch (error) {
                    console.error('Error parsing response:', error);
                }
            }

            return response;
        };

        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const response = await originalFetch(...args);
            return interceptor(response.clone());
        };

        return () => {
            window.fetch = originalFetch;
        };
    }, []);

    return (cd
        <AuthContext.Provider value={{ authState, setAuthState }}>
            {children}
            {showSessionExpired && (
                <SessionExpiredAlert onConfirm={handleConfirmSessionExpired} />
            )}
        </AuthContext.Provider>
    );
};

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export { AuthContext, AuthProvider };
