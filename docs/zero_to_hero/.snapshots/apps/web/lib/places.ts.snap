/** The console's places: the sidebar lists the fixed ones, and the command palette searches them with every
 *  organisation and project the person can open. */

export interface Place {
  label: string;
  href: string;
  hint: string;
}

export const PLACES: Place[] = [
  { label: "Organisations", href: "/console", hint: "All your organisations" },
  { label: "Age model", href: "/console/model", hint: "The model deciding, and its lines" },
  { label: "Security", href: "/console/account", hint: "One-time codes and recovery codes" },
];

/** The places whose label or hint contains every word typed, in any order and any case; those whose label starts
 *  with the first word come first. Nothing typed: everything, as it was. */
export function matching(places: Place[], typed: string): Place[] {
  const words = typed.toLowerCase().split(/\s+/).filter(Boolean);
  if (words.length === 0) return places;
  const found = places.filter((place) => {
    const text = `${place.label} ${place.hint}`.toLowerCase();
    return words.every((word) => text.includes(word));
  });
  const first = words[0] ?? "";
  const leads = (place: Place) => (place.label.toLowerCase().startsWith(first) ? 0 : 1);
  return found.sort((a, b) => leads(a) - leads(b));
}
