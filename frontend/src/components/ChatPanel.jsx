import { BookMarked, MessageSquareText, Quote, SendHorizonal, Sparkles, Trash2, TriangleAlert } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { errorMessage } from '../api/client';
import { ChatApi } from '../api/endpoints';
import { useI18n } from '../context/I18nContext';
import { Alert, Spinner } from './ui';
import { ProvenanceBadge, ProvenanceDetails } from './results/Provenance';

const MAX = 1000;

function AssistantExtras({ details, onAsk, isLast, disabled }) {
  const { t } = useI18n();
  const [openSource, setOpenSource] = useState(null);
  if (!details) return null;
  const quotes = details.quotes || [];
  const sources = details.sources || [];
  const followUps = isLast ? details.follow_ups || [] : [];
  return (
    <div className="mt-3 space-y-3">
      {quotes.length > 0 && (
        <div className="space-y-2">
          {quotes.map((q, i) => (
            <figure key={i} className="rounded-lg border-l-4 border-saffron-400 bg-saffron-50/70 px-3.5 py-2.5">
              <figcaption className="mb-1 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-saffron-800">
                <Quote className="h-3 w-3" />{t.chat.fromDoc}
              </figcaption>
              <blockquote className="text-sm italic leading-relaxed text-ink-700">“{q}”</blockquote>
            </figure>
          ))}
        </div>
      )}
      {sources.length > 0 && (
        <div>
          <p className="mb-1.5 text-[11px] font-bold uppercase tracking-wider text-ink-400">{t.chat.sources}</p>
          <div className="flex flex-wrap gap-1.5">
            {sources.map((s) => (
              <button key={s.source_id} onClick={() => setOpenSource(openSource === s.source_id ? null : s.source_id)}
                className="chip max-w-full bg-emerald-100 text-emerald-800 hover:bg-emerald-200" aria-expanded={openSource === s.source_id}>
                <BookMarked className="h-3 w-3 shrink-0" /><span className="truncate">{s.citation}</span>
              </button>
            ))}
          </div>
          {sources.filter((s) => s.source_id === openSource).map((s) => (
            <div key={s.source_id} className="mt-2 animate-fade-in">
              <div className="mb-1.5"><ProvenanceBadge source={s} /></div>
              <p className="whitespace-pre-line rounded-lg bg-ink-50 p-3 text-xs leading-relaxed text-ink-600">{s.snippet}</p>
              <ProvenanceDetails source={s} />
            </div>
          ))}
        </div>
      )}
      {followUps.length > 0 && (
        <div>
          <p className="mb-1.5 text-[11px] font-bold uppercase tracking-wider text-ink-400">{t.chat.followUps}</p>
          <div className="flex flex-wrap gap-2">
            {followUps.map((f) => (
              <button key={f} disabled={disabled} onClick={() => onAsk(f)}
                className="rounded-full border border-ink-200 bg-white px-3 py-1.5 text-left text-xs font-medium text-ink-700 transition hover:border-saffron-300 hover:bg-saffron-50 disabled:opacity-50">
                {f}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Bubble({ m, isLast, onAsk, busy }) {
  const { t } = useI18n();
  if (m.role === 'USER') {
    return (
      <div className="flex justify-end animate-fade-up">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-ink-900 px-4 py-3 text-white shadow-soft">
          <p className="whitespace-pre-line break-words leading-relaxed">{m.content}</p>
        </div>
      </div>
    );
  }
  const d = m.details;
  return (
    <div className="flex gap-3 animate-fade-up">
      <div className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-saffron-400 text-ink-950"><Sparkles className="h-4 w-4" /></div>
      <div className="min-w-0 max-w-[92%] flex-1">
        <div className="rounded-2xl rounded-tl-md border border-ink-100 bg-white px-4 py-3.5 shadow-soft">
          {d && d.answerable === false && (
            <span className="chip mb-2 bg-amber-100 text-amber-900"><TriangleAlert className="h-3 w-3" />{t.chat.notFound}</span>
          )}
          <p className="whitespace-pre-line break-words leading-relaxed text-ink-800">{m.content}</p>
          <AssistantExtras details={d} onAsk={onAsk} isLast={isLast} disabled={busy} />
        </div>
        {d?.model === 'mock-extractive' && <span className="mt-1.5 inline-block text-[11px] text-ink-400">{t.chat.demo}</span>}
      </div>
    </div>
  );
}

export default function ChatPanel({ docId, lang, ready }) {
  const { t } = useI18n();
  const [messages, setMessages] = useState(null);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    setMessages(null);
    ChatApi.history(docId)
      .then((h) => !cancelled && setMessages(h))
      .catch((e) => { if (!cancelled) { setMessages([]); setError(errorMessage(e)); } });
    return () => { cancelled = true; };
  }, [docId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, busy]);

  const ask = useCallback(
    async (text) => {
      const question = text.trim();
      if (!question || busy || !ready) return;
      setError(null);
      setBusy(true);
      setInput('');
      const temp = { id: `tmp-${Date.now()}`, role: 'USER', content: question };
      setMessages((m) => [...(m || []), temp]);
      try {
        const { question: saved, answer } = await ChatApi.ask(docId, question, lang);
        setMessages((m) => [...m.filter((x) => x.id !== temp.id), saved, answer]);
      } catch (e) {
        setMessages((m) => m.filter((x) => x.id !== temp.id));
        setInput(question); // let the user retry without retyping
        setError(errorMessage(e));
      } finally {
        setBusy(false);
        inputRef.current?.focus();
      }
    },
    [busy, ready, docId, lang],
  );

  async function clear() {
    if (!window.confirm(t.chat.confirmClear)) return;
    try {
      await ChatApi.clear(docId);
      setMessages([]);
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  const lastAssistantId = [...(messages || [])].reverse().find((m) => m.role === 'ASSISTANT')?.id;
  const empty = messages && messages.length === 0;

  return (
    <section className="card flex min-h-[60vh] flex-col overflow-hidden" aria-label={t.chat.title}>
      <div className="flex items-start justify-between gap-4 border-b border-ink-100 px-5 py-4 sm:px-6">
        <div>
          <h2 className="flex items-center gap-2.5 font-display text-lg font-semibold text-ink-950">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-ink-900 text-saffron-300"><MessageSquareText className="h-4 w-4" /></span>
            {t.chat.title}
          </h2>
          <p className="mt-1 text-sm text-ink-500">{t.chat.subtitle}</p>
        </div>
        {messages?.length > 0 && (
          <button className="btn-ghost shrink-0 !px-2.5 text-ink-500 hover:!text-rose-600" onClick={clear} disabled={busy} title={t.chat.clear} aria-label={t.chat.clear}>
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="max-h-[65vh] min-h-[320px] flex-1 space-y-5 overflow-y-auto bg-gradient-to-b from-ink-50/60 to-paper px-4 py-6 sm:px-6" aria-live="polite">
        {messages === null && <div className="space-y-3"><div className="skeleton ml-auto h-12 w-2/3" /><div className="skeleton h-20 w-4/5" /></div>}

        {empty && (
          <div className="mx-auto max-w-xl py-6 text-center">
            <p className="mb-4 text-sm font-medium text-ink-500">{t.chat.empty}</p>
            <div className="grid gap-2.5 sm:grid-cols-2">
              {t.chat.starters.map((s) => (
                <button key={s} disabled={!ready || busy} onClick={() => ask(s)}
                  className="rounded-xl border border-ink-200 bg-white px-4 py-3 text-left text-sm font-medium text-ink-700 shadow-soft transition hover:-translate-y-0.5 hover:border-saffron-300 hover:shadow-lift disabled:opacity-50">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages?.map((m) => <Bubble key={m.id} m={m} isLast={m.id === lastAssistantId} onAsk={ask} busy={busy} />)}

        {busy && (
          <div className="flex items-center gap-3 animate-fade-in" role="status">
            <div className="grid h-8 w-8 place-items-center rounded-xl bg-saffron-400 text-ink-950"><Spinner className="h-4 w-4" /></div>
            <span className="rounded-2xl border border-ink-100 bg-white px-4 py-2.5 text-sm text-ink-500 shadow-soft">{t.chat.thinking}</span>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="border-t border-ink-100 bg-white px-4 py-4 sm:px-6">
        {!ready && <div className="mb-3"><Alert kind="info">{t.chat.notReady}</Alert></div>}
        {error && <div className="mb-3"><Alert onClose={() => setError(null)}>{error}</Alert></div>}
        <form onSubmit={(e) => { e.preventDefault(); ask(input); }} className="flex items-end gap-3">
          <div className="min-w-0 flex-1">
            <textarea
              ref={inputRef}
              className="input max-h-40 min-h-[48px] resize-none"
              rows={1}
              maxLength={MAX}
              value={input}
              disabled={!ready}
              placeholder={t.chat.placeholder}
              aria-label={t.chat.placeholder}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); ask(input); }
              }}
            />
            <div className="mt-1.5 flex justify-between text-[11px] text-ink-400">
              <span>{t.chat.hint}</span>
              <span>{input.length}/{MAX}</span>
            </div>
          </div>
          <button className="btn-primary !h-12 !px-4" disabled={!ready || busy || !input.trim()} aria-label={t.chat.send}>
            {busy ? <Spinner /> : <SendHorizonal className="h-5 w-5" />}
            <span className="hidden sm:inline">{t.chat.send}</span>
          </button>
        </form>
      </div>
    </section>
  );
}
