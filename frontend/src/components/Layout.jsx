import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import Navbar from './Navbar';

export function ProtectedLayout() {
  const { isAuthenticated } = useAuth();
  const { t } = useI18n();
  const location = useLocation();
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
        <Outlet />
      </main>
      <footer className="no-print mx-auto max-w-6xl px-4 pb-10 text-center text-xs text-ink-400 sm:px-6">
        {t.landing.disclaimer}
      </footer>
    </div>
  );
}
