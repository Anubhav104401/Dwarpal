/** The camera: open it, take one quick burst of still frames, and switch it off again. */

import type { CapturedFrame } from "./flow-api";

export const BURST_SIZE = 5;
export const BURST_GAP_MS = 150;
const MAX_WIDTH = 960;
const JPEG_QUALITY = 0.85;

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

function toJpeg(canvas: HTMLCanvasElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob === null ? reject(new Error("a frame could not be encoded")) : resolve(blob)),
      "image/jpeg",
      JPEG_QUALITY,
    );
  });
}

/** Take `BURST_SIZE` frames, `BURST_GAP_MS` apart, from a playing video. `onFrame` reports progress. */
export async function captureBurst(
  video: HTMLVideoElement,
  onFrame?: (taken: number) => void,
): Promise<CapturedFrame[]> {
  const scale = Math.min(1, MAX_WIDTH / video.videoWidth);
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(video.videoWidth * scale);
  canvas.height = Math.round(video.videoHeight * scale);
  const context = canvas.getContext("2d");
  if (context === null) {
    throw new Error("this browser cannot draw camera frames");
  }
  const started = performance.now();
  const frames: CapturedFrame[] = [];
  for (let index = 0; index < BURST_SIZE; index += 1) {
    if (index > 0) {
      await wait(BURST_GAP_MS);
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    frames.push({ image: await toJpeg(canvas), tMs: performance.now() - started });
    onFrame?.(index + 1);
  }
  return frames;
}
