/**
 * The Age Pass in the browser (Phase 9, decision D21). After a passed check, the verify page makes one key pair per
 * pass — the private halves can't be read out, even by this page — and keeps the passes Dwarpal signs for them in
 * this browser's IndexedDB. A later check can then show one pass instead of the camera: only the age line it needs,
 * signed with that pass's key over the server's one-time nonce. Each pass is used once, so websites can't link them.
 * The checks happen on the server (services/api/src/dwarpal_api/domain/agepass.py).
 */

import { fromBase64Url, toBase64Url } from "./passkeys";

/** A public key as the API takes it: an EC key on P-256, its two coordinates, and nothing else. */
export interface HolderKey {
  kty: "EC";
  crv: "P-256";
  x: string;
  y: string;
}

/** A pass as this browser keeps it. */
export interface KeptPass {
  pass: string;
  key: CryptoKey; // the private half, not extractable
  lines: number[];
  expiresAt: number; // milliseconds since 1970
  livemode: boolean;
}

/** A pass that can answer a check, with its place in storage and the line it will show. */
export interface Usable {
  id: IDBValidKey;
  kept: KeptPass;
  line: number;
}

const encoder = new TextEncoder();

/** A pass's disclosures — the hidden claims it can reveal one by one — by the claim each reveals. */
export function disclosuresOf(pass: string): Map<string, string> {
  const [, ...rest] = pass.split("~");
  const found = new Map<string, string>();
  for (const disclosure of rest.filter(Boolean)) {
    const decoded: unknown = JSON.parse(new TextDecoder().decode(fromBase64Url(disclosure)));
    if (Array.isArray(decoded) && typeof decoded[1] === "string") {
      found.set(decoded[1], disclosure);
    }
  }
  return found;
}

/** The lowest line a pass states at or above the age asked: the least it needs to reveal. */
export function lineFor(lines: readonly number[], minAge: number): number | null {
  const enough = lines.filter((line) => line >= minAge);
  return enough.length === 0 ? null : Math.min(...enough);
}

/** New key pairs, one per pass. The private halves can sign but never be exported. */
export async function newKeys(count: number): Promise<CryptoKeyPair[]> {
  const algorithm: EcKeyGenParams = { name: "ECDSA", namedCurve: "P-256" };
  return Promise.all(
    Array.from({ length: count }, () => crypto.subtle.generateKey(algorithm, false, ["sign", "verify"])),
  );
}

/** A public key in the shape the API takes (the browser's own export adds fields the API refuses). */
export async function holderKey(key: CryptoKey): Promise<HolderKey> {
  const { x = "", y = "" } = await crypto.subtle.exportKey("jwk", key);
  return { kty: "EC", crv: "P-256", x, y };
}

/**
 * A presentation: the signed pass, the one disclosure for `line`, and a key-binding JWT signed with the pass's key
 * over the server's nonce, the audience (this session), the time, and a hash of everything before it — so the server
 * knows the holder of the key made it, for this session, just now, and with this disclosure.
 */
export async function presentation(
  pass: string,
  key: CryptoKey,
  line: number,
  nonce: string,
  audience: string,
  now: number = Date.now(),
): Promise<string> {
  const signed = pass.split("~")[0] ?? "";
  const disclosure = disclosuresOf(pass).get(`age_over_${line}`);
  if (disclosure === undefined) {
    throw new Error(`this pass doesn't state the ${line} line`);
  }
  const signedPart = `${signed}~${disclosure}~`;
  const sdHash = toBase64Url(await crypto.subtle.digest("SHA-256", encoder.encode(signedPart)));
  const json = (value: object) => toBase64Url(encoder.encode(JSON.stringify(value)));
  const header = json({ alg: "ES256", typ: "kb+jwt" });
  const payload = json({ iat: Math.floor(now / 1000), aud: audience, nonce, sd_hash: sdHash });
  // WebCrypto's ECDSA signature is the 64 bytes r‖s that JOSE's ES256 expects, with no further encoding.
  const signature = await crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    key,
    encoder.encode(`${header}.${payload}`),
  );
  return `${signedPart}${header}.${payload}.${toBase64Url(signature)}`;
}

// --- Keeping passes: IndexedDB, which can hold a CryptoKey as it is, still unexportable. ---

const DATABASE = "dwarpal-age-pass";
const STORE = "passes";
/** A pass isn't offered in its last minute: the check could outlast it. */
const MARGIN_MS = 60_000;

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE, { autoIncrement: true });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/** Run `work` in one transaction on the passes, and wait until the transaction is done. */
async function withStore<T>(mode: IDBTransactionMode, work: (store: IDBObjectStore) => T): Promise<T> {
  const database = await open();
  try {
    return await new Promise<T>((resolve, reject) => {
      const transaction = database.transaction(STORE, mode);
      const result = work(transaction.objectStore(STORE));
      transaction.oncomplete = () => resolve(result);
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(transaction.error);
    });
  } finally {
    database.close();
  }
}

/** Keep a new batch of passes. */
export async function keep(passes: readonly KeptPass[]): Promise<void> {
  await withStore("readwrite", (store) => {
    for (const kept of passes) {
      store.add(kept);
    }
  });
}

/** Every kept pass, with its place in storage. */
async function everything(): Promise<Array<{ id: IDBValidKey; kept: KeptPass }>> {
  const found: Array<{ id: IDBValidKey; kept: KeptPass }> = [];
  await withStore("readonly", (store) => {
    const request = store.openCursor();
    request.onsuccess = () => {
      const cursor = request.result;
      if (cursor !== null) {
        found.push({ id: cursor.primaryKey, kept: cursor.value as KeptPass });
        cursor.continue();
      }
    };
  });
  return found;
}

/** The oldest kept pass that can answer a check at `minAge` in this mode, or null. Expired passes are removed. */
export async function usable(
  minAge: number,
  livemode: boolean,
  now: number = Date.now(),
): Promise<Usable | null> {
  const all = await everything();
  const expired = all.filter(({ kept }) => kept.expiresAt <= now + MARGIN_MS);
  if (expired.length > 0) {
    await withStore("readwrite", (store) => {
      for (const { id } of expired) {
        store.delete(id);
      }
    });
  }
  for (const { id, kept } of all) {
    const line = lineFor(kept.lines, minAge);
    if (kept.expiresAt > now + MARGIN_MS && kept.livemode === livemode && line !== null) {
      return { id, kept, line };
    }
  }
  return null;
}

/** Remove one pass: used, or refused by the server. */
export async function forget(id: IDBValidKey): Promise<void> {
  await withStore("readwrite", (store) => {
    store.delete(id);
  });
}
