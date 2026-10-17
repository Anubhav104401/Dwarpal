/** The liveness challenge on the verify page: what the server asked for, how a head pose is read, what the browser reports. */

export type Pose = "turn_left" | "turn_right" | "look_up";
export type Phase = "baseline" | Pose;

export interface Challenge {
  id: string;
  poses: Pose[];
  colours: string[];
  stepMs: number;
}

/** What the browser reports about itself. The server never trusts it on its own: it is one input among many. */
export interface Signals {
  automation: boolean;
  virtualCamera: boolean;
  hiddenMs: number;
  lightShown: boolean;
}

/** The same two numbers the server measures (`liveness.py`), so the page and the server agree on what a pose is. */
export interface HeadAngles {
  /** Sideways turn: positive when the person turns to their left (the nose moves to the right of the picture). */
  yaw: number;
  /** Up and down: smaller when the head tilts back. About 0.55 when looking straight ahead. */
  pitch: number;
}

/** The page's targets, as shifts from the person's own frontal angles. The page's landmarks read a head a little further
 * turned than the server's do, so these are set well above the server's limits (0.18 and 0.03): when the page's meter
 * is full, the photos pass there too. */
export const TURN_SHIFT = 0.25;
export const RAISE_SHIFT = 0.12;
export const FRONTAL_YAW = 0.15;

export const CUES: Record<Pose, string> = {
  turn_left: "Turn your head to your left, eyes on the screen",
  turn_right: "Turn your head to your right, eyes on the screen",
  look_up: "Lift your chin up, eyes on the screen",
};

const POSES: readonly Pose[] = ["turn_left", "turn_right", "look_up"];
const COLOUR = /^#[0-9a-f]{6}$/;
// Names that virtual-camera programs give their devices. A match is reported, not acted on, by the page.
const VIRTUAL_CAMERA =
  /\b(obs|virtual|manycam|xsplit|snap camera|droidcam|ndi|splitcam|camtwist|mmhmm|vcam)\b/i;

export const isVirtualCamera = (label: string): boolean => VIRTUAL_CAMERA.test(label);

/** How much of the pose's target the head has reached, from its frontal `baseline`: 0 (not at all, or the wrong way)
 * to 1 (enough). */
export function poseProgress(pose: Pose, angles: HeadAngles, baseline: HeadAngles): number {
  const moved =
    pose === "turn_left"
      ? (angles.yaw - baseline.yaw) / TURN_SHIFT
      : pose === "turn_right"
        ? (baseline.yaw - angles.yaw) / TURN_SHIFT
        : (baseline.pitch - angles.pitch) / RAISE_SHIFT;
  return Math.min(1, Math.max(0, moved));
}

const median = (values: number[]): number => {
  const sorted = [...values].sort((a, b) => a - b);
  const half = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 1 ? (sorted[half] ?? 0) : ((sorted[half - 1] ?? 0) + (sorted[half] ?? 0)) / 2;
};

/** The person's frontal angles: the median of the readings taken with the baseline photos, or `null` with none. */
export function frontalAngles(readings: readonly HeadAngles[]): HeadAngles | null {
  if (readings.length === 0) {
    return null;
  }
  return { yaw: median(readings.map((r) => r.yaw)), pitch: median(readings.map((r) => r.pitch)) };
}

export interface Point {
  x: number;
  y: number;
}

const middle = (a: Point, b: Point): Point => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });

/** Head angles from five points of the face, in picture coordinates: the same formulas as the server's. */
export function anglesFrom(rightEye: Point, leftEye: Point, nose: Point, mouth: Point): HeadAngles {
  const eyes = middle(rightEye, leftEye);
  const eyeDistance = Math.max(Math.hypot(leftEye.x - rightEye.x, leftEye.y - rightEye.y), 1e-6);
  const drop = Math.max(mouth.y - eyes.y, 1e-6);
  return { yaw: (nose.x - eyes.x) / eyeDistance, pitch: (nose.y - eyes.y) / drop };
}

/** Read a challenge from the server's answer, refusing anything that isn't exactly what the page can play. */
export function readChallenge(data: Record<string, unknown>): Challenge {
  const { challenge_id: id, poses, colours, step_ms: stepMs } = data;
  const valid =
    typeof id === "string" &&
    id.length > 0 &&
    Array.isArray(poses) &&
    poses.length > 0 &&
    poses.every((pose) => POSES.includes(pose as Pose)) &&
    Array.isArray(colours) &&
    colours.length >= 2 &&
    colours.every((colour) => typeof colour === "string" && COLOUR.test(colour)) &&
    typeof stepMs === "number" &&
    stepMs >= 400 &&
    stepMs <= 2000;
  if (!valid) {
    throw new Error("the server sent a challenge this page cannot play");
  }
  return { id, poses: poses as Pose[], colours: colours as string[], stepMs };
}
