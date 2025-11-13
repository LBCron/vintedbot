import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../api/client';
import type { User, LoginRequest, RegisterRequest } from '../types';
import { logger } from '../utils/logger';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = async () => {
    // Check if token exists in localStorage
    const token = localStorage.getItem('auth_token');
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const response = await authAPI.getMe();
      setUser(response.data);
    } catch (error) {
      // Token invalid or expired - clear it and user not authenticated
      localStorage.removeItem('auth_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUser();
  }, []);

  const login = async (data: LoginRequest) => {
    // Get token from response and store in localStorage
    const response = await authAPI.login(data);
    const token = response.data.access_token;
    localStorage.setItem('auth_token', token);
    await loadUser();
  };

  const register = async (data: RegisterRequest) => {
    // Get token from response and store in localStorage
    const response = await authAPI.register(data);
    const token = response.data.access_token;
    localStorage.setItem('auth_token', token);
    await loadUser();
  };

  const logout = async () => {
    // Clear token from localStorage
    localStorage.removeItem('auth_token');
    try {
      await authAPI.logout();
    } catch (error) {
      logger.error('Logout error', error);
    } finally {
      setUser(null);
    }
  };

  const refreshUser = async () => {
    await loadUser();
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
