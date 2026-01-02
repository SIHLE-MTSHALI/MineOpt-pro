import React, { useState, useEffect } from 'react';
import PlannerWorkspace from './pages/PlannerWorkspace';
import LoginPage from './pages/LoginPage';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));

  if (!token) {
    return <LoginPage onLogin={(tok) => setToken(tok)} />;
  }

  return (
    <PlannerWorkspace />
  );
}

export default App;
