"use client";

import { useEffect, useRef, useState } from "react";

import { Arch } from "./arch";

/** Whether this browser can draw the 3D face: WebGL works, and the person hasn't asked for less motion. */
function canAnimate(): boolean {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return false;
  }
  try {
    return document.createElement("canvas").getContext("webgl2") !== null;
  } catch {
    return false;
  }
}

/**
 * The home page's hero (decision D1): the doorway with a face of points of light inside it, in 3D. The page first
 * shows the still artwork; once the browser is idle, and only if it can animate, the 3D scene's code is fetched and
 * takes the face's place. Anything that goes wrong leaves the still artwork as it was.
 */
export function FaceHero() {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [live, setLive] = useState(false);

  useEffect(() => {
    if (!canAnimate()) {
      return;
    }
    let stop: (() => void) | null = null;
    let cancelled = false;
    const begin = () => {
      import("./face-scene")
        .then(({ startFaceScene }) => {
          if (cancelled || canvas.current === null) {
            return;
          }
          stop = startFaceScene(canvas.current);
          setLive(true);
        })
        .catch(() => setLive(false));
    };
    // Wait for a quiet moment, so the 3D code never competes with the page's first paint and first input.
    const idle = window.requestIdleCallback?.(begin, { timeout: 2500 }) ?? window.setTimeout(begin, 1200);
    return () => {
      cancelled = true;
      window.cancelIdleCallback?.(idle);
      window.clearTimeout(idle);
      stop?.();
    };
  }, []);

  return (
    <div className="relative w-full max-w-72">
      <Arch face={!live} />
      {/* The face's box inside the doorway, in the artwork's own proportions (240 × 280). Decoration only. */}
      <div aria-hidden="true" className="absolute top-[22%] left-[20%] h-[56%] w-[60%]">
        <canvas ref={canvas} className={`size-full ${live ? "" : "invisible"}`} />
      </div>
    </div>
  );
}
