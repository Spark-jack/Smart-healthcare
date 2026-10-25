import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/common/Navbar';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { PatientDashboard } from './pages/PatientDashboard';
import { DoctorDashboard } from './pages/DoctorDashboard';
import { AdminDashboard } from './pages/AdminDashboard';
import { Activity } from 'lucide-react';

const MainApp = () => {
  const { user, isAuthenticated, loading, isDoctor, isAdmin } = useAuth();
  const [authView, setAuthView] = useState('login'); // 'login' or 'register'
  const [activeTab, setActiveTab] = useState('patient');

  // Set default tab based on user's role on login
  useEffect(() => {
    if (user) {
      if (user.role === 'doctor') {
        setActiveTab('doctor');
      } else if (user.role === 'admin') {
        setActiveTab('admin');
      } else {
        setActiveTab('patient');
      }
    }
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="w-12 h-12 rounded-2xl bg-teal-600 text-white flex items-center justify-center mx-auto shadow-lg shadow-teal-600/30 mb-3 animate-pulse">
            <Activity className="w-6 h-6 animate-spin" />
          </div>
          <p className="text-xs font-bold text-slate-600">Initializing SmartHealth.AI Environment...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return authView === 'login' ? (
      <LoginPage onSwitchToRegister={() => setAuthView('register')} />
    ) : (
      <RegisterPage onSwitchToLogin={() => setAuthView('login')} />
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans selection:bg-teal-500 selection:text-white">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 pb-16">
        {activeTab === 'patient' && <PatientDashboard />}
        {activeTab === 'doctor' && (isDoctor || isAdmin) && <DoctorDashboard />}
        {activeTab === 'admin' && isAdmin && <AdminDashboard />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200/80 bg-white py-6 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Smart Healthcare Ecosystem with Predictive Analytics & Explainable AI (PRJ-02)</span>
          <div className="flex items-center gap-4 text-slate-500 font-medium">
            <span>XGBoost + SHAP</span>
            <span>•</span>
            <span>FastAPI + SQLAlchemy</span>
            <span>•</span>
            <span>React + Tailwind CSS</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
