import { Link, Route, Routes } from 'react-router-dom';
import { ProtectedLayout } from './components/Layout';
import { useI18n } from './context/I18nContext';
import { LoginPage, RegisterPage } from './pages/AuthPages';
import Dashboard from './pages/Dashboard';
import Deadlines from './pages/Deadlines';
import DocumentDetail from './pages/DocumentDetail';
import Drafts from './pages/Drafts';
import Landing from './pages/Landing';
import SettingsPage from './pages/SettingsPage';

function NotFound() {
  const { t } = useI18n();
  return (
    <div className="grid min-h-screen place-items-center px-4 text-center">
      <div>
        <p className="font-display text-7xl font-semibold text-saffron-500">404</p>
        <p className="mt-3 text-lg text-ink-600">{t.common.notFound}</p>
        <Link to="/" className="btn-dark mt-6">{t.common.goHome}</Link>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/app" element={<ProtectedLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="documents/:id" element={<DocumentDetail />} />
        <Route path="drafts" element={<Drafts />} />
        <Route path="deadlines" element={<Deadlines />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
