import { describe, expect, it } from "vitest";

import { anglesFrom, isVirtualCamera, reached, readChallenge } from "./challenge";

describe("head angles", () => {
  const rightEye = { x: 0.4, y: 0.4 };
  const leftEye = { x: 0.6, y: 0.4 };
  const mouth = { x: 0.5, y: 0.6 };

  it("measures a frontal face as straight ahead", () => {
    const angles = anglesFrom(rightEye, leftEye, { x: 0.5, y: 0.51 }, mouth);
    expect(angles.yaw).toBeCloseTo(0);
    expect(angles.pitch).toBeCloseTo(0.55);
  });

  it("reads a nose moved towards the picture's right as a turn to the person's left", () => {
    const angles = anglesFrom(rightEye, leftEye, { x: 0.6, y: 0.51 }, mouth);
    expect(reached("turn_left", angles)).toBe(true);
    expect(reached("turn_right", angles)).toBe(false);
  });

  it("reads a nose close to the eyes as a raised head", () => {
    expect(reached("look_up", anglesFrom(rightEye, leftEye, { x: 0.5, y: 0.46 }, mouth))).toBe(true);
    expect(reached("look_up", anglesFrom(rightEye, leftEye, { x: 0.5, y: 0.51 }, mouth))).toBe(false);
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
