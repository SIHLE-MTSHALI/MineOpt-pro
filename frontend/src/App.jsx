import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import PlannerWorkspace from './pages/PlannerWorkspace';
import LoginPage from './pages/LoginPage';
import LandingPage from './pages/LandingPage';
import SiteDashboard from './pages/SiteDashboard';

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

        {/* Legacy /app route redirects to dashboard */}
        <Route
          path="/app"
          element={<Navigate to="/app/dashboard" replace />}
        />

        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

