import { CalendarCheck2, CalendarClock, FileText } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage } from '../api/client';
import { DeadlineApi } from '../api/endpoints';
import { Alert, Spinner } from '../components/ui';
import { fmt, useI18n } from '../context/I18nContext';
import { daysUntil, formatDate, groupDeadlines } from '../utils/format';

export default function Deadlines() {
  const { t, lang } = useI18n();
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(null);

  useEffect(() => {
    DeadlineApi.list().then(setItems).catch((e) => setError(errorMessage(e)));
  }, []);

  const groups = useMemo(() => groupDeadlines(items || []), [items]);

  async function toggle(d) {
    setBusy(d.id);
    try {
      const updated = await DeadlineApi.setStatus(d.id, d.status === 'PENDING' ? 'DONE' : 'PENDING');
      setItems((list) => list.map((x) => (x.id === updated.id ? updated : x)));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(null);
    }
  }

  const sections = [
    { key: 'overdue', title: t.deadlines.overdue, tone: 'text-rose-700' },
    { key: 'week', title: t.deadlines.week, tone: 'text-amber-700' },
    { key: 'later', title: t.deadlines.later, tone: 'text-ink-800' },
    { key: 'noDate', title: t.deadlines.noDate, tone: 'text-sky-700' },
    { key: 'done', title: t.deadlines.done, tone: 'text-emerald-700' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-semibold">{t.deadlines.title}</h1>
        <p className="mt-1 text-ink-500">{t.deadlines.sub}</p>
      </div>
      {error && <Alert onClose={() => setError(null)}>{error}</Alert>}
      {items === null ? (
        <div className="space-y-3">{[0, 1, 2].map((i) => <div key={i} className="skeleton h-20" />)}</div>
      ) : items.length === 0 ? (
        <div className="card grid place-items-center px-6 py-14 text-center">
          <CalendarClock className="mb-3 h-10 w-10 text-ink-300" />
          <p className="max-w-sm text-sm text-ink-500">{t.deadlines.empty}</p>
        </div>
      ) : (
        sections.filter((s) => groups[s.key].length > 0).map((s) => (
          <section key={s.key}>
            <h2 className={`mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wider ${s.tone}`}>
              {s.title} <span className="chip bg-ink-100 text-ink-600 normal-case tracking-normal">{groups[s.key].length}</span>
            </h2>
            <ul className="space-y-3">
              {groups[s.key].map((d) => {
                const left = d.dueDate ? daysUntil(d.dueDate) : null;
                return (
                  <li key={d.id} className="card flex items-start gap-4 p-4">
                    <button
                      onClick={() => toggle(d)}
                      disabled={busy === d.id}
                      className={`mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full border-2 transition ${d.status === 'DONE' ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-ink-300 hover:border-emerald-500'}`}
                      aria-label={d.status === 'DONE' ? t.doc.undo : t.doc.markDone}
                      title={d.status === 'DONE' ? t.doc.undo : t.doc.markDone}
                    >
                      {busy === d.id ? <Spinner className="h-3 w-3" /> : d.status === 'DONE' ? <CalendarCheck2 className="h-3.5 w-3.5" /> : null}
                    </button>
                    <div className="min-w-0 flex-1">
                      <p className={`font-medium leading-relaxed ${d.status === 'DONE' ? 'text-ink-400 line-through' : 'text-ink-900'}`}>{d.description}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                        {d.dueDate && <span className="chip bg-ink-900 text-white">{formatDate(d.dueDate, lang)}</span>}
                        {d.status === 'PENDING' && left != null && (
                          <span className={`chip ${left < 0 ? 'bg-rose-100 text-rose-800' : left <= 7 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>
                            {left < 0 ? fmt(t.doc.overdue, { n: -left }) : left === 0 ? t.doc.today : fmt(t.doc.daysLeft, { n: left })}
                          </span>
                        )}
                        {d.period && <span className="chip bg-sky-100 text-sky-800">{d.period}</span>}
                        <Link to={`/app/documents/${d.documentId}`} className="inline-flex max-w-[14rem] items-center gap-1 truncate text-ink-500 hover:text-saffron-700">
                          <FileText className="h-3 w-3 shrink-0" />{d.documentName}
                        </Link>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>
        ))
      )}
    </div>
  );
}
