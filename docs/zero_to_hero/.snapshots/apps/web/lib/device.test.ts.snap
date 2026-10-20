import { describe, expect, it } from "vitest";

import { deviceId } from "./device";

function memory(): Pick<Storage, "getItem" | "setItem"> {
  const values = new Map<string, string>();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => {
      values.set(key, value);
    },
  };
}

describe("the device ID", () => {
  it("is created once, then kept", () => {
    const storage = memory();
    const first = deviceId(storage);
    expect(first).toMatch(/^[0-9a-f-]{36}$/);
    expect(deviceId(storage)).toBe(first);
  });

  it("replaces a malformed value, and is null where nothing may be stored", () => {
    const storage = memory();
    storage.setItem("dwarpal.device", "<script>");
    expect(deviceId(storage)).toMatch(/^[0-9a-f-]{36}$/);
    expect(deviceId(null)).toBeNull();
    const refusing = {
      getItem: () => null,
      setItem: () => {
        throw new Error("blocked");
      },
    };
    expect(deviceId(refusing)).toBeNull();
  });
});
