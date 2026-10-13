export function LogoMark({ className = 'h-9 w-9' }) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <defs>
        <linearGradient id="ns-g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#ffc052" />
          <stop offset="1" stopColor="#f98b0b" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="16" fill="#0a1020" />
      <path d="M10 40c6-14 14-20 22-20s16 6 22 20" fill="none" stroke="url(#ns-g)" strokeWidth="5" strokeLinecap="round" />
      <path d="M8 44h48" stroke="#e9edf6" strokeWidth="4" strokeLinecap="round" />
      <path d="M20 44V33M32 44V26M44 44V33" stroke="#e9edf6" strokeWidth="3.5" strokeLinecap="round" />
    </svg>
  );
}

export default function Logo({ name, dark = false }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <LogoMark />
      <span className={`font-display text-xl font-semibold tracking-tight ${dark ? 'text-white' : 'text-ink-950'}`}>{name}</span>
    </span>
  );
}
