import { HashRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import { Compass } from "lucide-react";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import { DemoBanner } from "./components/ui";
import PageLoading from "./components/Loading";
import { useAuth } from "./context/AuthContext";

import Home from "./pages/Home";
import Login from "./pages/Login";
import AdminDashboard from "./pages/AdminDashboard";
import ElectionManagement from "./pages/ElectionManagement";
import CandidateManagement from "./pages/CandidateManagement";
import VoterManagement from "./pages/VoterManagement";
import QRManagement from "./pages/QRManagement";
import AuditLogs from "./pages/AuditLogs";
import Results from "./pages/Results";
import VoterDashboard from "./pages/VoterDashboard";
import QRVerification from "./pages/QRVerification";
import Voting from "./pages/Voting";
import VoteConfirmation from "./pages/VoteConfirmation";

/**
 * Entry point.
 *
 * - HashRouter is used so the single-file production build works on any
 *   static host without rewrite rules. Swap for BrowserRouter if your server
 *   rewrites all paths to index.html (standard for SPA deployments).
 * - ProtectedRoute gates the UI; the Django backend remains the real
 *   authorization boundary for every request.
 */
function NotFound() {
  return (
    <div className="text-center py-5" style={{ minHeight: "70vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
      <Compass size={34} className="text-faint mb-3" />
      <h4 style={{ fontWeight: 700 }}>Page not found</h4>
      <p className="text-soft mb-3" style={{ fontSize: "0.92rem" }}>The page you are looking for does not exist.</p>
      <Link to="/" className="btn btn-primary btn-sm">Back to home</Link>
    </div>
  );
}

function Gate({ children }: { children: React.ReactNode }) {
  // AuthContext is authored in JSX (per project structure); cast avoids a TS inference gap.
  const { initializing } = useAuth() as unknown as { initializing: boolean };
  if (initializing) return <PageLoading label="Starting…" />;
  return <>{children}</>;
}

export default function App() {
  return (
    <HashRouter>
      <AuthProvider>
        <DemoBanner />
        <Gate>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />

            {/* Administrator area — UI-gated to admin role; enforced by backend */}
            <Route path="/admin" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
            <Route path="/admin/elections" element={<ProtectedRoute role="admin"><ElectionManagement /></ProtectedRoute>} />
            <Route path="/admin/candidates" element={<ProtectedRoute role="admin"><CandidateManagement /></ProtectedRoute>} />
            <Route path="/admin/voters" element={<ProtectedRoute role="admin"><VoterManagement /></ProtectedRoute>} />
            <Route path="/admin/qr" element={<ProtectedRoute role="admin"><QRManagement /></ProtectedRoute>} />
            <Route path="/admin/audit" element={<ProtectedRoute role="admin"><AuditLogs /></ProtectedRoute>} />
            <Route path="/admin/results" element={<ProtectedRoute role="admin"><Results /></ProtectedRoute>} />

            {/* Voter area — UI-gated to voter role; enforced by backend */}
            <Route path="/vote" element={<ProtectedRoute role="voter"><VoterDashboard /></ProtectedRoute>} />
            <Route path="/vote/qr/:electionId" element={<ProtectedRoute role="voter"><QRVerification /></ProtectedRoute>} />
            <Route path="/vote/election/:electionId" element={<ProtectedRoute role="voter"><Voting /></ProtectedRoute>} />
            <Route path="/vote/confirmed/:electionId" element={<ProtectedRoute role="voter"><VoteConfirmation /></ProtectedRoute>} />

            <Route path="/home" element={<Navigate to="/" replace />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Gate>
      </AuthProvider>
    </HashRouter>
  );
}
