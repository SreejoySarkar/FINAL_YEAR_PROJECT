import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getToken, clearToken, setUnauthorizedHandler } from "../services/api";
import { fetchCurrentUser, logout as apiLogout } from "../services/authService";

const AuthContext = createContext(null);
AuthContext.displayName = "AuthContext";

/**
 * Holds the authenticated user + session state.
 *
 * Security note: this context makes the UI *convenient*, it is NOT the
 * security boundary. Every protected action is re-authorized by the Django
 * backend, which decides what data each role can read or write.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const [sessionNotice, setSessionNotice] = useState(null);
  const navigate = useNavigate();

  /* restore a valid session (token kept in sessionStorage, never localStorage) */
  useEffect(() => {
    let alive = true;
    (async () => {
      if (getToken()) {
        try {
          const u = await fetchCurrentUser();
          if (alive) setUser(u || null);
        } catch {
          if (alive) {
            clearToken();
            setUser(null);
          }
        }
      }
      if (alive) setInitializing(false);
    })();
    return () => {
      alive = false;
    };
  }, []);

  /* global 401 handling — expire the session everywhere at once */
  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null);
      setSessionNotice("Your session has expired. Please log in again.");
      navigate("/login", { replace: true });
    });
    return () => setUnauthorizedHandler(null);
  }, [navigate]);

  const completeLogin = useCallback((data) => {
    setUser(data.user);
    setSessionNotice(null);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      setUser(null);
      navigate("/login", { replace: true });
    }
  }, [navigate]);

  const role = user?.role || (user?.is_staff ? "admin" : user ? "voter" : null);

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        initializing,
        sessionNotice,
        clearSessionNotice: () => setSessionNotice(null),
        completeLogin,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
