import { ExternalLink, FileWarning, ShieldCheck, ShieldQuestion } from 'lucide-react';
import { fmt, useI18n } from '../../context/I18nContext';
import { formatDate } from '../../utils/format';

/** Where a cited source comes from and how far it can be trusted. Results saved before provenance existed were
 *  all unverified summaries, so a missing source_type is shown as such. */
const isOfficial = (source) => source.source_type === 'official_pdf' || source.source_type === 'official_reprint';

export function ProvenanceBadge({ source }) {
  const { t } = useI18n();
  return isOfficial(source) ? (
    <span className="chip bg-emerald-100 text-emerald-800"><ShieldCheck className="h-3 w-3" />
      {source.source_type === 'official_reprint' ? t.prov.reprint : t.prov.official}
    </span>
  ) : (
    <span className="chip bg-amber-100 text-amber-900"><ShieldQuestion className="h-3 w-3" />{t.prov.unverified}</span>
  );
}

export function ProvenanceDetails({ source }) {
  const { t, lang } = useI18n();
  const official = isOfficial(source);
  return (
    <div className="mt-3 space-y-1.5 rounded-lg border border-ink-100 bg-white p-3 text-xs text-ink-600">
      {official ? (
        <>
          {source.version_date && <p>{fmt(t.prov.asOf, { date: formatDate(source.version_date, lang) })}</p>}
          <p className={source.verified_at ? 'font-medium text-emerald-700' : 'text-amber-800'}>
            {source.verified_at
              ? fmt(t.prov.verified, { date: formatDate(source.verified_at, lang), by: source.verified_by ? ` · ${source.verified_by}` : '' })
              : t.prov.notVerified}
          </p>
          {source.gazette_ref && <p><span className="font-semibold">{t.prov.gazette}:</span> {source.gazette_ref}</p>}
          {source.notes && <p className="rounded bg-amber-50 px-2 py-1.5 text-amber-900"><span className="font-semibold">{t.prov.note}:</span> {source.notes}</p>}
          {source.ocr && <p className="flex items-start gap-1.5 text-amber-800"><FileWarning className="mt-0.5 h-3.5 w-3.5 shrink-0" />{t.prov.ocr}</p>}
          {source.source_url && (
            <a href={source.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 font-semibold text-saffron-700 hover:underline">
              <ExternalLink className="h-3 w-3" />{t.prov.openSource}
            </a>
          )}
        </>
      ) : (
        <p className="text-amber-800">{t.prov.unverifiedNote}</p>
      )}
    </div>
  );
}
