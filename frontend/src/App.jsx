import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import PlannerWorkspace from './pages/PlannerWorkspace';
import LoginPage from './pages/LoginPage';
import LandingPage from './pages/LandingPage';
import SiteDashboard from './pages/SiteDashboard';
import FleetDashboard from './pages/FleetDashboard';
import DrillBlastDashboard from './pages/DrillBlastDashboard';
import OperationsDashboard from './pages/OperationsDashboard';
import MonitoringDashboard from './pages/MonitoringDashboard';
import SeedDataPage from './pages/SeedDataPage';
import NotFoundPage from './pages/NotFoundPage';
import { SiteProvider } from './context/SiteContext';
import { ToastProvider } from './context/ToastContext';

// Protected Route wrapper
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Auth pages wrapper with redirect if already logged in
const AuthRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (token) {
    return <Navigate to="/app/dashboard" replace />;
  }
  return children;
};

// Login wrapper to handle navigation after login
const LoginWrapper = () => {
  const navigate = useNavigate();

  const handleLogin = (token) => {
    localStorage.setItem('token', token);
    navigate('/app/dashboard');
  };

  return <LoginPage onLogin={handleLogin} />;
};

// Register wrapper (reuses LoginPage in register mode)
const RegisterWrapper = () => {
  const navigate = useNavigate();

  const handleLogin = (token) => {
    localStorage.setItem('token', token);
    navigate('/app/dashboard');
  };

  return <LoginPage onLogin={handleLogin} defaultMode="register" />;
};

function App() {
  return (
    <BrowserRouter>
      <SiteProvider>
        <ToastProvider>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />

            <Route
              path="/login"
              element={
                <AuthRoute>
                  <LoginWrapper />
                </AuthRoute>
              }
            />

            <Route
              path="/register"
              element={
                <AuthRoute>
                  <RegisterWrapper />
                </AuthRoute>
              }
            />

            {/* Protected Routes */}
            <Route
              path="/app/dashboard"
              element={
                <ProtectedRoute>
                  <SiteDashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/app/planner"
              element={
                <ProtectedRoute>
                  <PlannerWorkspace />
                </ProtectedRoute>
              }
            />

            <Route
              path="/app/fleet"
              element={
                <ProtectedRoute>
                  <FleetDashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/app/drill-blast"
              element={
                <ProtectedRoute>
                  <DrillBlastDashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/app/operations"
              element={
                <ProtectedRoute>
                  <OperationsDashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/app/monitoring"
              element={
                <ProtectedRoute>
                  <MonitoringDashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/app/seed-data"
              element={
                <ProtectedRoute>
                  <SeedDataPage />
                </ProtectedRoute>
              }
            />

            {/* Legacy /app route redirects to dashboard */}
            <Route
              path="/app"
              element={<Navigate to="/app/dashboard" replace />}
            />

            {/* 404 Page */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </ToastProvider>
      </SiteProvider>
    </BrowserRouter>
  );
}

export default App;

