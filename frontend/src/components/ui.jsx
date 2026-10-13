import { AlertTriangle, CheckCircle2, Info, Loader2, X } from 'lucide-react';
import { cloneElement, isValidElement, useId } from 'react';

export function Spinner({ className = 'h-4 w-4' }) {
  return <Loader2 className={`animate-spin ${className}`} aria-hidden="true" />;
}

export function Alert({ kind = 'error', children, onClose }) {
  const styles = {
    error: 'border-rose-200 bg-rose-50 text-rose-800',
    success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    info: 'border-sky-200 bg-sky-50 text-sky-800',
    warn: 'border-amber-200 bg-amber-50 text-amber-900',
  };
  const Icon = { error: AlertTriangle, success: CheckCircle2, info: Info, warn: AlertTriangle }[kind];
  return (
    <div role={kind === 'error' ? 'alert' : 'status'} className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-sm ${styles[kind]}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="min-w-0 flex-1">{children}</div>
      {onClose && (
        <button onClick={onClose} className="rounded p-0.5 opacity-60 hover:opacity-100" aria-label="Dismiss">
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

export function Field({ label, hint, error, children }) {
  const autoId = useId();
  const note = error || hint;
  const id = (isValidElement(children) && children.props.id) || autoId;
  // Associate the label (and hint/error) with the control for screen readers and click-to-focus.
  const control = isValidElement(children)
    ? cloneElement(children, { id, 'aria-describedby': note ? `${id}-note` : undefined, 'aria-invalid': error ? true : undefined })
    : children;
  return (
    <div>
      <label className="label" htmlFor={id}>{label}</label>
      {control}
      {note && <p id={`${id}-note`} className={`mt-1.5 text-xs ${error ? 'text-rose-600' : 'text-ink-400'}`}>{note}</p>}
    </div>
  );
}

export function Toggle({ checked, onChange, label, disabled }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative h-6 w-11 shrink-0 rounded-full transition disabled:opacity-50 ${checked ? 'bg-saffron-500' : 'bg-ink-200'}`}
    >
      <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${checked ? 'left-[22px]' : 'left-0.5'}`} />
    </button>
  );
}

export function Segmented({ value, onChange, options, label }) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-xl bg-ink-100 p-1">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          aria-checked={value === o.value}
          onClick={() => onChange(o.value)}
          className={`rounded-lg px-3.5 py-1.5 text-sm font-semibold transition ${
            value === o.value ? 'bg-white text-ink-950 shadow-soft' : 'text-ink-500 hover:text-ink-800'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
