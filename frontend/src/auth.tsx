import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, clearToken, hasToken, setUnauthorizedHandler, storeToken } from "./api";
import type { User } from "./types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<User>;
  signUp: (body: { email: string; password: string; display_name: string; timezone: string; challenge_mode: string }) => Promise<User>;
  updateUser: (user: User) => void;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null));
    if (!hasToken()) {
      setLoading(false);
      return;
    }
    api.me()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    signIn: async (email, password) => {
      const response = await api.login({ email, password });
      storeToken(response.token);
      setUser(response.user);
      return response.user;
    },
    signUp: async (body) => {
      const response = await api.register(body);
      storeToken(response.token);
      setUser(response.user);
      return response.user;
    },
    updateUser: setUser,
    signOut: async () => {
      try {
        if (hasToken()) await api.logout();
      } finally {
        clearToken();
        setUser(null);
      }
    },
  }), [loading, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
