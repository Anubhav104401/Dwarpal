"use client";

import type { FaceLandmarker } from "@mediapipe/tasks-vision";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { accentButton } from "@/components/shell";
import { closeCamera, openCamera, runChallenge } from "@/lib/camera";
import { type Challenge, FRONTAL_YAW, isVirtualCamera } from "@/lib/challenge";
import type { CapturedAttempt } from "@/lib/flow-api";
import { loadLandmarker, type Reading, read } from "@/lib/landmarker";

/** After this long, the person may start even if the guidance isn't satisfied: it advises, the server decides. */
const GUIDANCE_GRACE_MS = 8000;

interface CameraViewProps {
  tip: string | null;
  getChallenge: () => Promise<Challenge>;
  onCaptured: (attempt: CapturedAttempt) => void;
  onCameraError: (error: unknown) => void;
}

/** The oval the person lines their face up with. While the check runs, its outline marches. */
function FaceGuide({ active, good }: { active: boolean; good: boolean }) {
  const tone = active || good ? "stroke-brand-400" : "stroke-white/80";
  return (
    <svg viewBox="0 0 400 300" className="pointer-events-none absolute inset-0 size-full" aria-hidden="true">
      <defs>
        <mask id="face-window">
          <rect width="400" height="300" fill="white" />
          <ellipse cx="200" cy="146" rx="86" ry="110" fill="black" />
        </mask>
      </defs>
      <rect width="400" height="300" fill="rgb(9 9 11 / 0.5)" mask="url(#face-window)" />
      <ellipse
        cx="200"
        cy="146"
        rx="86"
        ry="110"
        fill="none"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray={active ? "6 10" : undefined}
        className={`${active ? "motion-safe:animate-march" : ""} ${tone}`}
      />
    </svg>
  );
}

/** Plain words for what the landmarker sees, and whether the face is ready. */
function guidance(reading: Reading | null): { hint: string; good: boolean } {
  if (reading === null || reading.faces === 0) {
    return { hint: "We can't see your face yet. Look at the camera.", good: false };
  }
  if (reading.faces > 1) {
    return { hint: "Make sure only you are in view.", good: false };
  }
  if (!reading.closeEnough) {
    return { hint: "Move a little closer.", good: false };
  }
  if (!reading.centred) {
    return { hint: "Centre your face in the oval.", good: false };
  }
  if (reading.angles !== null && Math.abs(reading.angles.yaw) > FRONTAL_YAW) {
    return { hint: "Look straight at the camera.", good: false };
  }
  return { hint: "That's good. Press Start when you're ready.", good: true };
}

