/** The document camera (decision D43): on a computer, the webcam photographs the ID document, held inside a guide
 * shaped like a passport's photo page. The file chooser stays beside it, for anyone without a camera. */

/** A passport's photo page is 125 × 88 mm (ICAO's TD3 size): the guide has its shape. An ID card (85.6 × 54 mm) fits
 * inside it. */
export const GUIDE_ASPECT = 125 / 88;
/** The guide fills at most this share of the picture's width and of its height. */
const GUIDE_FILL = 0.9;
/** JPEG quality of the photo taken: high, since small print must be read; `prepareDocument` re-encodes it anyway. */
const PHOTO_QUALITY = 0.95;

/** Whether this device is a computer that can film: a mouse or trackpad (a fine pointer) and a camera API. Phones keep
 * their own camera app, opened by the file chooser: its photos of small print are sharper than a video stream's. */
export function canFilmDocument(): boolean {
  return window.matchMedia("(pointer: fine)").matches && navigator.mediaDevices?.getUserMedia !== undefined;
}

/** The guide's size in a picture of `width` × `height`, as shares of each side: as large as fits within 90 % of both,
 * in the passport page's shape. */
export function guideShare(width: number, height: number): { width: number; height: number } {
  const across = Math.min(GUIDE_FILL, (GUIDE_FILL * height * GUIDE_ASPECT) / width);
  return { width: across, height: (across * width) / GUIDE_ASPECT / height };
}

/** Open the camera for a document: the one facing away from the person if there is one, otherwise the webcam — at up
 * to 1920 × 1080, since the lines at the bottom of the page must be read. */
export function openDocumentCamera(): Promise<MediaStream> {
  return navigator.mediaDevices.getUserMedia({
    audio: false,
    video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } },
  });
}

/** The camera's picture now, whole and unmirrored, as a JPEG. The check reads the document wherever it is in the
 * picture, so nothing is cut off: a page held a little outside the guide still counts. */
export function takePhoto(video: HTMLVideoElement): Promise<Blob> {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const context = canvas.getContext("2d");
  if (context === null) {
    return Promise.reject(new Error("this browser can't draw the camera's picture"));
  }
  context.drawImage(video, 0, 0);
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob === null ? reject(new Error("the photo couldn't be encoded")) : resolve(blob)),
      "image/jpeg",
      PHOTO_QUALITY,
    );
  });
}
