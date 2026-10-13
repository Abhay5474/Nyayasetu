import { ArrowLeft, ExternalLink, FileText, MessageSquareText, Printer, RefreshCcw, XCircle } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { errorMessage } from '../api/client';
import { DeadlineApi, DocumentApi } from '../api/endpoints';
import ChatPanel from '../components/ChatPanel';
import ProcessingPanel from '../components/results/ProcessingPanel';
import {
  ActionChecklist, Caveats, DeadlineTimeline, KeyPoints, LegalReferences, SourceCitations, SummaryCard,
} from '../components/results/Sections';
import StatusBadge from '../components/StatusBadge';
import { Alert, Segmented, Spinner } from '../components/ui';
import { fmt, useI18n } from '../context/I18nContext';
import { usePolling } from '../hooks';
import { formatBytes, formatDateTime } from '../utils/format';

const LANG_LABEL = { en: 'English', mr: 'मराठी' };

export default function DocumentDetail() {
  const { id } = useParams();
  const { t, lang: uiLang } = useI18n();
  const [params, setParams] = useSearchParams();

  const [doc, setDoc] = useState(null);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [tracked, setTracked] = useState([]);
  const [busyDeadline, setBusyDeadline] = useState(null);
  const [starting, setStarting] = useState(false);

  const outLang = params.get('lang') === 'mr' || params.get('lang') === 'en' ? params.get('lang') : null;
  const [fallbackLang, setFallbackLang] = useState(null);
  const lang = outLang || fallbackLang || uiLang;
  const tab = params.get('tab') === 'ask' ? 'ask' : 'summary';
  const textReady = doc?.pageCount != null; // text was extracted, so questions can be answered

  const loadDoc = useCallback(async () => {
    try {
      const d = await DocumentApi.get(id);
      setDoc(d);
      setError(null);
      return d;
    } catch (e) {
      setError(errorMessage(e));
      return null;
    }
  }, [id]);

  useEffect(() => { loadDoc(); }, [loadDoc]);

  // When opened without ?lang=, prefer a language that already has a finished explanation.
  useEffect(() => {
    if (!doc || outLang) return;
    const done = doc.results.filter((r) => r.status === 'COMPLETED').map((r) => r.language);
    if (done.length && !done.includes(uiLang)) setFallbackLang(done[0]);
  }, [doc, outLang, uiLang]);

  const langState = doc?.results.find((r) => r.language === lang);
  const processing = doc?.status === 'PROCESSING' || langState?.status === 'PROCESSING';
  usePolling(loadDoc, 2500, !!processing);

  const completedAt = langState?.status === 'COMPLETED';
  useEffect(() => {
    let cancelled = false;
    setResult(null);
    if (!completedAt) return undefined;
    DocumentApi.result(id, lang)
      .then((r) => !cancelled && setResult(r))
      .catch((e) => !cancelled && setError(errorMessage(e)));
    DocumentApi.deadlines(id).then((d) => !cancelled && setTracked(d)).catch(() => {});
    return () => { cancelled = true; };
  }, [id, lang, completedAt]);

  function pickLang(l) {
    setParams((p) => { const n = new URLSearchParams(p); n.set('lang', l); return n; }, { replace: true });
  }

  function pickTab(next) {
    setParams((p) => { const n = new URLSearchParams(p); if (next === 'ask') n.set('tab', 'ask'); else n.delete('tab'); return n; }, { replace: true });
  }

  async function generate(force = false) {
    setStarting(true);
    setError(null);
    try {
      setDoc(await DocumentApi.process(id, lang, force));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setStarting(false);
    }
  }

  async function toggleDeadline(item) {
    setBusyDeadline(item.id);
    try {
      const updated = await DeadlineApi.setStatus(item.id, item.status === 'PENDING' ? 'DONE' : 'PENDING');
      setTracked((list) => list.map((x) => (x.id === updated.id ? updated : x)));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusyDeadline(null);
    }
  }

  async function openOriginal() {
    try {
      const blob = await DocumentApi.fileBlob(id);
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank', 'noopener');
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  const payload = result?.result;
  const out = payload?.document;
  const sourceIds = useMemo(() => new Set((payload?.sources || []).map((s) => s.source_id)), [payload]);

  if (!doc && !error) return <div className="space-y-4"><div className="skeleton h-10 w-64" /><div className="skeleton h-64" /></div>;
  if (!doc) return <Alert>{error}</Alert>;

  return (
    <div className="space-y-8">
      <div className="no-print">
        <Link to="/app" className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 hover:text-ink-900"><ArrowLeft className="h-4 w-4" />{t.doc.back}</Link>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="truncate font-display text-2xl font-semibold sm:text-3xl" title={doc.originalFilename}>{doc.originalFilename}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2.5 text-sm text-ink-500">
            <StatusBadge status={langState?.status || doc.status} />
            <span>{formatDateTime(doc.createdAt, uiLang)}</span>
          </div>
        </div>
        <div className="no-print flex flex-wrap items-center gap-3">
          <span className="hidden text-sm font-medium text-ink-600 sm:inline">{t.doc.language}</span>
          <Segmented label={t.doc.language} value={lang} onChange={pickLang} options={[{ value: 'en', label: 'English' }, { value: 'mr', label: 'मराठी' }]} />
          {out && <button className="btn-outline" onClick={() => window.print()}><Printer className="h-4 w-4" />{t.doc.printable}</button>}
        </div>
      </div>

      <div className="no-print flex gap-1 border-b border-ink-200" role="tablist">
        {[['summary', t.chat.summaryTab, FileText], ['ask', t.chat.tab, MessageSquareText]].map(([key, label, Icon]) => (
          <button key={key} role="tab" aria-selected={tab === key} onClick={() => pickTab(key)}
            className={`-mb-px inline-flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold transition ${tab === key ? 'border-saffron-500 text-ink-950' : 'border-transparent text-ink-500 hover:text-ink-800'}`}>
            <Icon className="h-4 w-4" />{label}
          </button>
        ))}
      </div>

      {error && <Alert onClose={() => setError(null)}>{error}</Alert>}

      {tab === 'ask' ? (
        <div className="mx-auto max-w-3xl"><ChatPanel docId={id} lang={lang} ready={textReady} /></div>
      ) : processing ? (
        <ProcessingPanel />
      ) : langState?.status === 'FAILED' ? (
        <div className="card flex flex-col items-center px-6 py-12 text-center">
          <XCircle className="mb-4 h-12 w-12 text-rose-500" />
          <h2 className="font-display text-xl font-semibold">{t.doc.failedTitle}</h2>
          <p className="mt-2 max-w-md text-sm text-ink-600">{langState.error}</p>
          <button className="btn-primary mt-6" onClick={() => generate(true)} disabled={starting}>{starting ? <Spinner /> : <RefreshCcw className="h-4 w-4" />}{t.doc.retry}</button>
        </div>
      ) : !langState ? (
        <div className="card flex flex-col items-center px-6 py-12 text-center">
          <FileText className="mb-4 h-12 w-12 text-ink-300" />
          <button className="btn-primary" onClick={() => generate(false)} disabled={starting}>
            {starting ? <><Spinner />{t.doc.generating}</> : fmt(t.doc.generate, { lang: LANG_LABEL[lang] })}
          </button>
        </div>
      ) : !out ? (
        <div className="space-y-4"><div className="skeleton h-48" /><div className="skeleton h-40" /></div>
      ) : (
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
          <div className="space-y-6">
            <div className="animate-fade-up"><SummaryCard doc={out} /></div>
            <KeyPoints points={out.key_points} />
            <ActionChecklist actions={out.required_actions} />
            <DeadlineTimeline deadlines={out.deadlines} tracked={tracked} onToggle={toggleDeadline} busyId={busyDeadline} />
            <LegalReferences references={out.legal_references} sourceIds={sourceIds} />
            <SourceCitations sources={payload.sources} />
            <Caveats items={out.caveats} />
            <p className="rounded-xl bg-ink-100 px-4 py-3 text-xs leading-relaxed text-ink-600">{t.doc.disclaimer}</p>
          </div>

          <aside className="no-print space-y-4 lg:sticky lg:top-24 lg:self-start">
            <div className="card-pad">
              <h2 className="mb-4 font-display text-base font-semibold">{t.doc.info}</h2>
              <dl className="space-y-3 text-sm">
                <Row k={t.doc.type} v={out.document_type} />
                <Row k={t.doc.pagesLabel} v={doc.pageCount} />
                <Row k={t.doc.method} v={t.doc[doc.extractionMethod] || doc.extractionMethod} />
                <Row k={t.dash.outputLang} v={LANG_LABEL[lang]} />
                <Row k={t.doc.uploaded} v={formatDateTime(doc.createdAt, uiLang)} />
                <Row k="Size" v={formatBytes(doc.sizeBytes)} />
                <Row k={t.doc.model} v={result.model} />
              </dl>
              <button className="btn-primary mt-5 w-full" onClick={() => pickTab('ask')}><MessageSquareText className="h-4 w-4" />{t.chat.tab}</button>
              <button className="btn-outline mt-3 w-full" onClick={openOriginal}><ExternalLink className="h-4 w-4" />{t.doc.viewOriginal}</button>
              {result.model === 'mock-extractive' && <div className="mt-4"><Alert kind="warn">{t.doc.demoMode}</Alert></div>}
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

function Row({ k, v }) {
  if (v == null || v === '') return null;
  return (
    <div className="flex items-baseline justify-between gap-4">
      <dt className="shrink-0 text-ink-500">{k}</dt>
      <dd className="min-w-0 truncate text-right font-medium text-ink-900" title={String(v)}>{v}</dd>
    </div>
  );
}
