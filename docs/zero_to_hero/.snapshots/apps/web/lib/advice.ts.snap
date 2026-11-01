/** Which of the API's short codes have their own words for the person (decision D2 moved the words themselves into
 * `messages/`, one file per language): a tip when photos weren't good enough, a message when something stops the
 * check. Anything else gets the general one. */

const TIPS = new Set([
  "undecodable",
  "no_face",
  "multiple_faces",
  "face_too_small",
  "too_dark",
  "too_bright",
  "too_blurry",
  "not_frontal",
  "low_confidence",
  "inconsistent_frames",
  "analysis_unavailable",
  // Liveness: deliberately the same words whichever check it was, so nobody can learn which one to fool.
  "liveness_check_failed",
  "liveness_unavailable",
  // The document check (Phase 6).
  "mrz_not_found",
  "mrz_unreadable",
  "mrz_check_failed",
  "document_face_not_found",
  "face_not_found",
  "face_mismatch",
]);

const PROBLEMS = new Set([
  "invalid_client_secret",
  "session_not_found",
  "session_not_open",
  "too_many_attempts",
  "too_many_challenges",
  "camera_blocked",
  "camera_missing",
  "network_error",
]);

/** The general tip's and problem's key. */
export const DEFAULT = "default";

/** The tip for the first reason that has one (its key in `Tips`), or the general tip. */
export function tipFor(reasons: readonly string[]): string {
  return reasons.find((reason) => TIPS.has(reason)) ?? DEFAULT;
}

/** The problem's key in `Problems`: its own, or the general one — never a raw code shown to the person. */
export function problemFor(code: string): string {
  return PROBLEMS.has(code) ? code : DEFAULT;
}
