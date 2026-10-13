import { AlertCircle, CheckCircle2, Clock3 } from 'lucide-react';
import { Spinner } from './ui';
import { useI18n } from '../context/I18nContext';

const STYLE = {
  UPLOADED: 'bg-ink-100 text-ink-700',
  PROCESSING: 'bg-amber-100 text-amber-800',
  COMPLETED: 'bg-emerald-100 text-emerald-800',
  FAILED: 'bg-rose-100 text-rose-800',
};

export default function StatusBadge({ status }) {
  const { t } = useI18n();
  const icon =
    status === 'PROCESSING' ? <Spinner className="h-3 w-3" /> :
    status === 'COMPLETED' ? <CheckCircle2 className="h-3 w-3" /> :
    status === 'FAILED' ? <AlertCircle className="h-3 w-3" /> : <Clock3 className="h-3 w-3" />;
  return (
    <span className={`chip ${STYLE[status] || STYLE.UPLOADED}`}>
      {icon}
      {t.status[status] || status}
    </span>
  );
}
