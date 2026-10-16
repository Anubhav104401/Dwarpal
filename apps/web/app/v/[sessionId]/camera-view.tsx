"use client";

import { useEffect, useRef, useState } from "react";

import { accentButton } from "@/components/shell";
import { BURST_SIZE, captureBurst, closeCamera, openCamera } from "@/lib/camera";
import type { CapturedFrame } from "@/lib/flow-api";

interface CameraViewProps {
  tip: string | null;
  onCaptured: (frames: CapturedFrame[]) => void;
  onCameraError: (error: unknown) => void;
}

/** The oval the person lines their face up with. While photos are taken, its outline marches. */
function FaceGuide({ capturing }: { capturing: boolean }) {
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
        strokeDasharray={capturing ? "6 10" : undefined}
        className={capturing ? "motion-safe:animate-march stroke-brand-400" : "stroke-white/80"}
      />
    </svg>
  );
}

export function CameraView({ tip, onCaptured, onCameraError }: CameraViewProps) {
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const [ready, setReady] = useState(false);
  const [taken, setTaken] = useState(0);
  const [capturing, setCapturing] = useState(false);

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

  async function capture() {
    if (video.current === null) {
      return;
    }
    setCapturing(true);
    try {
      const frames = await captureBurst(video.current, setTaken);
      closeCamera(stream.current);
      stream.current = null;
      onCaptured(frames);
    } catch (error) {
      onCameraError(error);
    }
  }

  return (
    <div>
      <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-zinc-900 ring-1 ring-black/5 dark:ring-white/10">
        <video
          ref={video}
          autoPlay
          playsInline
          muted
          onLoadedData={() => setReady(true)}
          className="size-full -scale-x-100 object-cover"
        />
        <FaceGuide capturing={capturing} />
        {ready ? null : (
          <p className="absolute inset-0 grid place-items-center text-sm text-zinc-300">
            Starting the camera…
          </p>
        )}
      </div>
      <p
        aria-live="polite"
        className="mt-4 min-h-12 text-center text-[15px] leading-relaxed text-zinc-700 dark:text-zinc-300"
      >
        {capturing
          ? `Hold still… ${taken} of ${BURST_SIZE}`
          : (tip ?? "Centre your face in the oval, in good light.")}
      </p>
      <button
        type="button"
        className={`${accentButton} mt-2`}
        disabled={!ready || capturing}
        onClick={capture}
      >
        {capturing ? "Taking photos…" : "Take photos"}
      </button>
    </div>
  );
}
