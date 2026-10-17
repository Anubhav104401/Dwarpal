import { describe, expect, it } from "vitest";

import { anglesFrom, frontalAngles, isVirtualCamera, poseProgress, readChallenge } from "./challenge";

describe("head angles", () => {
  const rightEye = { x: 0.4, y: 0.4 };
  const leftEye = { x: 0.6, y: 0.4 };
  const mouth = { x: 0.5, y: 0.6 };

  it("measures a frontal face as straight ahead", () => {
    const angles = anglesFrom(rightEye, leftEye, { x: 0.5, y: 0.51 }, mouth);
    expect(angles.yaw).toBeCloseTo(0);
    expect(angles.pitch).toBeCloseTo(0.55);
  });

  const front = { yaw: 0, pitch: 0.55 };

  it("reads a nose moved towards the picture's right as a turn to the person's left", () => {
    const angles = anglesFrom(rightEye, leftEye, { x: 0.6, y: 0.51 }, mouth);
    expect(poseProgress("turn_left", angles, front)).toBe(1);
    expect(poseProgress("turn_right", angles, front)).toBe(0);
  });

  it("reads a nose moved towards the eyes as a raised chin, from the person's own frontal pitch", () => {
    expect(poseProgress("look_up", anglesFrom(rightEye, leftEye, { x: 0.5, y: 0.46 }, mouth), front)).toBe(1);
    expect(
      poseProgress("look_up", anglesFrom(rightEye, leftEye, { x: 0.5, y: 0.51 }, mouth), front),
    ).toBeCloseTo(0);
    expect(poseProgress("look_up", { yaw: 0, pitch: 0.55 }, { yaw: 0, pitch: 0.7 })).toBe(1);
  });

  it("measures a partial turn as a share of the target, for the on-screen meter", () => {
    expect(poseProgress("turn_left", { yaw: 0.1, pitch: 0.55 }, front)).toBeCloseTo(0.4);
    expect(poseProgress("turn_right", { yaw: 0.1, pitch: 0.55 }, front)).toBe(0);
  });

  it("takes the frontal angles as the median of the baseline readings", () => {
    const readings = [
      { yaw: 0.02, pitch: 0.6 },
      { yaw: 0.3, pitch: 0.5 },
      { yaw: -0.01, pitch: 0.58 },
    ];
    expect(frontalAngles(readings)).toEqual({ yaw: 0.02, pitch: 0.58 });
    expect(frontalAngles([])).toBeNull();
  });
});

describe("reading a challenge", () => {
  const answer = {
    challenge_id: "abc",
    poses: ["turn_left", "look_up"],
    colours: ["#3c78ff", "#ffd23c"],
    step_ms: 600,
  };

  it("accepts exactly what the page can play", () => {
    expect(readChallenge(answer)).toEqual({
      id: "abc",
      poses: ["turn_left", "look_up"],
      colours: answer.colours,
      stepMs: 600,
    });
  });

  it("refuses unknown poses, malformed colours and implausible timings", () => {
    expect(() => readChallenge({ ...answer, poses: ["somersault"] })).toThrow();
    expect(() => readChallenge({ ...answer, colours: ["red", "blue"] })).toThrow();
    expect(() => readChallenge({ ...answer, step_ms: 50 })).toThrow();
    expect(() => readChallenge({ ...answer, challenge_id: "" })).toThrow();
  });
});

describe("virtual cameras", () => {
  it("recognises common virtual-camera names and nothing else", () => {
    expect(isVirtualCamera("OBS Virtual Camera")).toBe(true);
    expect(isVirtualCamera("ManyCam Virtual Webcam")).toBe(true);
    expect(isVirtualCamera("Integrated Webcam (0bda:5532)")).toBe(false);
    expect(isVirtualCamera("FaceTime HD Camera")).toBe(false);
  });
});
