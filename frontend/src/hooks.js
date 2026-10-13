import { useEffect, useRef } from 'react';

/** Calls `fn` every `ms` while `active` is true (and the tab is visible). Always uses the latest `fn`. */
export function usePolling(fn, ms, active) {
  const saved = useRef(fn);
  saved.current = fn;
  useEffect(() => {
    if (!active) return undefined;
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') saved.current();
    }, ms);
    return () => clearInterval(id);
  }, [ms, active]);
}
