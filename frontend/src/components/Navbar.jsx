import { CalendarClock, LayoutDashboard, LogOut, Menu, Settings, X } from 'lucide-react';
import { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import Logo from './Logo';
import UiLangSwitch from './UiLangSwitch';

export default function Navbar() {
  const { t } = useI18n();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const links = [
    { to: '/app', label: t.nav.dashboard, icon: LayoutDashboard, end: true },
    { to: '/app/deadlines', label: t.nav.deadlines, icon: CalendarClock },
    { to: '/app/settings', label: t.nav.settings, icon: Settings },
  ];
  const linkClass = ({ isActive }) =>
    `inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition ${
      isActive ? 'bg-ink-900 text-white' : 'text-ink-600 hover:bg-ink-100 hover:text-ink-900'
    }`;

  return (
    <header className="no-print sticky top-0 z-30 border-b border-ink-100/80 bg-paper/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link to="/app" aria-label={t.appName}>
          <Logo name={t.appName} />
        </Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
              <l.icon className="h-4 w-4" />
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <UiLangSwitch />
          <div className="mx-1 h-6 w-px bg-ink-200" />
          <span className="max-w-[10rem] truncate text-sm font-medium text-ink-600" title={user?.email}>{user?.fullName}</span>
          <button
            className="btn-ghost !px-2.5"
            aria-label={t.nav.signOut}
            title={t.nav.signOut}
            onClick={() => { logout(); navigate('/'); }}
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>

        <button className="btn-ghost !px-2.5 md:hidden" onClick={() => setOpen((o) => !o)} aria-label="Menu" aria-expanded={open}>
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <div className="animate-fade-in border-t border-ink-100 bg-paper px-4 pb-4 pt-2 md:hidden">
          <nav className="flex flex-col gap-1" aria-label="Mobile">
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end} className={linkClass} onClick={() => setOpen(false)}>
                <l.icon className="h-4 w-4" />
                {l.label}
              </NavLink>
            ))}
          </nav>
          <div className="mt-3 flex items-center justify-between border-t border-ink-100 pt-3">
            <UiLangSwitch />
            <button className="btn-outline" onClick={() => { logout(); navigate('/'); }}>
              <LogOut className="h-4 w-4" />
              {t.nav.signOut}
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
