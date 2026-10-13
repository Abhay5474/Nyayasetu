import { Languages } from 'lucide-react';
import { useI18n } from '../context/I18nContext';

export default function UiLangSwitch({ dark = false }) {
  const { lang, setLang } = useI18n();
  const next = lang === 'en' ? 'mr' : 'en';
  return (
    <button
      onClick={() => setLang(next)}
      aria-label={next === 'mr' ? 'मराठीत पहा' : 'Switch to English'}
      className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-semibold transition ${
        dark ? 'text-ink-100 hover:bg-white/10' : 'text-ink-700 hover:bg-ink-100'
      }`}
    >
      <Languages className="h-4 w-4" />
      <span lang={next}>{next === 'mr' ? 'मराठी' : 'English'}</span>
    </button>
  );
}
