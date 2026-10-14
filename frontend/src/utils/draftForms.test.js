import { describe, expect, it } from 'vitest';
import { buildPayload, filenameFrom, initialValues, missingFields } from './draftForms';

const rtiValues = (over = {}) => ({
  ...initialValues('rti_application'),
  full_name: ' Ramesh Kulkarni ', address: 'Kothrud, Pune', place: 'Pune', authority: 'PMC, Pune', subject: 'Roads',
  items: 'Work orders\n\n  Payments to contractors  \n', ...over,
});

describe('draft form helpers', () => {
  it('reports every empty required field and ignores hidden ones', () => {
    const missing = missingFields('rti_application', initialValues('rti_application'));
    expect(Object.keys(missing).sort()).toEqual(['address', 'authority', 'full_name', 'items', 'place', 'subject']);
    expect(missing.fee_reference).toBeUndefined(); // court fee stamp: no reference needed
    expect(missingFields('rti_application', rtiValues({ fee_mode: 'cash' })).fee_reference).toBe(true);
    expect(missingFields('rti_application', rtiValues({ fee_mode: 'cash', below_poverty_line: true })).fee_reference).toBeUndefined();
  });

  it('builds a clean payload: trims, splits lines, drops blanks and hidden fields', () => {
    const body = buildPayload('rti_application', rtiValues({ delivery: 'in_person', post_mode: 'speed', phone: '  ' }), 'mr');
    expect(body).toMatchObject({ kind: 'rti_application', language: 'mr', full_name: 'Ramesh Kulkarni', items: ['Work orders', 'Payments to contractors'], delivery: 'in_person' });
    expect(body.phone).toBeUndefined();
    expect(body.post_mode).toBeUndefined(); // only sent when delivery is "post"
    expect(body.fee_reference).toBeUndefined();
  });

  it('first appeal: the "received a decision" switch controls the decision fields', () => {
    const v = { ...initialValues('first_appeal'), grounds: ['no_reply', 'other'], order_received: false, order_received_date: '2026-08-20' };
    expect(buildPayload('first_appeal', v, 'en').order_received_date).toBeUndefined();
    expect('order_received' in buildPayload('first_appeal', v, 'en')).toBe(false);
    expect(buildPayload('first_appeal', { ...v, order_received: true }, 'en').order_received_date).toBe('2026-08-20');
    expect(missingFields('first_appeal', v).grounds_other).toBe(true); // "other" needs a reason
    expect(missingFields('first_appeal', { ...v, grounds: [] }).grounds).toBe(true);
  });

  it('numbers become numbers and empty numbers are left out', () => {
    const v = { ...initialValues('fee_payment_reply'), amount_demanded: '148', amount_paid: '148.50', pages: '' };
    const body = buildPayload('fee_payment_reply', v, 'en');
    expect(body.amount_demanded).toBe(148);
    expect(body.amount_paid).toBe(148.5);
    expect('pages' in body).toBe(false);
  });

  it('reads the filename from Content-Disposition', () => {
    expect(filenameFrom('attachment; filename="RTI-application-2026-10-14.pdf"', 'x.pdf')).toBe('RTI-application-2026-10-14.pdf');
    expect(filenameFrom(undefined, 'draft.pdf')).toBe('draft.pdf');
  });
});
