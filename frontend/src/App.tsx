import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { WorkspaceProvider } from './contexts/WorkspaceContext';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { SignUpPage } from './pages/SignUpPage';
import { DashboardPage } from './pages/DashboardPage';
import { WorkspacePage } from './pages/WorkspacePage';
import type { ReactNode } from 'react';

// Protected route wrapper
const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

// Redirect authenticated users away from auth pages
const PublicOnlyRoute = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
};

function AppRoutes() {
  return (
    <AnimatePresence mode="wait">
      <Routes>
        {/* Public routes */}
        <Route path="/" element={
          <PublicOnlyRoute><LandingPage /></PublicOnlyRoute>
        } />
        <Route path="/login" element={
          <PublicOnlyRoute><LoginPage /></PublicOnlyRoute>
        } />
        <Route path="/signup" element={
          <PublicOnlyRoute><SignUpPage /></PublicOnlyRoute>
        } />

        {/* Protected routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute><DashboardPage /></ProtectedRoute>
        } />
        <Route path="/workspace/:owner/:repo" element={
          <ProtectedRoute><WorkspacePage /></ProtectedRoute>
        } />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  return (
    <div className="dark">
      <AuthProvider>
        <WorkspaceProvider>
          <Router>
            <AppRoutes />
          </Router>
        </WorkspaceProvider>
      </AuthProvider>
    </div>
  );
}

export default App;
