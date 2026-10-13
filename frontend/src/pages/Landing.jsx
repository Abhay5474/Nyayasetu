import { ArrowRight, BookMarked, CalendarClock, FileScan, Languages, ShieldCheck, UploadCloud, Search, Lightbulb } from 'lucide-react';
import { Link } from 'react-router-dom';
import Logo from '../components/Logo';
import UiLangSwitch from '../components/UiLangSwitch';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';

const FEATURE_ICONS = [FileScan, Languages, BookMarked, CalendarClock];
const STEP_ICONS = [UploadCloud, Search, Lightbulb];

export default function Landing() {
  const { t } = useI18n();
  const { isAuthenticated } = useAuth();
  const L = t.landing;

  return (
    <div className="min-h-screen bg-paper">
      <section className="relative isolate overflow-hidden bg-ink-950 text-white">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -left-32 top-[-10rem] h-[32rem] w-[32rem] rounded-full bg-saffron-500/25 blur-[120px]" />
          <div className="absolute -right-40 top-40 h-[30rem] w-[30rem] rounded-full bg-indigo-500/20 blur-[120px]" />
          <svg className="absolute inset-0 h-full w-full opacity-[.07]" aria-hidden="true">
            <defs><pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="white" strokeWidth="1" /></pattern></defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        <header className="mx-auto flex h-20 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Logo name={t.appName} dark />
          <nav className="flex items-center gap-1 sm:gap-2">
            <UiLangSwitch dark />
            {isAuthenticated ? (
              <Link to="/app" className="btn-primary">{t.nav.dashboard}</Link>
            ) : (
              <>
                <Link to="/login" className="btn-ghost !text-ink-100 hover:!bg-white/10">{t.nav.signIn}</Link>
                <Link to="/register" className="btn-primary">{t.nav.getStarted}</Link>
              </>
            )}
          </nav>
        </header>

        <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-24 pt-10 sm:px-6 lg:grid-cols-[1.05fr_.95fr] lg:pt-16">
          <div className="animate-fade-up">
            <span className="chip mb-6 border border-white/15 bg-white/5 text-saffron-200 backdrop-blur"><ShieldCheck className="h-3.5 w-3.5" />{L.badge}</span>
            <h1 className="font-display text-4xl font-semibold leading-[1.08] tracking-tight !text-white sm:text-5xl lg:text-[3.5rem]">{L.title}</h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-200">{L.subtitle}</p>
            <div className="mt-9 flex flex-wrap items-center gap-3">
              <Link to={isAuthenticated ? '/app' : '/register'} className="btn-primary !px-6 !py-3.5 text-base">{L.ctaPrimary}<ArrowRight className="h-4 w-4" /></Link>
              <a href="#how" className="btn !px-5 !py-3.5 text-base text-ink-100 hover:bg-white/10">{L.ctaSecondary}</a>
            </div>
          </div>

          <div className="relative animate-fade-up [animation-delay:.15s]" aria-hidden="true">
            <div className="absolute -inset-4 rounded-[2rem] bg-gradient-to-tr from-saffron-500/20 to-indigo-500/20 blur-2xl" />
            <div className="relative space-y-4">
              <div className="rotate-[-1.5deg] rounded-2xl border border-white/10 bg-white/[.06] p-5 backdrop-blur-xl">
                <span className="chip mb-3 bg-rose-400/15 text-rose-200">{L.before}</span>
                <p className="font-serif text-[15px] italic leading-relaxed text-ink-200">{L.legalese}</p>
              </div>
              <div className="ml-6 animate-float rounded-2xl bg-white p-5 shadow-lift">
                <span className="chip mb-3 bg-emerald-100 text-emerald-800">{L.after}</span>
                <p className="text-[17px] font-medium leading-relaxed text-ink-900">{L.plain}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="chip bg-saffron-100 text-saffron-800"><CalendarClock className="h-3 w-3" />30 days</span>
                  <span className="chip bg-indigo-100 text-indigo-800"><BookMarked className="h-3 w-3" />RTI Act · Sec 19(1)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <h2 className="mx-auto max-w-2xl text-center font-display text-3xl font-semibold sm:text-4xl">{L.featuresTitle}</h2>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {L.features.map((f, i) => {
            const Icon = FEATURE_ICONS[i];
            return (
              <div key={f.title} className="card group p-6 transition duration-300 hover:-translate-y-1 hover:shadow-lift">
                <div className="mb-4 grid h-11 w-11 place-items-center rounded-xl bg-ink-950 text-saffron-300 transition group-hover:bg-saffron-500 group-hover:text-ink-950"><Icon className="h-5 w-5" /></div>
                <h3 className="font-display text-lg font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-600">{f.body}</p>
              </div>
            );
          })}
        </div>
      </section>

      <section id="how" className="border-y border-ink-100 bg-white py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-center font-display text-3xl font-semibold sm:text-4xl">{L.stepsTitle}</h2>
          <ol className="mt-12 grid gap-8 md:grid-cols-3">
            {L.steps.map((s, i) => {
              const Icon = STEP_ICONS[i];
              return (
                <li key={s.title} className="relative text-center md:text-left">
                  <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-saffron-100 text-saffron-700 md:mx-0"><Icon className="h-6 w-6" /></div>
                  <span className="font-display text-sm font-semibold text-saffron-600">0{i + 1}</span>
                  <h3 className="font-display text-xl font-semibold">{s.title}</h3>
                  <p className="mt-2 text-ink-600">{s.body}</p>
                </li>
              );
            })}
          </ol>
        </div>
      </section>

      <footer className="mx-auto max-w-4xl px-4 py-14 text-center sm:px-6">
        <Logo name={t.appName} />
        <p className="mt-5 text-sm leading-relaxed text-ink-500">{L.disclaimer}</p>
      </footer>
    </div>
  );
}
