import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, tokenStore } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!tokenStore.get()) {
      setUser(null);
      return null;
    }
    try {
      const u = await api.me();
      setUser(u);
      return u;
    } catch {
      setUser(null);
      tokenStore.clear();
      return null;
    }
  }, []);

  useEffect(() => {
    // Skip /auth/me if returning from OAuth — AuthCallback will handle token first
    if (window.location.hash?.includes("token=")) {
      setLoading(false);
      return;
    }
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  const logout = async () => {
    try {
      await api.logout();
    } catch {}
    tokenStore.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loading, refresh, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
