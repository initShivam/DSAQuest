import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { ApiError, api, clearToken, hasToken, setUnauthorizedHandler, storeToken, TOKEN_KEY } from "./api";
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
    let active = true;
    const refreshUser = async () => {
      if (!hasToken()) {
        if (active) {
          setUser(null);
          setLoading(false);
        }
        return;
      }
      if (active) setLoading(true);
      try {
        const nextUser = await api.me();
        if (active) setUser(nextUser);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) clearToken();
        if (active) setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    };

    setUnauthorizedHandler(() => {
      if (active) {
        setUser(null);
        setLoading(false);
      }
    });
    void refreshUser();

    const handleStorage = (event: StorageEvent) => {
      if (event.key !== TOKEN_KEY) return;
      if (!event.newValue) {
        setUser(null);
        setLoading(false);
        return;
      }
      void refreshUser();
    };
    window.addEventListener("storage", handleStorage);

    return () => {
      active = false;
      window.removeEventListener("storage", handleStorage);
      setUnauthorizedHandler();
    };
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
