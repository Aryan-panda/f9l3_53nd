import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { AdminPage } from './pages/AdminPage';
import { Navbar } from './components/Navbar';
import { ShieldCheck } from 'lucide-react';

const MainLayout: React.FC = () => {
  const { user, loading } = useAuth();
  const [currentTab, setCurrentTab] = useState<'transfers' | 'admin'>('transfers');

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-600 to-emerald-500 flex items-center justify-center shadow-xl shadow-cyan-500/20 animate-pulse">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <p className="text-xs text-slate-400 font-mono">
          Verifying security session...
        </p>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-black">
      <Navbar currentTab={currentTab} onTabChange={setCurrentTab} />
      <main className="flex-1">
        {currentTab === 'transfers' ? <DashboardPage /> : <AdminPage />}
      </main>
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500 font-mono">
        f9l3_53nd • AES-256-GCM AEAD • SHA-256 Integrity • WireGuard VPN
      </footer>
    </div>
  );
};

export function App() {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
}

export default App;
