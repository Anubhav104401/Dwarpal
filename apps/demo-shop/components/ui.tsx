export const button =
  "inline-flex items-center justify-center rounded-full bg-amber-glow px-7 py-3.5 text-[15px] font-semibold text-stone-950 shadow-lg shadow-amber-glow/20 transition hover:brightness-110 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-amber-glow";

export const quietButton =
  "inline-flex items-center justify-center rounded-full border border-white/15 px-7 py-3.5 text-[15px] font-medium text-stone-200 transition hover:bg-white/5";

/** A wine bottle drawn with two shapes, filled with the wine's own colour. */
export function Bottle({ colour, label }: { colour: string; label: string }) {
  return (
    <svg viewBox="0 0 60 160" className="h-40 w-auto drop-shadow-2xl" aria-hidden="true">
      <path
        d="M24 6h12v34c0 6 14 12 14 30v78a6 6 0 0 1-6 6H16a6 6 0 0 1-6-6V70c0-18 14-24 14-30z"
        fill={colour}
      />
      <rect x="14" y="88" width="32" height="34" rx="3" fill="rgb(250 245 235 / 0.92)" />
      <text x="30" y="108" textAnchor="middle" fontSize="7" fontFamily="Georgia, serif" fill="#3b2a20">
        {label}
      </text>
    </svg>
  );
}
