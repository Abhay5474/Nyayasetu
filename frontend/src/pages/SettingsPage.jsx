import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { errorMessage } from '../api/client';
import { UserApi } from '../api/endpoints';
import { Alert, Field, Segmented, Spinner, Toggle } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';

export default function SettingsPage() {
  const { t } = useI18n();
  const { user, updateProfile, logout } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    fullName: user.fullName, phone: user.phone || '', preferredLanguage: user.preferredLanguage,
    emailAlerts: user.emailAlerts, smsAlerts: user.smsAlerts,
  });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [error, setError] = useState(null);

  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      const body = { ...form, phone: form.phone.trim() || undefined };
      await updateProfile(body);
      setMsg(t.settings.saved);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function deleteAccount() {
    if (!window.confirm(t.settings.confirmDelete)) return;
    try {
      await UserApi.remove();
      logout();
      navigate('/');
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <h1 className="font-display text-3xl font-semibold">{t.settings.title}</h1>
      <form onSubmit={save} className="space-y-8">
        {error && <Alert onClose={() => setError(null)}>{error}</Alert>}
        {msg && <Alert kind="success" onClose={() => setMsg(null)}>{msg}</Alert>}

        <section className="card-pad space-y-5">
          <h2 className="font-display text-lg font-semibold">{t.settings.profile}</h2>
          <Field label={t.auth.fullName}><input className="input" required maxLength={120} value={form.fullName} onChange={(e) => setForm({ ...form, fullName: e.target.value })} /></Field>
          <Field label={t.auth.email}><input className="input bg-ink-50" disabled value={user.email} /></Field>
          <Field label={t.auth.phone} hint={t.auth.phoneHint}>
            <input className="input" type="tel" placeholder="+91…" pattern="^\+[1-9]\d{7,14}$" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </Field>
          <Field label={t.settings.prefLang}>
            <Segmented label={t.settings.prefLang} value={form.preferredLanguage} onChange={(v) => setForm({ ...form, preferredLanguage: v })} options={[{ value: 'en', label: 'English' }, { value: 'mr', label: 'मराठी' }]} />
          </Field>
        </section>

        <section className="card-pad space-y-5">
          <div>
            <h2 className="font-display text-lg font-semibold">{t.settings.alerts}</h2>
            <p className="mt-1 text-sm text-ink-500">{t.settings.alertsSub}</p>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="font-medium text-ink-800">{t.settings.emailAlerts}</span>
            <Toggle label={t.settings.emailAlerts} checked={form.emailAlerts} onChange={(v) => setForm({ ...form, emailAlerts: v })} />
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="font-medium text-ink-800">{t.settings.smsAlerts}</span>
            <Toggle label={t.settings.smsAlerts} checked={form.smsAlerts} onChange={(v) => setForm({ ...form, smsAlerts: v })} />
          </div>
        </section>

        <button className="btn-primary !px-6 !py-3" disabled={busy}>{busy && <Spinner />}{t.settings.save}</button>
      </form>

      <section className="rounded-2xl border border-rose-200 bg-rose-50/50 p-5 sm:p-6">
        <h2 className="font-display text-lg font-semibold text-rose-900">{t.settings.danger}</h2>
        <p className="mt-1 text-sm text-rose-800/80">{t.settings.deleteBody}</p>
        <button className="btn-danger mt-4" onClick={deleteAccount}>{t.settings.deleteAccount}</button>
      </section>
    </div>
  );
}
