import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('hs_token'));
  const [loading, setLoading] = useState(true);

  const axiosInstance = axios.create({
    baseURL: API,
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  const updateAxiosToken = useCallback((newToken) => {
    if (newToken) {
      axiosInstance.defaults.headers.Authorization = `Bearer ${newToken}`;
    } else {
      delete axiosInstance.defaults.headers.Authorization;
    }
  }, [axiosInstance]);

  useEffect(() => {
    updateAxiosToken(token);
  }, [token, updateAxiosToken]);

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const response = await axiosInstance.get('/auth/me');
          setUser(response.data);
        } catch (error) {
          console.error('Auth init error:', error);
          logout();
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { token: newToken, user: userData } = response.data;
    localStorage.setItem('hs_token', newToken);
    setToken(newToken);
    setUser(userData);
    updateAxiosToken(newToken);
    return userData;
  };

  const register = async (name, email, password, company, secret_code) => {
    const response = await axios.post(`${API}/auth/register`, { name, email, password, company, secret_code });
    const { token: newToken, user: userData } = response.data;
    localStorage.setItem('hs_token', newToken);
    setToken(newToken);
    setUser(userData);
    updateAxiosToken(newToken);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('hs_token');
    setToken(null);
    setUser(null);
    updateAxiosToken(null);
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    api: axiosInstance
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
