/** Stylised circular emblem — a placeholder for the Ashoka Chakra / State Emblem.
 *
 *  Important: the actual State Emblem of India is protected (Emblems and Names
 *  (Prevention of Improper Use) Act, 1950). This is an institutional-looking
 *  circular device — concentric rings + 24 spokes + a lotus base — that signals
 *  "government portal" without imitating the protected emblem.
 */
export function GovEmblem({ className }: { className?: string }) {
  const spokes = Array.from({ length: 24 }, (_, i) => i * 15);
  return (
    <svg viewBox="0 0 64 64" className={className} aria-label="Government emblem (decorative)">
      {/* outer ring */}
      <circle cx="32" cy="32" r="29" fill="#FFFFFF" stroke="#0B2545" strokeWidth="1.5" />
      <circle cx="32" cy="32" r="25.5" fill="none" stroke="#0B2545" strokeWidth="0.75" />
      {/* spokes */}
      <g stroke="#0B2545" strokeWidth="1" strokeLinecap="round">
        {spokes.map((deg) => (
          <line
            key={deg}
            x1="32" y1="9.5"
            x2="32" y2="20.5"
            transform={`rotate(${deg} 32 32)`}
          />
        ))}
      </g>
      {/* hub */}
      <circle cx="32" cy="32" r="6.5" fill="#0B2545" />
      <circle cx="32" cy="32" r="2.5" fill="#FF9933" />
      {/* tricolor base bar */}
      <rect x="14" y="56" width="36" height="3" fill="#FF9933" />
      <rect x="14" y="58" width="36" height="2" fill="#FFFFFF" stroke="#0B2545" strokeWidth="0.4" />
      <rect x="14" y="59" width="36" height="2.5" fill="#138808" />
    </svg>
  );
}
