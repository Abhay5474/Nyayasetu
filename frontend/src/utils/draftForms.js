// Field layout of each draft type. Labels come from t.drafts.fields / t.drafts.options (see i18n/drafts.js).
const you = { section: 'you', fields: [
  { name: 'full_name', type: 'text', required: true },
  { name: 'address', type: 'textarea', required: true, rows: 2 },
  { name: 'phone', type: 'text' },
  { name: 'email', type: 'text' },
  { name: 'place', type: 'text', required: true },
  { name: 'date', type: 'date', required: true },
] };

const feeFields = (extra = {}) => [
  { name: 'fee_mode', type: 'select', options: ['court_fee_stamp', 'cash', 'demand_draft', 'banker_cheque'], ...extra },
  { name: 'fee_reference', type: 'text', required: (v) => v.fee_mode !== 'court_fee_stamp', showIf: (v) => v.fee_mode !== 'court_fee_stamp' },
];

export const FORMS = {
  rti_application: [
    you,
    { section: 'to', fields: [{ name: 'authority', type: 'textarea', required: true, rows: 3, hint: true }] },
    { section: 'info', fields: [
      { name: 'subject', type: 'text', required: true, hint: true },
      { name: 'period', type: 'text', hint: true },
      { name: 'items', type: 'lines', required: true, rows: 5, hint: true },
      { name: 'delivery', type: 'select', options: ['in_person', 'post'] },
      { name: 'post_mode', type: 'select', options: ['ordinary', 'registered', 'speed'], showIf: (v) => v.delivery === 'post' },
    ] },
    { section: 'fee', fields: [
      { name: 'below_poverty_line', type: 'checkbox' },
      { name: 'bpl_card_no', type: 'text', showIf: (v) => v.below_poverty_line },
      ...feeFields().map((f) => ({ ...f, showIf: (v) => !v.below_poverty_line && (f.showIf ? f.showIf(v) : true) })),
    ] },
  ],
  first_appeal: [
    you,
    { section: 'to', fields: [
      { name: 'appellate_authority', type: 'textarea', required: true, rows: 3, hint: true },
      { name: 'pio_details', type: 'textarea', required: true, rows: 2, hint: true },
    ] },
    { section: 'rti', fields: [
      { name: 'application_date', type: 'date', required: true },
      { name: 'application_ref', type: 'text' },
      { name: 'order_received', type: 'checkbox', client: true },
      { name: 'order_received_date', type: 'date', required: true, showIf: (v) => v.order_received },
      { name: 'order_ref', type: 'text', showIf: (v) => v.order_received },
      { name: 'info_subject', type: 'textarea', required: true, rows: 2 },
      { name: 'info_office', type: 'text', required: true },
    ] },
    { section: 'grounds', fields: [
      { name: 'grounds', type: 'checks', required: true, options: ['no_reply', 'refused_exemption', 'incomplete', 'wrong_fee', 'misleading', 'other'] },
      { name: 'grounds_other', type: 'textarea', rows: 3, required: true, showIf: (v) => (v.grounds || []).includes('other') },
      { name: 'delay_reason', type: 'textarea', rows: 3, hint: true },
    ] },
    { section: 'fee', fields: feeFields() },
  ],
  fee_payment_reply: [
    you,
    { section: 'pio', fields: [
      { name: 'pio_office', type: 'textarea', required: true, rows: 3 },
      { name: 'pio_letter_ref', type: 'text' },
      { name: 'pio_letter_date', type: 'date', required: true },
      { name: 'application_date', type: 'date', required: true },
      { name: 'application_ref', type: 'text' },
      { name: 'amount_demanded', type: 'number', required: true },
      { name: 'pages', type: 'number', hint: true },
    ] },
    { section: 'payment', fields: [
      { name: 'amount_paid', type: 'number', required: true },
      { name: 'payment_mode', type: 'select', options: ['demand_draft', 'cash', 'banker_cheque', 'online'], required: true },
      { name: 'payment_reference', type: 'text', required: true },
      { name: 'payment_date', type: 'date', required: true },
    ] },
  ],
};

export const today = () => new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD in the browser's time zone

export function initialValues(kind) {
  const v = { date: today(), grounds: [] };
  if (kind === 'rti_application') Object.assign(v, { delivery: 'in_person', fee_mode: 'court_fee_stamp', below_poverty_line: false });
  if (kind === 'first_appeal') Object.assign(v, { fee_mode: 'court_fee_stamp', order_received: false });
  if (kind === 'fee_payment_reply') Object.assign(v, { payment_mode: 'demand_draft' });
  return v;
}

const isRequired = (f, v) => (typeof f.required === 'function' ? f.required(v) : !!f.required);
const visible = (f, v) => !f.showIf || f.showIf(v);

/** Field name -> true for each visible required field that is empty. */
export function missingFields(kind, v) {
  const out = {};
  for (const sec of FORMS[kind]) {
    for (const f of sec.fields) {
      if (!visible(f, v) || !isRequired(f, v)) continue;
      const val = v[f.name];
      const empty = f.type === 'checks' ? !(val || []).length : f.type === 'checkbox' ? false : val == null || String(val).trim() === '';
      if (empty) out[f.name] = true;
    }
  }
  return out;
}

/** The JSON the server expects: hidden / blank fields are left out, "lines" become a list, numbers become numbers. */
export function buildPayload(kind, v, language) {
  const body = { kind, language };
  for (const sec of FORMS[kind]) {
    for (const f of sec.fields) {
      if (f.client || !visible(f, v)) continue;
      const val = v[f.name];
      if (f.type === 'checkbox') body[f.name] = !!val;
      else if (f.type === 'checks') body[f.name] = val || [];
      else if (f.type === 'lines') body[f.name] = String(val || '').split('\n').map((s) => s.trim()).filter(Boolean);
      else if (f.type === 'number') { if (String(val ?? '').trim() !== '') body[f.name] = Number(val); }
      else if (val != null && String(val).trim() !== '') body[f.name] = String(val).trim();
    }
  }
  return body;
}

/** Filename from a Content-Disposition header, with a safe fallback. */
export function filenameFrom(disposition, fallback) {
  const m = /filename="?([^";]+)"?/i.exec(disposition || '');
  return m ? m[1] : fallback;
}
