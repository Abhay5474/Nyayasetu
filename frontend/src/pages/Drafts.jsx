import { ArrowLeft, Download, Eye, FileDown, FilePenLine, FileText, Gavel, Receipt } from 'lucide-react';
import { useMemo, useRef, useState } from 'react';
import { errorMessage } from '../api/client';
import { DraftApi } from '../api/endpoints';
import DraftPaper from '../components/drafts/DraftPaper';
import { Alert, Field, Segmented, Spinner } from '../components/ui';
import { fmt, useI18n } from '../context/I18nContext';
import { FORMS, buildPayload, filenameFrom, friendlyError, initialValues, missingFields, today } from '../utils/draftForms';
import { formatDate } from '../utils/format';

const KIND_ICONS = { rti_application: FileText, first_appeal: Gavel, fee_payment_reply: Receipt };

export default function Drafts() {
  const { t, lang } = useI18n();
  const d = t.drafts;
  const [kind, setKind] = useState(null);
  const [values, setValues] = useState({});
  const [docLang, setDocLang] = useState(lang);
  const [errors, setErrors] = useState({});
  const [preview, setPreview] = useState(null);
  const [stale, setStale] = useState(false);
  const [busy, setBusy] = useState(null); // 'preview' | 'pdf' | 'docx'
  const [error, setError] = useState(null);
  const previewRef = useRef(null);

  const form = kind ? FORMS[kind] : [];
  const payloadOf = () => buildPayload(kind, values, docLang);
  const options = useMemo(() => [{ value: 'en', label: t.common.english }, { value: 'mr', label: t.common.marathi }], [t]);

  function choose(k) {
    setKind(k);
    setValues(initialValues(k));
    setErrors({});
    setPreview(null);
    setError(null);
    setStale(false);
  }

  function set(name, value) {
    setValues((v) => ({ ...v, [name]: value }));
    setErrors((e) => (e[name] ? { ...e, [name]: false } : e));
    if (preview) setStale(true);
  }

  function validate() {
    const missing = missingFields(kind, values);
    setErrors(missing);
    if (Object.keys(missing).length) {
      setError(d.fixFields);
      return false;
    }
    setError(null);
    return true;
  }

  async function makePreview() {
    if (!validate()) return;
    setBusy('preview');
    try {
      setPreview(await DraftApi.preview(payloadOf()));
      setStale(false);
      setTimeout(() => previewRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
    } catch (e) {
      setError(friendlyError(errorMessage(e), d.fields));
    } finally {
      setBusy(null);
    }
  }

  async function download(format) {
    if (!validate()) return;
    setBusy(format);
    try {
      const { blob, disposition } = await DraftApi.file(payloadOf(), format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filenameFrom(disposition, `draft.${format}`);
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10_000);
    } catch (e) {
      // an error body arrives as a Blob: read the message out of it
      let message = errorMessage(e);
      try { message = JSON.parse(await e.response.data.text()).message || message; } catch { /* keep the generic text */ }
      setError(friendlyError(message, d.fields));
    } finally {
      setBusy(null);
    }
  }

  if (!kind) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="font-display text-3xl font-semibold">{d.title}</h1>
          <p className="mt-1 max-w-2xl text-ink-500">{d.sub}</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          {Object.keys(FORMS).map((k) => {
            const Icon = KIND_ICONS[k];
            return (
              <button key={k} type="button" onClick={() => choose(k)} className="card-pad text-left transition hover:-translate-y-0.5 hover:border-saffron-300">
                <Icon className="mb-3 h-6 w-6 text-saffron-600" />
                <p className="font-display text-lg font-semibold">{d.kinds[k].title}</p>
                <p className="mt-1 text-sm text-ink-500">{d.kinds[k].body}</p>
              </button>
            );
          })}
        </div>
        <Alert kind="info">{d.privacy}</Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <button type="button" className="btn-ghost !px-2 text-sm" onClick={() => setKind(null)}>
            <ArrowLeft className="h-4 w-4" />{d.chooseAnother}
          </button>
          <h1 className="mt-1 flex items-center gap-2 font-display text-3xl font-semibold"><FilePenLine className="h-7 w-7 text-saffron-600" />{d.kinds[kind].title}</h1>
        </div>
        <div>
          <p className="mb-1.5 text-sm font-medium text-ink-700">{d.docLang}</p>
          <Segmented value={docLang} onChange={(v) => { setDocLang(v); if (preview) setStale(true); }} options={options} label={d.docLang} />
        </div>
      </div>

      {error && <Alert onClose={() => setError(null)}><span className="whitespace-pre-line">{error}</span></Alert>}

      <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
        <form className="card-pad space-y-7" onSubmit={(e) => { e.preventDefault(); makePreview(); }} noValidate>
          {form.map((sec) => (
            <fieldset key={sec.section} className="space-y-4">
              <legend className="section-title mb-3 !text-base">{d.sections[sec.section]}</legend>
              {sec.fields.filter((f) => !f.showIf || f.showIf(values)).map((f) => (
                <FormField key={f.name} f={f} d={d} lang={lang} value={values[f.name]} error={errors[f.name]} onChange={(val) => set(f.name, val)} />
              ))}
            </fieldset>
          ))}
          <button type="submit" className="btn-dark w-full" disabled={busy !== null}>
            {busy === 'preview' ? <Spinner /> : <Eye className="h-4 w-4" />}{busy === 'preview' ? d.preparing : d.preview}
          </button>
        </form>

        <div ref={previewRef} className="space-y-4 lg:sticky lg:top-20">
          <h2 className="section-title !text-lg">{d.previewTitle}</h2>
          {!preview ? (
            <div className="card grid place-items-center px-6 py-16 text-center text-sm text-ink-400">{d.previewEmpty}</div>
          ) : (
            <>
              {stale && <Alert kind="warn">{d.stale}</Alert>}
              {preview.last_date && <Alert kind="info">{fmt(d.lastDate, { date: formatDate(preview.last_date, lang) })}</Alert>}
              {preview.warnings.length > 0 && (
                <Alert kind="warn">
                  <p className="mb-1 font-semibold">{d.warningsTitle}</p>
                  <ul className="list-disc space-y-1 pl-5">{preview.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
                </Alert>
              )}
              <div className="flex flex-wrap gap-2">
                <button type="button" className="btn-primary" disabled={busy !== null} onClick={() => download('pdf')}>
                  {busy === 'pdf' ? <Spinner /> : <Download className="h-4 w-4" />}{d.downloadPdf}
                </button>
                <button type="button" className="btn-outline" disabled={busy !== null} onClick={() => download('docx')}>
                  {busy === 'docx' ? <Spinner /> : <FileDown className="h-4 w-4" />}{d.downloadWord}
                </button>
              </div>
              <DraftPaper doc={preview} />
              {preview.notes.length > 0 && (
                <div className="card-pad text-sm">
                  <p className="mb-1.5 font-semibold">{d.notesTitle}</p>
                  <ul className="list-disc space-y-1 pl-5 text-ink-600">{preview.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
                </div>
              )}
              <p className="text-xs text-ink-400">{d.privacy}</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function FormField({ f, d, lang, value, error, onChange }) {
  const label = d.fields[f.name];
  const hint = f.hint ? d.fields[`${f.name}Hint`] : undefined;
  const err = error ? (error === 'future' ? d.futureDate : d.required) : undefined;
  const star = f.required ? ' *' : '';

  if (f.type === 'checkbox') {
    return (
      <label className="flex items-start gap-2.5 text-sm text-ink-800">
        <input type="checkbox" className="mt-0.5 h-4 w-4 rounded border-ink-300 accent-saffron-600" checked={!!value} onChange={(e) => onChange(e.target.checked)} />
        {label}
      </label>
    );
  }
  if (f.type === 'checks') {
    const chosen = value || [];
    return (
      <Field label={label + star} error={err}>
        <div className="space-y-2" role="group">
          {f.options.map((o) => (
            <label key={o} className="flex items-start gap-2.5 text-sm text-ink-800">
              <input
                type="checkbox"
                className="mt-0.5 h-4 w-4 rounded border-ink-300 accent-saffron-600"
                checked={chosen.includes(o)}
                onChange={(e) => onChange(e.target.checked ? [...chosen, o] : chosen.filter((x) => x !== o))}
              />
              {d.options.grounds[o]}
            </label>
          ))}
        </div>
      </Field>
    );
  }
  if (f.type === 'select') {
    return (
      <Field label={label + star} error={err}>
        <select className="input" value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
          {f.options.map((o) => <option key={o} value={o}>{d.options[f.name][o]}</option>)}
        </select>
      </Field>
    );
  }
  if (f.type === 'textarea' || f.type === 'lines') {
    return (
      <Field label={label + star} hint={hint} error={err}>
        <textarea className="input" rows={f.rows || 3} value={value ?? ''} onChange={(e) => onChange(e.target.value)} maxLength={f.type === 'lines' ? 6000 : 1500} />
      </Field>
    );
  }
  // A date input shows the browser's own day/month order; spelling the chosen date out makes a mix-up visible at once.
  const dateHint = f.type === 'date' && value ? fmt(d.dateIs, { date: formatDate(value, lang) }) : undefined;
  return (
    <Field label={label + star} hint={dateHint || hint} error={err}>
      <input
        className="input"
        type={f.type === 'date' ? 'date' : f.type === 'number' ? 'number' : 'text'}
        {...(f.type === 'date' && f.name !== 'date' ? { max: today() } : {})}
        {...(f.type === 'number' ? { min: 0, step: '0.01', inputMode: 'decimal' } : {})}
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        maxLength={f.type === 'text' ? 400 : undefined}
      />
    </Field>
  );
}
