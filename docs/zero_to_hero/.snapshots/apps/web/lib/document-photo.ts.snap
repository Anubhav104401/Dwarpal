/** The photo of an ID document for the step-up check (Phase 6): scaled down and re-encoded in the browser before it is
 * sent, so it fits the API's limit — and so whatever else the original file carried (its location, the camera's
 * details) is left behind. */

/** The API's limit for a document photo, and the inference service's for its sides. */
export const MAX_DOCUMENT_BYTES = 1024 * 1024;
export const MAX_DOCUMENT_SIDE = 2000;

/** The size to draw a picture at so neither side exceeds `maxSide`, keeping its shape; never enlarged. */
export function fitWithin(width: number, height: number, maxSide: number): { width: number; height: number } {
  const scale = Math.min(1, maxSide / Math.max(width, height));
  return { width: Math.max(1, Math.round(width * scale)), height: Math.max(1, Math.round(height * scale)) };
}

/** JPEG qualities to try, best first, until the photo fits the limit. */
export const QUALITIES = [0.9, 0.8, 0.7, 0.6] as const;

export class DocumentPhotoError extends Error {
  override readonly name = "DocumentPhotoError";
}

/** Draw the chosen file onto a canvas at a size the API accepts, and encode it as a JPEG under the byte limit. */
export async function prepareDocument(file: Blob): Promise<Blob> {
  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch {
    throw new DocumentPhotoError("this file isn't a picture this browser can read");
  }
  const { width, height } = fitWithin(bitmap.width, bitmap.height, MAX_DOCUMENT_SIDE);
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  if (context === null) {
    bitmap.close();
    throw new DocumentPhotoError("this browser can't prepare pictures");
  }
  context.drawImage(bitmap, 0, 0, width, height);
  bitmap.close();
  for (const quality of QUALITIES) {
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
    if (blob !== null && blob.size <= MAX_DOCUMENT_BYTES) {
      return blob;
    }
  }
  throw new DocumentPhotoError("the photo is too detailed to send; try a plainer background");
}
