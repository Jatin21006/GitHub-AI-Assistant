import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

interface User {
  name: string;
  email: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

const AUTH_KEY = 'repomind_auth';
const USER_KEY = 'repomind_user';

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  // Restore session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(AUTH_KEY);
    const storedUser = localStorage.getItem(USER_KEY);
    if (stored === 'true' && storedUser) {
      setIsAuthenticated(true);
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const login = async (email: string, _password: string) => {
    // Simulate a brief network delay for realism
    await new Promise(resolve => setTimeout(resolve, 800));
    
    const userData: User = {
      name: email.split('@')[0],
      email,
    };
    
    setUser(userData);
    setIsAuthenticated(true);
    localStorage.setItem(AUTH_KEY, 'true');
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
  };

  const signup = async (name: string, email: string, _password: string) => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const userData: User = { name, email };
    
    setUser(userData);
    setIsAuthenticated(true);
    localStorage.setItem(AUTH_KEY, 'true');
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(USER_KEY);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
