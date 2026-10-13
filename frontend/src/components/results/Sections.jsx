import {
  AlertTriangle, BookMarked, CalendarClock, CheckCircle2, ChevronDown, ListChecks, Quote, Scale, Sparkles,
} from 'lucide-react';
import { useState } from 'react';
import { fmt, useI18n } from '../../context/I18nContext';
import { daysUntil, formatDate } from '../../utils/format';
import { Spinner } from '../ui';

export function SectionHeader({ icon: Icon, children, count }) {
  return (
    <h2 className="section-title">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-ink-900 text-saffron-300"><Icon className="h-4 w-4" /></span>
      {children}
      {count != null && <span className="chip bg-ink-100 text-ink-600">{count}</span>}
    </h2>
  );
}

export function SummaryCard({ doc }) {
  const { t } = useI18n();
  return (
    <section className="relative overflow-hidden rounded-3xl bg-ink-950 p-6 text-white shadow-lift sm:p-8" aria-labelledby="summary-h">
      <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-saffron-500/25 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -left-16 h-72 w-72 rounded-full bg-sky-500/10 blur-3xl" />
      <div className="relative">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <span className="chip bg-saffron-400/20 text-saffron-200"><Sparkles className="h-3 w-3" />{t.doc.summary}</span>
          {doc.document_type && <span className="chip bg-white/10 text-ink-100">{doc.document_type}</span>}
        </div>
        {doc.title && <h1 id="summary-h" className="mb-3 font-display text-2xl font-semibold leading-snug text-white sm:text-3xl">{doc.title}</h1>}
        <p className="whitespace-pre-line text-base leading-relaxed text-ink-100 sm:text-lg">{doc.summary}</p>
      </div>
    </section>
  );
}

