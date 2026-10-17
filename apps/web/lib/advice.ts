/** Friendly words for the API's short codes: a tip when photos weren't good enough, and a message when something stops the check. */

const TIPS: Record<string, string> = {
  undecodable: "Your camera's pictures couldn't be read. Please try again.",
  no_face: "We couldn't see a face. Look straight into the camera.",
  multiple_faces: "We can see more than one face. Make sure only you are in view.",
  face_too_small: "Move a little closer to the camera.",
  too_dark: "It's too dark. Face a window or a lamp.",
  too_bright: "There's too much light. Turn away from bright lights behind you.",
  too_blurry: "The photos were blurry. Hold still while they are taken.",
  not_frontal: "Look straight at the camera, not to the side.",
  low_confidence: "We couldn't see your face clearly. Uncover your face and try again.",
  inconsistent_frames: "Keep still and stay in view while the photos are taken.",
  analysis_unavailable: "The checker is busy right now. Please try again in a moment.",
  // Liveness: deliberately the same words whichever check it was, so nobody can learn which one to fool.
  liveness_check_failed:
    "Follow the prompts on screen: turn your head when asked, and keep your face in view.",
  liveness_unavailable: "We couldn't complete the check. Please try again.",
};

export const DEFAULT_TIP = "The photos didn't work out. Please try again in good, even light.";

export function tipFor(reasons: readonly string[]): string {
  for (const reason of reasons) {
    const tip = TIPS[reason];
    if (tip !== undefined) {
      return tip;
    }
  }
  return DEFAULT_TIP;
}

export interface Problem {
  title: string;
  detail: string;
}

const PROBLEMS: Record<string, Problem> = {
  invalid_client_secret: {
    title: "This link doesn't work",
    detail: "It may be incomplete or already used. Go back to the website and start the age check again.",
  },
  session_not_found: {
    title: "This link doesn't work",
    detail: "Go back to the website and start the age check again.",
  },
  session_not_open: {
    title: "This age check has ended",
    detail: "It expired before it was finished. Go back to the website and start a new one.",
  },
  too_many_challenges: {
    title: "Too many tries",
    detail: "This age check can't take any more photos. Go back to the website and start a new one.",
  },
  camera_blocked: {
    title: "We need your camera",
    detail: "Allow camera access for this page in your browser's settings, then reload the page.",
  },
  camera_missing: {
    title: "No camera found",
    detail: "Use a device with a front-facing camera, or plug one in and reload the page.",
  },
  network_error: {
    title: "You seem to be offline",
    detail: "Check your internet connection, then reload the page.",
  },
};

export const DEFAULT_PROBLEM: Problem = {
  title: "Something went wrong",
  detail: "Please reload the page. If it keeps happening, go back to the website and start again.",
};

export function problemFor(code: string): Problem {
  return PROBLEMS[code] ?? DEFAULT_PROBLEM;
}
