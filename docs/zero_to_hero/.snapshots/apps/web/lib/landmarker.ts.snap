/** MediaPipe Face Landmarker, loaded only when the camera starts. It guides the person; it decides nothing. */

import type { FaceLandmarker, NormalizedLandmark } from "@mediapipe/tasks-vision";

import { anglesFrom, type HeadAngles } from "./challenge";

/** Where `scripts/mediapipe.mjs` puts the WebAssembly files and the pinned face model. */
const ASSETS = "/mediapipe";

export interface Reading {
  faces: number;
  angles: HeadAngles | null;
  /** The face's middle is near the middle of the picture. */
  centred: boolean;
  /** The face is wide enough for good photos: at least a fifth of the picture. */
  closeEnough: boolean;
}

/** Points of MediaPipe's face mesh: both corners of each eye, the tip of the nose, the corners of the mouth. */
const MESH = { rightEye: [33, 133], leftEye: [362, 263], nose: [1], mouth: [61, 291] } as const;

function centre(points: NormalizedLandmark[], indices: readonly number[]): { x: number; y: number } {
  const chosen = indices.map((index) => points[index] ?? { x: 0, y: 0 });
  return {
    x: chosen.reduce((sum, point) => sum + point.x, 0) / chosen.length,
    y: chosen.reduce((sum, point) => sum + point.y, 0) / chosen.length,
  };
}

async function create(delegate: "GPU" | "CPU"): Promise<FaceLandmarker> {
  const { FaceLandmarker, FilesetResolver } = await import("@mediapipe/tasks-vision");
  const files = await FilesetResolver.forVisionTasks(`${ASSETS}/wasm`);
  return FaceLandmarker.createFromOptions(files, {
    baseOptions: { modelAssetPath: `${ASSETS}/face_landmarker.task`, delegate },
    runningMode: "VIDEO",
    numFaces: 2,
  });
}

/** The landmarker, on the graphics chip if possible, otherwise the processor — or `null` if it can't run here. */
export async function loadLandmarker(): Promise<FaceLandmarker | null> {
  for (const delegate of ["GPU", "CPU"] as const) {
    try {
      return await create(delegate);
    } catch {
      // Try the next way of running it; without any, the page still works, only without live guidance.
    }
  }
  return null;
}

export function read(landmarker: FaceLandmarker, video: HTMLVideoElement, nowMs: number): Reading {
  const faces = landmarker.detectForVideo(video, nowMs).faceLandmarks;
  const face = faces[0];
  if (face === undefined || face.length === 0) {
    return { faces: 0, angles: null, centred: false, closeEnough: false };
  }
  const xs = face.map((point) => point.x);
  const ys = face.map((point) => point.y);
  const width = Math.max(...xs) - Math.min(...xs);
  const middleX = (Math.max(...xs) + Math.min(...xs)) / 2;
  const middleY = (Math.max(...ys) + Math.min(...ys)) / 2;
  const angles = anglesFrom(
    centre(face, MESH.rightEye),
    centre(face, MESH.leftEye),
    centre(face, MESH.nose),
    centre(face, MESH.mouth),
  );
  return {
    faces: faces.length,
    angles,
    centred: Math.abs(middleX - 0.5) < 0.15 && Math.abs(middleY - 0.5) < 0.2,
    closeEnough: width >= 0.2,
  };
}
