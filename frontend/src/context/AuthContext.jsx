import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { AuthApi, UserApi } from '../api/endpoints';
import { readSession, setUnauthorizedHandler, writeSession } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => readSession());

  const persist = useCallback((s) => {
    writeSession(s);
    setSession(s);
  }, []);

  const logout = useCallback(() => persist(null), [persist]);

  useEffect(() => {
    setUnauthorizedHandler(logout);
  }, [logout]);

  // Sign out automatically when the token expires.
  useEffect(() => {
    if (!session?.expiresAt) return undefined;
    const ms = new Date(session.expiresAt).getTime() - Date.now();
    if (ms <= 0) { logout(); return undefined; }
    const id = setTimeout(logout, Math.min(ms, 2 ** 31 - 1));
    return () => clearTimeout(id);
  }, [session, logout]);

  const authenticate = useCallback(
    async (call, body) => {
      const res = await call(body);
      persist({ token: res.token, expiresAt: res.expiresAt, user: res.user });
      return res.user;
    },
    [persist],
  );

  const value = useMemo(
    () => ({
      user: session?.user ?? null,
      isAuthenticated: !!session,
      login: (body) => authenticate(AuthApi.login, body),
      register: (body) => authenticate(AuthApi.register, body),
      logout,
      updateProfile: async (body) => {
        const user = await UserApi.update(body);
        persist({ ...session, user });
        return user;
      },
    }),
    [session, authenticate, logout, persist],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
