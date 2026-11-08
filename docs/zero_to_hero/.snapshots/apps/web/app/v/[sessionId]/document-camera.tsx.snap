"use client";

import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";

import { accentButton, quietButton } from "@/components/shell";
import { closeCamera } from "@/lib/camera";
import { guideShare, openDocumentCamera, takePhoto } from "@/lib/document-camera";

interface DocumentCameraProps {
  /** The photo the person took and accepted: the camera's whole picture, as a JPEG. */
  onTaken: (photo: Blob) => void;
  /** The person would rather choose a file. */
  onChooseFile: () => void;
  /** The camera couldn't be opened (refused, missing or busy). Keep it the same function between renders: a new one
   * opens the camera again. */
  onUnavailable: () => void;
}

interface Size {
  width: number;
  height: number;
}

/** The passport-shaped frame the document is held in, with a dashed box where the lines with `<<<` go. Everything
 * outside it is dimmed by a shadow wide enough to cover the picture. */
function DocumentGuide({ share }: { share: Size }) {
  return (
    <div className="pointer-events-none absolute inset-0 grid place-items-center" aria-hidden="true">
      <div
        className="relative rounded-xl border-[3px] border-white/90 shadow-[0_0_0_100vmax_rgb(9_9_11/0.5)]"
        style={{ width: `${share.width * 100}%`, height: `${share.height * 100}%` }}
      >
        <div className="absolute inset-x-[4%] bottom-[4%] h-[22%] rounded-md border-2 border-dashed border-white/80" />
      </div>
    </div>
  );
}

/** The document camera (decision D43): the webcam's picture with the guide, a photo taken on request, and a look at
 * it before it is used. */
export function DocumentCamera({ onTaken, onChooseFile, onUnavailable }: DocumentCameraProps) {
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const [size, setSize] = useState<Size | null>(null);
  const [photo, setPhoto] = useState<(Size & { blob: Blob; url: string }) | null>(null);
  const [taking, setTaking] = useState(false);
  const t = useTranslations("DocumentCamera");

  // The camera is on only while no photo waits to be looked at: looking at one, or leaving, switches it off.
  useEffect(() => {
    if (photo !== null) {
      return;
    }
    let active = true;
    openDocumentCamera().then(
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
      () => {
        if (active) {
          onUnavailable();
        }
      },
    );
    return () => {
      active = false;
      closeCamera(stream.current);
      stream.current = null;
      setSize(null);
    };
  }, [photo, onUnavailable]);

  // A photo's address in this page is given back once the photo is replaced or the view closes.
  useEffect(() => {
    return () => {
      if (photo !== null) {
        URL.revokeObjectURL(photo.url);
      }
    };
  }, [photo]);

  async function take() {
    const shown = video.current;
    if (shown === null) {
      return;
    }
    setTaking(true);
    try {
      const blob = await takePhoto(shown);
      setPhoto({ blob, url: URL.createObjectURL(blob), width: shown.videoWidth, height: shown.videoHeight });
    } catch {
      onUnavailable();
    } finally {
      setTaking(false);
    }
  }

  const frame = photo ?? size;
  return (
    <div>
      <div
        className="relative overflow-hidden rounded-2xl bg-ink-900 ring-1 ring-black/5 dark:ring-white/10"
        style={{ aspectRatio: frame === null ? "16 / 9" : `${frame.width} / ${frame.height}` }}
      >
        {photo === null ? (
          <>
            <video
              ref={video}
              autoPlay
              playsInline
              muted
              aria-label={t("preview")}
              onLoadedMetadata={(event) =>
                setSize({ width: event.currentTarget.videoWidth, height: event.currentTarget.videoHeight })
              }
              className="size-full object-contain"
            />
            {size === null ? null : <DocumentGuide share={guideShare(size.width, size.height)} />}
          </>
        ) : (
          // A plain <img>: the photo lives only in this page (a `blob:` address), which Next's image service can't fetch.
          // biome-ignore lint/performance/noImgElement: see above
          <img src={photo.url} alt={t("photoAlt")} className="size-full object-contain" />
        )}
      </div>
      <p
        aria-live="polite"
        className="mt-4 min-h-12 text-center text-[15px] leading-relaxed text-ink-700 dark:text-ink-300"
      >
        {photo !== null ? t("check") : size === null ? t("starting") : t("hint")}
      </p>
      {photo === null ? (
        <>
          <p className="text-center text-xs text-ink-600 dark:text-ink-400">{t("notMirrored")}</p>
          <button
            type="button"
            className={`${accentButton} mt-4`}
            disabled={size === null || taking}
            onClick={take}
          >
            {t("take")}
          </button>
          <button type="button" className={`${quietButton} mt-3`} onClick={onChooseFile}>
            {t("file")}
          </button>
        </>
      ) : (
        <>
          <button type="button" className={`${accentButton} mt-2`} onClick={() => onTaken(photo.blob)}>
            {t("use")}
          </button>
          <button type="button" className={`${quietButton} mt-3`} onClick={() => setPhoto(null)}>
            {t("retake")}
          </button>
        </>
      )}
    </div>
  );
}
