import { describe, expect, it } from "vitest";

import { FACE_POINTS, facePoints } from "./face-cloud";

const points = facePoints();
const at = (i: number) => ({ x: points[i * 3] ?? 0, y: points[i * 3 + 1] ?? 0, z: points[i * 3 + 2] ?? 0 });
const all = Array.from({ length: FACE_POINTS }, (_, i) => at(i));

describe("facePoints", () => {
  it("makes one x, y, z for each of the 478 points, all ordinary numbers inside a small box", () => {
    expect(points).toHaveLength(FACE_POINTS * 3);
    for (const value of points) {
      expect(Number.isFinite(value)).toBe(true);
      expect(Math.abs(value)).toBeLessThanOrEqual(1);
    }
  });

  it("is the same face every time", () => {
    expect(facePoints()).toEqual(points);
  });

  it("is taller than it is wide, and faces forward", () => {
    const span = (pick: (p: { x: number; y: number; z: number }) => number) =>
      Math.max(...all.map(pick)) - Math.min(...all.map(pick));
    expect(span((p) => p.y)).toBeGreaterThan(span((p) => p.x));
    expect(all.every((p) => p.z >= -0.2)).toBe(true);
  });

  it("has its nose as the point nearest the viewer, in the middle", () => {
    const nearest = all.reduce((best, p) => (p.z > best.z ? p : best));
    expect(Math.abs(nearest.x)).toBeLessThan(0.15);
    expect(Math.abs(nearest.y)).toBeLessThan(0.4);
  });

  it("spreads its points over both halves alike", () => {
    const left = all.filter((p) => p.x < 0).length;
    expect(Math.abs(left - FACE_POINTS / 2)).toBeLessThan(FACE_POINTS * 0.1);
  });
});
