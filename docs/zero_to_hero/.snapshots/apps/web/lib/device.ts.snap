/** A random ID this browser keeps for the verify page, so the API can limit how many age checks one device tries.
 * It is not a fingerprint: it says nothing about the device or the person, and clearing the site's data resets it. */

const KEY = "dwarpal.device";
const WELL_FORMED = /^[A-Za-z0-9-]{16,64}$/;

type Store = Pick<Storage, "getItem" | "setItem">;

function browserStorage(): Store | null {
  try {
    return globalThis.localStorage ?? null;
  } catch {
    return null;
  }
}

/** This browser's device ID, created the first time — or `null` where the page may not store anything. */
export function deviceId(storage: Store | null = browserStorage()): string | null {
  if (storage === null) {
    return null;
  }
  try {
    const known = storage.getItem(KEY);
    if (known !== null && WELL_FORMED.test(known)) {
      return known;
    }
    const fresh = crypto.randomUUID();
    storage.setItem(KEY, fresh);
    return fresh;
  } catch {
    return null;
  }
}
