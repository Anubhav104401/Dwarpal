import { describe, expect, it } from "vitest";

import { GUIDE_ASPECT, guideShare } from "./document-camera";

describe("guideShare", () => {
  it("fills 90 % of the height of a wide webcam picture, in the passport page's shape", () => {
    const share = guideShare(1920, 1080);
    expect(share.height).toBeCloseTo(0.9);
    expect((share.width * 1920) / (share.height * 1080)).toBeCloseTo(GUIDE_ASPECT);
  });

  it("fills 90 % of the width of an older 4:3 picture, and of a phone's upright one", () => {
    for (const [width, height] of [
      [640, 480],
      [1080, 1920],
    ] as const) {
      const share = guideShare(width, height);
      expect(share.width).toBeCloseTo(0.9);
      expect(share.height).toBeLessThanOrEqual(0.9);
      expect((share.width * width) / (share.height * height)).toBeCloseTo(GUIDE_ASPECT);
    }
  });
});
