import React, { createContext, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { fetchRefresh } from '../services/AuthService';
import {fetchMe} from '../api/auth.jsx'
import SessionExpiredAlert from '../components/Alert/SessionExpireAlert.jsx';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [authState, setAuthState] = useState({
        isAuthenticated: false,
        isLoading: true,
        user: null,
    });
    const [showSessionExpired, setShowSessionExpired] = useState(false);

    const logoutAndRedirect = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setAuthState({ isAuthenticated: false, isLoading: false, user: null });
        setShowSessionExpired(true);
    };

    const handleSessionError = (errorDetail) => {
        const reason = errorDetail?.detail || errorDetail?.statusText;

        switch (reason) {
            case 'Unauthorized':
            case 'Invalid Token':
            case 'Signature has expired':
            case 'Refresh token has expired':
            case 'Login session expired':
                logoutAndRedirect();
                break;
            default:
                console.warn('Unknown auth error:', reason);
                logoutAndRedirect();
        }
    };

    const checkAuth = async () => {
        const refresh_token = localStorage.getItem('refresh_token');
        if (!refresh_token) {
            console.log('No refresh token found. Skipping auth check.');
            setAuthState({ isAuthenticated: false, isLoading: false });
            return;
        }

        try {
            const response = await fetchRefresh(); // → /auth/refresh
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                const me = await fetchMe();
                setAuthState({ isAuthenticated: true, isLoading: false, user: me });
            } else {
                const error = await response.json();
                handleSessionError(error);
            }
        } catch (err) {
            console.error('Auth check error:', err);
            logoutAndRedirect();
        }
    };

    // 최초 렌더링 시 로그인 상태 확인
    useEffect(() => {
        checkAuth();
    }, []);

    // fetch 인터셉터: 모든 요청 후 응답 확인
    useEffect(() => {
        const originalFetch = window.fetch;

        window.fetch = async (...args) => {
            const response = await originalFetch(...args);
            if ([401, 403, 422].includes(response.status)) {
                try {
                    const error = await response.clone().json();
                    handleSessionError(error);
                } catch (e) {
                    console.warn('Response JSON parse error');
                }
            }
            return response;
        };

        return () => {
            window.fetch = originalFetch;
        };
    }, []);

    const confirmSessionExpire = () => {
        setShowSessionExpired(false);
        window.location.href = '/signin';
    };

    return (
        <AuthContext.Provider value={{ authState, setAuthState }}>
            {children}
            {showSessionExpired && (
                <SessionExpiredAlert onConfirm={confirmSessionExpire} />
            )}
        </AuthContext.Provider>
    );
};

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
};