export function CameraView({ tip, getChallenge, onCaptured, onCameraError }: CameraViewProps) {
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const landmarker = useRef<FaceLandmarker | null>(null);
  const reading = useRef<Reading | null>(null);
  const hidden = useRef({ since: null as number | null, total: 0 });
  const [ready, setReady] = useState(false);
  const [guide, setGuide] = useState<{ hint: string; good: boolean } | null>(null);
  const [graceOver, setGraceOver] = useState(false);
  const [running, setRunning] = useState(false);
  const [colour, setColour] = useState<string | null>(null);
  const [cue, setCue] = useState<string | null>(null);
  const [progress, setProgress] = useState<[number, number]>([0, 0]);

  useEffect(() => {
    let active = true;
    openCamera().then(
      (media) => {
        if (!active) {
          closeCamera(media);
          return;
        }
        stream.current = media;
        if (video.current !== null) {
          video.current.srcObject = media;
        }
      },
      (error: unknown) => {
        if (active) {
          onCameraError(error);
        }
      },
    );
    return () => {
      active = false;
      closeCamera(stream.current);
      stream.current = null;
    };
  }, [onCameraError]);

  // Guidance: read the face on every screen refresh, for as long as the camera is open.
  useEffect(() => {
    if (!ready) {
      return;
    }
    let active = true;
    let frame = 0;
    const grace = setTimeout(() => setGraceOver(true), GUIDANCE_GRACE_MS);
    loadLandmarker().then((loaded) => {
      if (!active) {
        loaded?.close();
        return;
      }
      landmarker.current = loaded;
      const loop = () => {
        if (!active || landmarker.current === null || video.current === null) {
          return;
        }
        reading.current = read(landmarker.current, video.current, performance.now());
        const next = guidance(reading.current);
        setGuide((previous) => (previous?.hint === next.hint ? previous : next));
        frame = requestAnimationFrame(loop);
      };
      if (loaded === null) {
        setGraceOver(true);
      } else {
        loop();
      }
    });
    return () => {
      active = false;
      clearTimeout(grace);
      cancelAnimationFrame(frame);
      landmarker.current?.close();
      landmarker.current = null;
    };
  }, [ready]);

  // Time the page spends hidden during the check is reported: someone else's video may be playing in its place.
  useEffect(() => {
    const onChange = () => {
      const now = performance.now();
      if (document.hidden) {
        hidden.current.since = now;
      } else if (hidden.current.since !== null) {
        hidden.current.total += now - hidden.current.since;
        hidden.current.since = null;
      }
    };
    document.addEventListener("visibilitychange", onChange);
    return () => document.removeEventListener("visibilitychange", onChange);
  }, []);

  async function start() {
    if (video.current === null) {
      return;
    }
    setRunning(true);
    try {
      const challenge = await getChallenge();
      const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      hidden.current = { since: null, total: 0 };
      const run = await runChallenge(video.current, challenge, {
        onColour: setColour,
        onCue: setCue,
        onProgress: (taken, total) => setProgress([taken, total]),
        readAngles: () => reading.current?.angles ?? null,
        calm,
      });
      const label = stream.current?.getVideoTracks()[0]?.label ?? "";
      closeCamera(stream.current);
      stream.current = null;
      onCaptured({
        challengeId: challenge.id,
        frames: run.frames,
        lightStartedMs: run.lightStartedMs,
        signals: {
          automation: navigator.webdriver === true,
          virtualCamera: isVirtualCamera(label),
          hiddenMs: hidden.current.total,
          lightShown: !calm,
        },
      });
    } catch (error) {
      setColour(null);
      onCameraError(error);
    }
  }

  const [taken, total] = progress;
  const message = running
    ? (cue ?? (colour === null ? `Hold still… ${taken} of ${total}` : "Keep looking at the screen."))
    : (tip ?? guide?.hint ?? "Starting the camera…");

  return (
    <div>
      {colour === null
        ? null
        : createPortal(
            // Drawn straight into the page body: inside the card, whose blurred background turns it into the frame
            // for "fixed" elements, the colour would light only the card, not the whole screen.
            <div
              aria-hidden="true"
              className="fixed inset-0 z-40 grid place-items-center transition-colors duration-200"
              style={{ backgroundColor: colour }}
            >
              <p className="rounded-full bg-black/60 px-5 py-2 text-lg font-medium text-white">
                Keep looking at the screen.
              </p>
            </div>,
            document.body,
          )}
      <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-zinc-900 ring-1 ring-black/5 dark:ring-white/10">
        <video
          ref={video}
          autoPlay
          playsInline
          muted
          onLoadedData={() => setReady(true)}
          className="size-full -scale-x-100 object-cover"
        />
        <FaceGuide active={running} good={guide?.good ?? false} />
        {ready ? null : (
          <p className="absolute inset-0 grid place-items-center text-sm text-zinc-300">
            Starting the camera…
          </p>
        )}
        {cue === null ? null : (
          <p className="absolute inset-x-4 bottom-4 rounded-xl bg-black/70 px-4 py-3 text-center text-lg font-medium text-white">
            {cue}
          </p>
        )}
      </div>
      <p
        aria-live="polite"
        className="mt-4 min-h-12 text-center text-[15px] leading-relaxed text-zinc-700 dark:text-zinc-300"
      >
        {message}
      </p>
      <button
        type="button"
        className={`${accentButton} mt-2`}
        disabled={!ready || running || !(guide?.good || graceOver)}
        onClick={start}
      >
        {running ? "Checking you're here…" : "Start"}
      </button>
    </div>
  );
}