export function KeyPoints({ points }) {
  const { t } = useI18n();
  if (!points?.length) return null;
  return (
    <section className="card-pad" aria-labelledby="kp-h">
      <SectionHeader icon={Quote} count={points.length}><span id="kp-h">{t.doc.keyPoints}</span></SectionHeader>
      <ol className="mt-5 space-y-3">
        {points.map((p, i) => (
          <li key={i} className="flex gap-3.5">
            <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-saffron-100 text-xs font-bold text-saffron-800">{i + 1}</span>
            <p className="leading-relaxed text-ink-700">{p}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

const PRIORITY = {
  high: 'bg-rose-100 text-rose-800',
  medium: 'bg-amber-100 text-amber-800',
  low: 'bg-ink-100 text-ink-600',
};

export function ActionChecklist({ actions }) {
  const { t } = useI18n();
  const [checked, setChecked] = useState({});
  return (
    <section className="card-pad" aria-labelledby="act-h">
      <SectionHeader icon={ListChecks} count={actions?.length || null}><span id="act-h">{t.doc.actions}</span></SectionHeader>
      {!actions?.length ? (
        <p className="mt-4 text-sm text-ink-500">{t.doc.noActions}</p>
      ) : (
        <ul className="mt-5 space-y-3">
          {actions.map((a, i) => {
            const on = !!checked[i];
            return (
              <li key={i}>
                <label className={`flex cursor-pointer items-start gap-3.5 rounded-xl border p-3.5 transition ${on ? 'border-emerald-200 bg-emerald-50/60' : 'border-ink-100 hover:border-ink-200'}`}>
                  <input type="checkbox" className="mt-1 h-4 w-4 shrink-0 accent-emerald-600" checked={on} onChange={() => setChecked((c) => ({ ...c, [i]: !c[i] }))} />
                  <span className="min-w-0 flex-1">
                    <span className={`block leading-relaxed ${on ? 'text-ink-400 line-through' : 'text-ink-800'}`}>{a.action}</span>
                    <span className="mt-1.5 flex flex-wrap items-center gap-2">
                      <span className={`chip ${PRIORITY[a.priority] || PRIORITY.medium}`}>{t.doc.priority[a.priority] || t.doc.priority.medium}</span>
                      {a.due && <span className="chip bg-ink-100 text-ink-600"><CalendarClock className="h-3 w-3" />{a.due}</span>}
                    </span>
                  </span>
                </label>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function urgency(t, dueDate) {
  if (!dueDate) return null;
  const n = daysUntil(dueDate);
  if (n < 0) return { text: fmt(t.doc.overdue, { n: -n }), cls: 'bg-rose-100 text-rose-800', ring: 'ring-rose-200' };
  if (n === 0) return { text: t.doc.today, cls: 'bg-rose-100 text-rose-800', ring: 'ring-rose-200' };
  if (n === 1) return { text: t.doc.tomorrow, cls: 'bg-amber-100 text-amber-800', ring: 'ring-amber-200' };
  if (n <= 7) return { text: fmt(t.doc.daysLeft, { n }), cls: 'bg-amber-100 text-amber-800', ring: 'ring-amber-200' };
  return { text: fmt(t.doc.daysLeft, { n }), cls: 'bg-emerald-100 text-emerald-800', ring: 'ring-emerald-100' };
}

/**
 * Timeline of deadlines from the explanation. `tracked` (persisted deadlines, same order) lets the user
 * mark items done; it is only used when it lines up one-to-one with the AI list.
 */
export function DeadlineTimeline({ deadlines, tracked, onToggle, busyId }) {
  const { t, lang } = useI18n();
  const paired = tracked && tracked.length === deadlines?.length;
  return (
    <section className="card-pad" aria-labelledby="dl-h">
      <SectionHeader icon={CalendarClock} count={deadlines?.length || null}><span id="dl-h">{t.doc.deadlines}</span></SectionHeader>
      {!deadlines?.length ? (
        <p className="mt-4 text-sm text-ink-500">{t.doc.noDeadlines}</p>
      ) : (
        <ol className="relative mt-6 space-y-5 border-l-2 border-dashed border-ink-200 pl-6">
          {deadlines.map((d, i) => {
            const track = paired ? tracked[i] : null;
            const done = track && track.status !== 'PENDING';
            const u = !done && d.date ? urgency(t, d.date) : null;
            const dt = d.date ? new Date(`${d.date}T00:00:00`) : null;
            return (
              <li key={i} className="relative">
                <span className={`absolute -left-[33px] top-3 h-3.5 w-3.5 rounded-full border-2 border-white ring-4 ${done ? 'bg-emerald-500 ring-emerald-100' : u ? u.ring.replace('ring-', 'ring-') + ' bg-saffron-500' : 'bg-ink-300 ring-ink-100'}`} />
                <div className={`flex gap-4 rounded-xl border p-4 transition ${done ? 'border-emerald-200 bg-emerald-50/50' : 'border-ink-100 bg-white'}`}>
                  <div className="w-14 shrink-0 text-center">
                    {dt ? (
                      <div className="rounded-lg bg-ink-900 px-1 py-1.5 text-white">
                        <div className="text-[10px] font-semibold uppercase tracking-wider text-saffron-300">{formatDate(d.date, lang, { month: 'short' })}</div>
                        <div className="font-display text-xl font-semibold leading-none">{dt.getDate()}</div>
                        <div className="mt-0.5 text-[10px] text-ink-300">{dt.getFullYear()}</div>
                      </div>
                    ) : (
                      <div className="grid h-full min-h-[3.5rem] place-items-center rounded-lg bg-ink-100 text-ink-500"><CalendarClock className="h-6 w-6" /></div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className={`font-medium leading-relaxed ${done ? 'text-ink-400 line-through' : 'text-ink-900'}`}>{d.description}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      {d.period && <span className="chip bg-sky-100 text-sky-800">{d.period}</span>}
                      {u && <span className={`chip ${u.cls}`}>{u.text}</span>}
                      {done && <span className="chip bg-emerald-100 text-emerald-800"><CheckCircle2 className="h-3 w-3" />{t.deadlines.done}</span>}
                    </div>
                    {d.source_text && <p className="mt-2 border-l-2 border-ink-200 pl-3 text-xs italic text-ink-500">“{d.source_text}”</p>}
                    {track && onToggle && (
                      <button className="mt-3 text-xs font-semibold text-saffron-700 hover:underline disabled:opacity-50" disabled={busyId === track.id} onClick={() => onToggle(track)}>
                        {busyId === track.id ? <Spinner className="inline h-3 w-3" /> : done ? t.doc.undo : t.doc.markDone}
                      </button>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}

export function LegalReferences({ references, sourceIds }) {
  const { t } = useI18n();
  return (
    <section className="card-pad" aria-labelledby="ref-h">
      <SectionHeader icon={Scale} count={references?.length || null}><span id="ref-h">{t.doc.references}</span></SectionHeader>
      {!references?.length ? (
        <p className="mt-4 text-sm text-ink-500">{t.doc.noRefs}</p>
      ) : (
        <ul className="mt-5 grid gap-3 sm:grid-cols-2">
          {references.map((r, i) => (
            <li key={i} className="rounded-xl border border-ink-100 bg-gradient-to-b from-white to-ink-50/60 p-4">
              <p className="font-display text-base font-semibold text-ink-950">{r.citation}</p>
              {r.explanation && <p className="mt-1.5 text-sm leading-relaxed text-ink-600">{r.explanation}</p>}
              <div className="mt-3">
                {r.source_id && sourceIds.has(r.source_id) ? (
                  <a href={`#source-${r.source_id}`} className="chip bg-emerald-100 text-emerald-800 hover:bg-emerald-200">
                    <BookMarked className="h-3 w-3" />{r.source_id} · {t.doc.cited}
                  </a>
                ) : (
                  <span className="chip bg-ink-100 text-ink-500">{t.doc.fromDoc}</span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

const KIND = { act: 'Act', rule: 'Rule', notification: 'Notification', judgment: 'Judgment', other: 'Source' };
const KIND_STYLE = {
  act: 'bg-indigo-100 text-indigo-800', rule: 'bg-sky-100 text-sky-800', notification: 'bg-teal-100 text-teal-800',
  judgment: 'bg-purple-100 text-purple-800', other: 'bg-ink-100 text-ink-600',
};

export function SourceCitations({ sources }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(null);
  return (
    <section className="card-pad" aria-labelledby="src-h">
      <SectionHeader icon={BookMarked} count={sources?.length || null}><span id="src-h">{t.doc.sources}</span></SectionHeader>
      {!sources?.length ? (
        <p className="mt-4 text-sm text-ink-500">{t.doc.noSources}</p>
      ) : (
        <ul className="mt-5 divide-y divide-ink-100 overflow-hidden rounded-xl border border-ink-100">
          {sources.map((s) => {
            const isOpen = open === s.source_id;
            return (
              <li key={s.source_id} id={`source-${s.source_id}`} className={s.cited ? 'bg-emerald-50/40' : 'bg-white'}>
                <button className="flex w-full items-start gap-3 p-4 text-left" onClick={() => setOpen(isOpen ? null : s.source_id)} aria-expanded={isOpen}>
                  <span className="mt-0.5 grid h-6 w-8 shrink-0 place-items-center rounded-md bg-ink-900 text-[11px] font-bold text-white">{s.source_id}</span>
                  <span className="min-w-0 flex-1">
                    <span className="block font-semibold text-ink-900">{s.citation}</span>
                    <span className="mt-1.5 flex flex-wrap gap-1.5">
                      <span className={`chip ${KIND_STYLE[s.kind] || KIND_STYLE.other}`}>{KIND[s.kind] || KIND.other}</span>
                      <span className="chip bg-ink-100 text-ink-600">{s.jurisdiction}</span>
                      <span className={`chip ${s.cited ? 'bg-emerald-100 text-emerald-800' : 'bg-ink-100 text-ink-500'}`}>{s.cited ? t.doc.cited : t.doc.related}</span>
                    </span>
                  </span>
                  <ChevronDown className={`mt-1 h-4 w-4 shrink-0 text-ink-400 transition ${isOpen ? 'rotate-180' : ''}`} />
                </button>
                {isOpen && <p className="animate-fade-in whitespace-pre-line border-t border-ink-100 bg-white px-4 py-3.5 text-sm leading-relaxed text-ink-600">{s.snippet}</p>}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

export function Caveats({ items }) {
  const { t } = useI18n();
  if (!items?.length) return null;
  return (
    <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5" aria-labelledby="cv-h">
      <h2 id="cv-h" className="mb-2 flex items-center gap-2 font-semibold text-amber-900"><AlertTriangle className="h-4 w-4" />{t.doc.caveats}</h2>
      <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed text-amber-900/90">
        {items.map((c, i) => <li key={i}>{c}</li>)}
      </ul>
    </section>
  );
}
