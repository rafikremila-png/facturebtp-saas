import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Role constants (must match backend)
export const ROLE_SUPER_ADMIN = "super_admin";
export const ROLE_ADMIN = "admin";

export const ROLE_USER = "user";

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);

    const logout = useCallback(() => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
    }, []);

    useEffect(() => {
        const checkAuth = async () => {
            if (token) {
                try {
                    const response = await axios.get(`${API}/auth/me`, {
                        headers: { Authorization: `Bearer ${token}` }
                    });
                    setUser(response.data);
                } catch (error) {
                    logout();
                }
            }
            setLoading(false);
        };
        checkAuth();
    }, [token, logout]);

    const login = async (email, password) => {
        const response = await axios.post(`${API}/auth/login`, { email, password });
        const { access_token, user: userData } = response.data;
        localStorage.setItem('token', access_token);
        setToken(access_token);
        setUser(userData);
        return userData;
    };

    const register = async (email, password, name) => {
        const response = await axios.post(`${API}/auth/register`, { email, password, name });
        const { access_token, user: userData } = response.data;
        localStorage.setItem('token', access_token);
        setToken(access_token);
        setUser(userData);
        return userData;
    };

    // Role helper functions
    const isAdmin = () => {
        return user?.role === ROLE_ADMIN || user?.role === ROLE_SUPER_ADMIN;
    };

    const isSuperAdmin = () => {
        return user?.role === ROLE_SUPER_ADMIN;
    };

    const hasRole = (roles) => {
        if (!user?.role) return false;
        if (Array.isArray(roles)) {
            return roles.includes(user.role);
        }
        return user.role === roles;
    };

    const value = {
        user,
        token,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
        isAdmin,
        isSuperAdmin,
        hasRole,
        userRole: user?.role || ROLE_USER
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
