import { useEffect, useState } from 'react';
import { useI18n } from '../../context/I18nContext';
import { CheckCircle2 } from 'lucide-react';
import { Spinner } from '../ui';

/** Indeterminate progress: the backend reports only "processing", so steps advance on a timer for feedback. */
export default function ProcessingPanel() {
  const { t } = useI18n();
  const [step, setStep] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setStep((s) => Math.min(s + 1, t.doc.steps.length - 1)), 9000);
    return () => clearInterval(id);
  }, [t.doc.steps.length]);

  return (
    <div className="card overflow-hidden" role="status" aria-live="polite">
      <div className="h-1 w-full animate-shimmer bg-gradient-to-r from-saffron-200 via-saffron-500 to-saffron-200" style={{ backgroundSize: '200% 100%' }} />
      <div className="px-6 py-10 text-center sm:py-14">
        <div className="relative mx-auto mb-6 grid h-16 w-16 place-items-center rounded-2xl bg-ink-950 text-saffron-300">
          <span className="absolute inset-0 rounded-2xl bg-saffron-400/40 animate-pulse-ring" />
          <Spinner className="relative h-7 w-7" />
        </div>
        <h2 className="font-display text-xl font-semibold text-ink-950">{t.doc.processingTitle}</h2>
        <p className="mx-auto mt-2 max-w-md text-sm text-ink-500">{t.doc.processingSub}</p>
        <ol className="mx-auto mt-8 flex max-w-lg flex-col gap-3 text-left sm:flex-row sm:gap-6">
          {t.doc.steps.map((s, i) => (
            <li key={s} className={`flex flex-1 items-center gap-2.5 text-sm transition ${i <= step ? 'text-ink-900' : 'text-ink-300'}`}>
              {i < step ? <CheckCircle2 className="h-5 w-5 text-emerald-500" /> : i === step ? <Spinner className="h-5 w-5 text-saffron-500" /> : <span className="h-5 w-5 rounded-full border-2 border-ink-200" />}
              {s}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
