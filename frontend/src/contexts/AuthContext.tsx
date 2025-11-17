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
    // SECURITY FIX Bug #3: Use HTTP-only cookies instead of localStorage
    // Backend automatically sends session cookie with each request (withCredentials: true)
    try {
      const response = await authAPI.getMe();
      setUser(response.data);
    } catch (error) {
      // Cookie expired or invalid - user not authenticated
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUser();
  }, []);

  const login = async (data: LoginRequest) => {
    // SECURITY FIX Bug #3: Backend sets HTTP-only cookie automatically
    // No need to store token in localStorage (vulnerable to XSS)
    await authAPI.login(data);
    await loadUser();
  };

  const register = async (data: RegisterRequest) => {
    // SECURITY FIX Bug #3: Backend sets HTTP-only cookie automatically
    // No need to store token in localStorage (vulnerable to XSS)
    await authAPI.register(data);
    await loadUser();
  };

  const logout = async () => {
    // SECURITY FIX Bug #3: No localStorage to clear
    // Backend clears HTTP-only cookie on logout
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
