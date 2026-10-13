import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { strings } from '../i18n/strings';

const I18nContext = createContext(null);
const KEY = 'nyayasetu.ui-lang';

function initialLang() {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === 'en' || saved === 'mr') return saved;
  } catch { /* storage unavailable */ }
  return typeof navigator !== 'undefined' && navigator.language?.toLowerCase().startsWith('mr') ? 'mr' : 'en';
}

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(initialLang);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((l) => {
    setLangState(l);
    try { localStorage.setItem(KEY, l); } catch { /* ignore */ }
  }, []);

  const value = useMemo(() => ({ lang, setLang, t: strings[lang] }), [lang, setLang]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used inside <I18nProvider>');
  return ctx;
}

/** Replace {placeholders} in a template string. */
export function fmt(template, vars = {}) {
  return template.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? ''));
}
