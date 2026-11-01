/** Where the points of light sit: rings of an oval face, each ring with more points than the one inside it. */
function facePoints(): Array<{ x: number; y: number; ring: number }> {
  const points = [];
  for (let ring = 1; ring <= 6; ring++) {
    const count = ring * 8;
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * 2 * Math.PI + ring * 0.4;
      points.push({
        x: Math.round((120 + 52 * (ring / 6) * Math.cos(angle)) * 10) / 10,
        y: Math.round((156 + 68 * (ring / 6) * Math.sin(angle)) * 10) / 10,
        ring,
      });
    }
  }
  return points;
}

const POINTS = facePoints();

/**
 * The home page's artwork, the brand's motif: a face made of points of light, standing in a temple doorway — the
 * place a dwarpal guards. A line of light passes over it, as a check would; that motion is decoration, so it runs
 * only for people who haven't asked their system for less (the design's 3D hero waits on decision D1).
 */
export function Arch() {
  return (
    <svg viewBox="0 0 240 280" className="w-full max-w-72" aria-hidden="true">
      <path
        d="M28 272V124a92 92 0 0 1 184 0v148"
        fill="none"
        strokeWidth="5"
        strokeLinecap="round"
        className="stroke-brand-500"
      />
      <path
        d="M12 272h216"
        strokeWidth="5"
        strokeLinecap="round"
        className="stroke-ink-900 dark:stroke-ink-100"
      />
      {POINTS.map((point) => (
        <circle
          key={`${point.x},${point.y}`}
          cx={point.x}
          cy={point.y}
          r={point.ring === 6 ? 2.2 : 1.6}
          className={point.ring === 6 ? "fill-brand-500" : "fill-ink-400 dark:fill-ink-500"}
        />
      ))}
      <g className="motion-safe:animate-scan">
        <path
          d="M60 156h120"
          strokeWidth="2"
          strokeLinecap="round"
          className="stroke-brand-400"
          opacity="0.8"
        />
      </g>
    </svg>
  );
}
