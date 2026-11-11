import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import PageLoading from "./Loading";

/**
 * Route gate for the UI. The real authorization is enforced by the backend —
 * this component only prevents anonymous users from *seeing* protected pages
 * and keeps voters away from the admin area in the UI.
 */
export default function ProtectedRoute({ role: requiredRole, children }) {
  const { user, role, initializing, sessionNotice, clearSessionNotice } = useAuth();
  const location = useLocation();

  if (initializing) return <PageLoading label="Checking your session…" />;
  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname, ...(sessionNotice ? { notice: sessionNotice } : {}) }}
      />
    );
  }
  if (requiredRole && role !== requiredRole) {
    // Signed in, but wrong role — send them to their own area.
    return <Navigate to={role === "admin" ? "/admin" : "/vote"} replace />;
  }
  if (sessionNotice && location.pathname === "/login") clearSessionNotice();
  return children;
}
