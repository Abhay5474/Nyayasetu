export function formatBytes(bytes) {
  if (bytes == null) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function formatDate(iso, lang = 'en', opts = { day: 'numeric', month: 'short', year: 'numeric' }) {
  if (!iso) return '';
  // Plain dates (YYYY-MM-DD) must not shift with the viewer's timezone.
  const d = /^\d{4}-\d{2}-\d{2}$/.test(iso) ? new Date(`${iso}T00:00:00`) : new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat(lang === 'mr' ? 'mr-IN' : 'en-IN', opts).format(d);
}

export function formatDateTime(iso, lang = 'en') {
  return formatDate(iso, lang, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

/** Whole days from today (local) to a YYYY-MM-DD date. Negative = overdue. */
export function daysUntil(isoDate, now = new Date()) {
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const [y, m, d] = isoDate.split('-').map(Number);
  return Math.round((new Date(y, m - 1, d) - today) / 86_400_000);
}

/** Bucket deadlines for the deadlines page. */
export function groupDeadlines(items, now = new Date()) {
  const groups = { overdue: [], week: [], later: [], noDate: [], done: [] };
  for (const d of items) {
    if (d.status !== 'PENDING') { groups.done.push(d); continue; }
    if (!d.dueDate) { groups.noDate.push(d); continue; }
    const left = daysUntil(d.dueDate, now);
    if (left < 0) groups.overdue.push(d);
    else if (left <= 7) groups.week.push(d);
    else groups.later.push(d);
  }
  return groups;
}

export function isActive(doc) {
  return doc?.status === 'PROCESSING' || doc?.status === 'UPLOADED';
}
