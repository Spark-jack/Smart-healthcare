import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('sh_token') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem('sh_token');
      const savedUser = localStorage.getItem('sh_user');

      if (savedToken && savedUser) {
        try {
          setUser(JSON.parse(savedUser));
          setToken(savedToken);
          // Refresh user data from API in background
          const me = await api.getMe();
          setUser(me);
          localStorage.setItem('sh_user', JSON.stringify(me));
        } catch (err) {
          console.error("Token verification failed, signing out:", err);
          logout();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    const data = await api.login({ email, password });
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('sh_token', data.access_token);
    localStorage.setItem('sh_user', JSON.stringify(data.user));
    return data.user;
  };

  const register = async (userData) => {
    const newUser = await api.register(userData);
    // Auto-login after registration
    return await login(userData.email, userData.password);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('sh_token');
    localStorage.removeItem('sh_user');
  };

  const isPatient = user?.role === 'patient';
  const isDoctor = user?.role === 'doctor';
  const isAdmin = user?.role === 'admin';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        isPatient,
        isDoctor,
        isAdmin,
        isAuthenticated: !!token && !!user
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
