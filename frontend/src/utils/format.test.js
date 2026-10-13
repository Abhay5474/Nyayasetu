import { describe, expect, it } from 'vitest';
import { daysUntil, formatBytes, formatDate, groupDeadlines } from './format';

describe('format utils', () => {
  it('formats bytes', () => {
    expect(formatBytes(512)).toBe('512 B');
    expect(formatBytes(2048)).toBe('2 KB');
    expect(formatBytes(5 * 1024 * 1024)).toBe('5.0 MB');
  });

  it('computes whole days relative to today regardless of time of day', () => {
    const now = new Date(2025, 2, 10, 23, 59);
    expect(daysUntil('2025-03-10', now)).toBe(0);
    expect(daysUntil('2025-03-11', now)).toBe(1);
    expect(daysUntil('2025-03-09', now)).toBe(-1);
  });

  it('does not shift plain dates across timezones', () => {
    expect(formatDate('2025-01-15', 'en')).toContain('15');
  });

  it('groups deadlines', () => {
    const now = new Date(2025, 2, 10);
    const g = groupDeadlines(
      [
        { id: 1, status: 'PENDING', dueDate: '2025-03-01' },
        { id: 2, status: 'PENDING', dueDate: '2025-03-14' },
        { id: 3, status: 'PENDING', dueDate: '2025-06-01' },
        { id: 4, status: 'PENDING', dueDate: null },
        { id: 5, status: 'DONE', dueDate: '2025-03-12' },
      ],
      now,
    );
    expect(g.overdue.map((d) => d.id)).toEqual([1]);
    expect(g.week.map((d) => d.id)).toEqual([2]);
    expect(g.later.map((d) => d.id)).toEqual([3]);
    expect(g.noDate.map((d) => d.id)).toEqual([4]);
    expect(g.done.map((d) => d.id)).toEqual([5]);
  });
});
