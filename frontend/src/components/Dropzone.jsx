import { FileText, ImageIcon, UploadCloud, X } from 'lucide-react';
import { useRef, useState } from 'react';
import { useI18n } from '../context/I18nContext';
import { formatBytes } from '../utils/format';

const ACCEPT = '.pdf,.png,.jpg,.jpeg,.tif,.tiff,.webp,application/pdf,image/png,image/jpeg,image/tiff,image/webp';
const MAX_MB = 25;

export default function Dropzone({ file, onFile, onError, disabled }) {
  const { t } = useI18n();
  const inputRef = useRef(null);
  const [over, setOver] = useState(false);

  function accept(f) {
    if (!f) return;
    if (!/\.(pdf|png|jpe?g|tiff?|webp)$/i.test(f.name)) return onError?.('Unsupported file type. Use PDF, PNG, JPG, TIFF or WEBP.');
    if (f.size > MAX_MB * 1024 * 1024) return onError?.(`The file is larger than ${MAX_MB} MB.`);
    onError?.(null);
    onFile(f);
  }

  if (file) {
    const isPdf = /\.pdf$/i.test(file.name);
    const Icon = isPdf ? FileText : ImageIcon;
    return (
      <div className="flex items-center gap-4 rounded-2xl border border-saffron-200 bg-saffron-50/60 p-4 animate-fade-in">
        <div className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-white text-saffron-600 shadow-soft">
          <Icon className="h-6 w-6" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-ink-900">{file.name}</p>
          <p className="text-xs text-ink-500">{formatBytes(file.size)}</p>
        </div>
        <button className="btn-ghost !px-2" onClick={() => onFile(null)} disabled={disabled} aria-label="Remove file">
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); if (!disabled) accept(e.dataTransfer.files?.[0]); }}
      className={`group relative rounded-2xl border-2 border-dashed p-8 text-center transition ${
        over ? 'border-saffron-400 bg-saffron-50' : 'border-ink-200 bg-ink-50/50 hover:border-saffron-300 hover:bg-saffron-50/40'
      }`}
    >
      <div className="relative mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-white text-saffron-600 shadow-soft">
        <span className="absolute inset-0 rounded-2xl bg-saffron-300/40 animate-pulse-ring" />
        <UploadCloud className="relative h-7 w-7" />
      </div>
      <p className="font-semibold text-ink-900">{t.dash.drop}</p>
      <button type="button" className="mt-1 text-sm font-semibold text-saffron-700 underline-offset-4 hover:underline" onClick={() => inputRef.current?.click()} disabled={disabled}>
        {t.dash.browse}
      </button>
      <input ref={inputRef} type="file" accept={ACCEPT} className="sr-only" onChange={(e) => { accept(e.target.files?.[0]); e.target.value = ''; }} aria-label={t.dash.browse} />
    </div>
  );
}
