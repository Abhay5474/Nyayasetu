import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { errorMessage } from '../api/client';
import Logo from '../components/Logo';
import UiLangSwitch from '../components/UiLangSwitch';
import { Alert, Field, Spinner } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';

function Shell({ title, subtitle, children, footer }) {
  const { t } = useI18n();
  return (
    <div className="grid min-h-screen lg:grid-cols-[1fr_1.1fr]">
      <div className="relative hidden overflow-hidden bg-ink-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute -left-24 top-1/3 h-96 w-96 rounded-full bg-saffron-500/25 blur-[110px]" />
        <div className="pointer-events-none absolute -right-24 bottom-0 h-96 w-96 rounded-full bg-indigo-500/20 blur-[110px]" />
        <Link to="/" className="relative"><Logo name={t.appName} dark /></Link>
        <div className="relative">
          <p className="font-display text-4xl font-semibold leading-tight !text-white">{t.landing.title}</p>
          <p className="mt-5 max-w-md text-ink-200">{t.landing.subtitle}</p>
        </div>
        <p className="relative text-xs text-ink-400">{t.landing.disclaimer}</p>
      </div>
      <div className="flex flex-col px-4 py-6 sm:px-10">
        <div className="flex items-center justify-between lg:justify-end">
          <Link to="/" className="lg:hidden"><Logo name={t.appName} /></Link>
          <UiLangSwitch />
        </div>
        <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-10">
          <h1 className="font-display text-3xl font-semibold">{title}</h1>
          <p className="mt-2 text-ink-500">{subtitle}</p>
          <div className="mt-8">{children}</div>
          <p className="mt-8 text-center text-sm text-ink-500">{footer}</p>
        </div>
      </div>
    </div>
  );
}

export function LoginPage() {
  const { t } = useI18n();
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: '', password: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  if (isAuthenticated) return <Navigate to="/app" replace />;

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(form);
      navigate(location.state?.from || '/app', { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Shell title={t.auth.loginTitle} subtitle={t.auth.loginSub} footer={<>{t.auth.noAccount} <Link className="font-semibold text-saffron-700 hover:underline" to="/register">{t.nav.getStarted}</Link></>}>
      <form onSubmit={submit} className="space-y-5">
        {error && <Alert>{error}</Alert>}
        <Field label={t.auth.email}>
          <input className="input" type="email" autoComplete="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </Field>
        <Field label={t.auth.password}>
          <input className="input" type="password" autoComplete="current-password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </Field>
        <button className="btn-primary w-full !py-3" disabled={busy}>{busy && <Spinner />}{t.auth.signIn}</button>
      </form>
    </Shell>
  );
}

export function RegisterPage() {
  const { t, lang } = useI18n();
  const { register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ fullName: '', email: '', password: '', phone: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  if (isAuthenticated) return <Navigate to="/app" replace />;
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await register({ ...form, phone: form.phone.trim() || undefined, preferredLanguage: lang });
      navigate('/app', { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Shell title={t.auth.registerTitle} subtitle={t.auth.registerSub} footer={<>{t.auth.haveAccount} <Link className="font-semibold text-saffron-700 hover:underline" to="/login">{t.auth.signIn}</Link></>}>
      <form onSubmit={submit} className="space-y-5">
        {error && <Alert>{error}</Alert>}
        <Field label={t.auth.fullName}><input className="input" autoComplete="name" required maxLength={120} value={form.fullName} onChange={set('fullName')} /></Field>
        <Field label={t.auth.email}><input className="input" type="email" autoComplete="email" required value={form.email} onChange={set('email')} /></Field>
        <Field label={t.auth.password} hint={t.auth.passwordHint}>
          <input className="input" type="password" autoComplete="new-password" required minLength={8} maxLength={72} value={form.password} onChange={set('password')} />
        </Field>
        <Field label={t.auth.phone} hint={t.auth.phoneHint}>
          <input className="input" type="tel" autoComplete="tel" placeholder="+91…" pattern="^\+[1-9]\d{7,14}$" value={form.phone} onChange={set('phone')} />
        </Field>
        <button className="btn-primary w-full !py-3" disabled={busy}>{busy && <Spinner />}{t.auth.createAccount}</button>
      </form>
    </Shell>
  );
}
