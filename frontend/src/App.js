import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import './App.css';
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import LearningPage from './pages/LearningPage';
import AssessmentPage from './pages/AssessmentPage';
import PerformancePage from './pages/PerformancePage';
import { useState, useEffect } from 'react';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || 'null'));

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    } else {
      localStorage.removeItem('user');
    }
  }, [user]);

  const handleLogin = (newToken, newUser) => {
    setToken(newToken);
    setUser(newUser);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.clear();
  };

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route 
            path="/auth" 
            element={token ? <Navigate to="/dashboard" /> : <AuthPage onLogin={handleLogin} />} 
          />
          <Route 
            path="/dashboard" 
            element={token ? <Dashboard user={user} onLogout={handleLogout} /> : <Navigate to="/auth" />} 
          />
          <Route 
            path="/learn" 
            element={token ? <LearningPage user={user} onLogout={handleLogout} /> : <Navigate to="/auth" />} 
          />
          <Route 
            path="/assess" 
            element={token ? <AssessmentPage user={user} onLogout={handleLogout} /> : <Navigate to="/auth" />} 
          />
          <Route 
            path="/performance" 
            element={token ? <PerformancePage user={user} onLogout={handleLogout} /> : <Navigate to="/auth" />} 
          />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-center" richColors />
    </div>
  );
}

export default App;
