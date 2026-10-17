/** The camera: open it, play a liveness challenge on it — screen colours, then head poses — and switch it off again. */

import { type Challenge, CUES, type HeadAngles, type Phase, type Pose, reached } from "./challenge";

const MAX_WIDTH = 960;
const JPEG_QUALITY = 0.85;
/** Frames taken without screen colours, when the person has asked their device for less motion. */
const CALM_BASELINE = 4;
const CALM_GAP_MS = 300;
/** How long to wait for a pose before taking the frame anyway: the server judges it either way. */
export const POSE_TIMEOUT_MS = 5000;
/** A pose must be seen this many readings in a row, so a passing wobble doesn't count. */
const STEADY_READINGS = 3;

export interface LabelledFrame {
  image: Blob;
  tMs: number;
  phase: Phase;
}

export interface ChallengeHooks {
  /** Show this colour around the screen, or none. */
  onColour: (colour: string | null) => void;
  /** Show this instruction, or none. */
  onCue: (cue: string | null) => void;
  onProgress: (taken: number, total: number) => void;
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

/** Wait until the head shows `pose` steadily, or until the timeout. */
async function holdPose(pose: Pose, readAngles: () => HeadAngles | null): Promise<void> {
  const deadline = performance.now() + POSE_TIMEOUT_MS;
  let steady = 0;
  while (performance.now() < deadline && steady < STEADY_READINGS) {
    await nextPaint();
    const angles = readAngles();
    steady = angles !== null && reached(pose, angles) ? steady + 1 : 0;
  }
}

/** Play `challenge` on a playing video and return the labelled frames. */
export async function runChallenge(
  video: HTMLVideoElement,
  challenge: Challenge,
  hooks: ChallengeHooks,
): Promise<ChallengeRun> {
  const scale = Math.min(1, MAX_WIDTH / video.videoWidth);
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(video.videoWidth * scale);
  canvas.height = Math.round(video.videoHeight * scale);
  const context = canvas.getContext("2d");
  if (context === null) {
    throw new Error("this browser cannot draw camera frames");
  }
  const baseline = hooks.calm ? CALM_BASELINE : challenge.colours.length;
  const total = baseline + challenge.poses.length;
  const started = performance.now();
  const frames: LabelledFrame[] = [];
  const snap = async (phase: Phase): Promise<void> => {
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    frames.push({ image: await toJpeg(canvas), tMs: performance.now() - started, phase });
    hooks.onProgress(frames.length, total);
  };

  let lightStartedMs: number | null = null;
  if (hooks.calm) {
    for (let index = 0; index < CALM_BASELINE; index += 1) {
      await wait(CALM_GAP_MS);
      await snap("baseline");
    }
  } else {
    // Each colour starts exactly one step after the last, by the clock, so the time spent encoding a frame never
    // pushes later frames into the wrong colour: the server matches frames to colours by their times alone.
    const light = performance.now() - started;
    const until = (ms: number): Promise<void> =>
      wait(Math.max(0, light + ms - (performance.now() - started)));
    lightStartedMs = light;
    for (const [step, colour] of challenge.colours.entries()) {
      await until(step * challenge.stepMs);
      hooks.onColour(colour);
      await until((step + 0.5) * challenge.stepMs);
      await snap("baseline");
    }
    await until(challenge.colours.length * challenge.stepMs);
    hooks.onColour(null);
  }

  for (const pose of challenge.poses) {
    hooks.onCue(CUES[pose]);
    await holdPose(pose, hooks.readAngles);
    await snap(pose);
  }
  hooks.onCue(null);
  return { frames, lightStartedMs };
}
