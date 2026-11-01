/** The camera: open it, play a liveness challenge on it — screen colours, then head poses — and switch it off again. */

import {
  type Challenge,
  frontalAngles,
  type HeadAngles,
  type Phase,
  type Pose,
  poseProgress,
} from "./challenge";

const MAX_WIDTH = 960;
const JPEG_QUALITY = 0.85;
/** Frames taken without screen colours, when the person has asked their device for less motion. */
const CALM_BASELINE = 4;
const CALM_GAP_MS = 300;
/** How long to wait for a pose before taking the frames anyway: the server judges them either way. */
export const POSE_TIMEOUT_MS = 6000;
/** A pose must be seen this many readings in a row, so a passing wobble doesn't count. */
const STEADY_READINGS = 3;
/** Photos taken of each pose once it is held, this far apart: the server counts the best of them. */
const FRAMES_PER_POSE = 2;
/** One more photo on the way, once the head is this far into the pose: a real head passes through the angles between,
 * while swiping between photos jumps straight from one pose to the next. */
const HALFWAY = 0.4;
const POSE_GAP_MS = 150;

export interface LabelledFrame {
  image: Blob;
  tMs: number;
  phase: Phase;
}

export interface ChallengeHooks {
  /** Show this colour around the screen, or none. */
  onColour: (colour: string | null) => void;
  /** The pose the person is asked for now, or none; the page puts it into words, in its language. */
  onCue: (pose: Pose | null) => void;
  onProgress: (taken: number, total: number) => void;
  /** How much of the current pose is reached, from 0 to 1 in steps of 0.05 — or `null` when it can't be measured. */
  onReach: (share: number | null) => void;
  /** The head's angles now, from the landmarker — or `null` when it can't see a face or isn't running. */
  readAngles: () => HeadAngles | null;
  /** The person asked their device for less motion: no colours are shown. */
  calm: boolean;
}

export interface ChallengeRun {
  frames: LabelledFrame[];
  /** When the colours began, on the same clock as the frames — or `null` if none were shown. */
  lightStartedMs: number | null;
}

export async function openCamera(): Promise<MediaStream> {
  return navigator.mediaDevices.getUserMedia({
    audio: false,
    video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
  });
}

export function closeCamera(stream: MediaStream | null): void {
  for (const track of stream?.getTracks() ?? []) {
    track.stop();
  }
}

const wait = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));
const nextPaint = (): Promise<number> => new Promise((resolve) => requestAnimationFrame(resolve));

function toJpeg(canvas: HTMLCanvasElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob === null ? reject(new Error("a frame could not be encoded")) : resolve(blob)),
      "image/jpeg",
      JPEG_QUALITY,
    );
  });
}

/** Wait until the head shows `pose` steadily, measured from its frontal `baseline`, or until the timeout, reporting how
 * far it has got on the way. */
async function holdPose(
  pose: Pose,
  baseline: HeadAngles | null,
  hooks: Pick<ChallengeHooks, "readAngles" | "onReach">,
  onHalfway: () => void,
): Promise<void> {
  const deadline = performance.now() + POSE_TIMEOUT_MS;
  let steady = 0;
  let halfway = false;
  while (performance.now() < deadline && steady < STEADY_READINGS) {
    await nextPaint();
    const angles = hooks.readAngles();
    const share = angles === null || baseline === null ? null : poseProgress(pose, angles, baseline);
    hooks.onReach(share === null ? null : Math.round(share * 20) / 20);
    if (!halfway && share !== null && share >= HALFWAY && share < 1) {
      halfway = true;
      onHalfway();
    }
    steady = share === 1 ? steady + 1 : 0;
  }
}

/** Play `challenge` on a playing video and return the labelled frames. */
export async function runChallenge(
  video: HTMLVideoElement,
  challenge: Challenge,
  hooks: ChallengeHooks,
): Promise<ChallengeRun> {
  const scale = Math.min(1, MAX_WIDTH / video.videoWidth);
  const width = Math.round(video.videoWidth * scale);
  const height = Math.round(video.videoHeight * scale);
  const baseline = hooks.calm ? CALM_BASELINE : challenge.colours.length;
  const total = baseline + challenge.poses.length * (FRAMES_PER_POSE + 1);
  const started = performance.now();
  const shots: { canvas: HTMLCanvasElement; tMs: number; phase: Phase }[] = [];
  const frontal: HeadAngles[] = [];
  // Each photo is only copied here, which is instant, and stamped with that moment. Encoding to JPEG can take a
  // second on a busy laptop, so it waits until the challenge is over: done here, it would push later photos out of
  // their colours, and the server matches photos to colours by their times alone.
  const snap = (phase: Phase): void => {
    const angles = phase === "baseline" ? hooks.readAngles() : null;
    if (angles !== null) {
      frontal.push(angles);
    }
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    if (context === null) {
      throw new Error("this browser cannot draw camera frames");
    }
    context.drawImage(video, 0, 0, width, height);
    shots.push({ canvas, tMs: performance.now() - started, phase });
    hooks.onProgress(shots.length, total);
  };

  let lightStartedMs: number | null = null;
  if (hooks.calm) {
    for (let index = 0; index < CALM_BASELINE; index += 1) {
      await wait(CALM_GAP_MS);
      snap("baseline");
    }
  } else {
    // Each colour starts exactly one step after the last, by the clock, so nothing slow can shift the timetable.
    const light = performance.now() - started;
    const until = (ms: number): Promise<void> =>
      wait(Math.max(0, light + ms - (performance.now() - started)));
    lightStartedMs = light;
    for (const [step, colour] of challenge.colours.entries()) {
      await until(step * challenge.stepMs);
      hooks.onColour(colour);
      await until((step + 0.5) * challenge.stepMs);
      snap("baseline");
    }
    await until(challenge.colours.length * challenge.stepMs);
    hooks.onColour(null);
  }

  const facing = frontalAngles(frontal);
  for (const pose of challenge.poses) {
    hooks.onCue(pose);
    await holdPose(pose, facing, hooks, () => snap(pose));
    for (let index = 0; index < FRAMES_PER_POSE; index += 1) {
      snap(pose);
      await wait(index + 1 < FRAMES_PER_POSE ? POSE_GAP_MS : 0);
    }
    hooks.onReach(null);
  }
  hooks.onCue(null);
  const frames = await Promise.all(
    shots.map(
      async (shot): Promise<LabelledFrame> => ({
        image: await toJpeg(shot.canvas),
        tMs: shot.tMs,
        phase: shot.phase,
      }),
    ),
  );
  return { frames, lightStartedMs };
}
