import { ArrowUpRight, FileText, ImageIcon, Trash2 } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { DocumentApi } from '../api/endpoints';
import { errorMessage } from '../api/client';
import Dropzone from '../components/Dropzone';
import StatusBadge from '../components/StatusBadge';
import { Alert, Segmented, Spinner } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import { usePolling } from '../hooks';
import { formatBytes, formatDateTime, isActive } from '../utils/format';

export default function Dashboard() {
  const { t, lang } = useI18n();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [file, setFile] = useState(null);
  const [outLang, setOutLang] = useState(user?.preferredLanguage || lang);
  const [progress, setProgress] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  const [docs, setDocs] = useState(null);
  const [listError, setListError] = useState(null);

  const load = useCallback(async () => {
    try {
      setDocs((await DocumentApi.list(0, 20)).items);
      setListError(null);
    } catch (e) {
      setListError(errorMessage(e));
    }
  }, []);

  useEffect(() => { load(); }, [load]);
  usePolling(load, 3000, !!docs?.some(isActive));

  async function submit(e) {
    e.preventDefault();
    if (!file) return setUploadError(t.dash.chooseFile);
    setUploadError(null);
    setProgress(0);
    try {
      const doc = await DocumentApi.upload(file, outLang, setProgress);
      navigate(`/app/documents/${doc.id}?lang=${outLang}`);
    } catch (err) {
      setUploadError(errorMessage(err));
      setProgress(null);
    }
  }

  async function remove(doc) {
    if (!window.confirm(t.dash.confirmDelete)) return;
    try {
      await DocumentApi.remove(doc.id);
      setDocs((d) => d.filter((x) => x.id !== doc.id));
    } catch (err) {
      setListError(errorMessage(err));
    }
  }

  const uploading = progress !== null;

  return (
    <div className="space-y-10">
      <div>
        <p className="text-sm font-semibold text-saffron-700">{t.dash.hello},</p>
        <h1 className="font-display text-3xl font-semibold sm:text-4xl">{user?.fullName}</h1>
      </div>

      <form onSubmit={submit} className="card-pad relative overflow-hidden">
        <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-saffron-200/50 blur-3xl" />
        <div className="relative">
          <h2 className="font-display text-xl font-semibold">{t.dash.uploadTitle}</h2>
          <p className="mt-1 text-sm text-ink-500">{t.dash.uploadSub}</p>
          <div className="mt-5"><Dropzone file={file} onFile={setFile} onError={setUploadError} disabled={uploading} /></div>
          {uploadError && <div className="mt-4"><Alert onClose={() => setUploadError(null)}>{uploadError}</Alert></div>}
          <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-ink-600">{t.dash.outputLang}</span>
              <Segmented label={t.dash.outputLang} value={outLang} onChange={setOutLang} options={[{ value: 'en', label: 'English' }, { value: 'mr', label: 'मराठी' }]} />
            </div>
            <button className="btn-primary !px-6 !py-3" disabled={!file || uploading}>
              {uploading ? <><Spinner />{t.dash.uploading} {progress}%</> : t.dash.submit}
            </button>
          </div>
        </div>
      </form>

      <section aria-labelledby="hist-h">
        <h2 id="hist-h" className="mb-4 font-display text-xl font-semibold">{t.dash.historyTitle}</h2>
        {listError && <div className="mb-4"><Alert>{listError}</Alert></div>}
        {docs === null ? (
          <div className="space-y-3">{[0, 1, 2].map((i) => <div key={i} className="skeleton h-[72px]" />)}</div>
        ) : docs.length === 0 ? (
          <div className="card grid place-items-center px-6 py-14 text-center">
            <div className="mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-ink-100 text-ink-400"><FileText className="h-7 w-7" /></div>
            <p className="font-semibold text-ink-800">{t.dash.emptyTitle}</p>
            <p className="mt-1 max-w-sm text-sm text-ink-500">{t.dash.emptyBody}</p>
          </div>
        ) : (
          <ul className="space-y-3">
            {docs.map((d) => {
              const Icon = d.contentType === 'application/pdf' ? FileText : ImageIcon;
              return (
                <li key={d.id} className="card group flex items-center gap-4 p-4 transition hover:border-saffron-200 hover:shadow-lift">
                  <Link to={`/app/documents/${d.id}`} className="flex min-w-0 flex-1 items-center gap-4">
                    <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-ink-100 text-ink-600 transition group-hover:bg-saffron-100 group-hover:text-saffron-700"><Icon className="h-5 w-5" /></div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold text-ink-900">{d.originalFilename}</p>
                      <p className="mt-0.5 text-xs text-ink-500">
                        {formatDateTime(d.createdAt, lang)} · {formatBytes(d.sizeBytes)}
                        {d.pageCount ? ` · ${d.pageCount} ${d.pageCount === 1 ? t.dash.page : t.dash.pages}` : ''}
                      </p>
                    </div>
                    <div className="hidden items-center gap-1.5 sm:flex">
                      {d.results?.filter((r) => r.status === 'COMPLETED').map((r) => (
                        <span key={r.language} className="chip bg-ink-100 text-ink-600">{r.language === 'mr' ? 'मराठी' : 'EN'}</span>
                      ))}
                    </div>
                    <StatusBadge status={d.status} />
                    <ArrowUpRight className="hidden h-4 w-4 text-ink-300 transition group-hover:text-saffron-600 sm:block" />
                  </Link>
                  <button className="btn-ghost !px-2 text-ink-400 hover:!text-rose-600" onClick={() => remove(d)} aria-label={`${t.dash.remove}: ${d.originalFilename}`}>
                    <Trash2 className="h-4 w-4" />
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
