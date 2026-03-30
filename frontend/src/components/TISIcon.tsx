export default function TISIcon({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="iconGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#6366f1"/>
          <stop offset="100%" stopColor="#06b6d4"/>
        </linearGradient>
      </defs>
      {/* Outer ring */}
      <circle cx="20" cy="20" r="18" fill="url(#iconGrad)" opacity="0.15"/>
      <circle cx="20" cy="20" r="18" stroke="url(#iconGrad)" strokeWidth="1.5" fill="none"/>
      {/* Road lines */}
      <path d="M20 6 L20 34" stroke="url(#iconGrad)" strokeWidth="2" strokeLinecap="round" strokeDasharray="3 3"/>
      <path d="M6 20 L34 20" stroke="url(#iconGrad)" strokeWidth="2" strokeLinecap="round" strokeDasharray="3 3"/>
      {/* Center pulse dot */}
      <circle cx="20" cy="20" r="5" fill="url(#iconGrad)"/>
      <circle cx="20" cy="20" r="3" fill="white" opacity="0.9"/>
      {/* Corner nodes */}
      <circle cx="20" cy="8"  r="2.5" fill="#6366f1"/>
      <circle cx="20" cy="32" r="2.5" fill="#06b6d4"/>
      <circle cx="8"  cy="20" r="2.5" fill="#6366f1"/>
      <circle cx="32" cy="20" r="2.5" fill="#06b6d4"/>
    </svg>
  );
}
