import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { LOCALES } from "./locales";

type Messages = { [key: string]: string | Messages };

function read(locale: string): Messages {
  return JSON.parse(readFileSync(join(__dirname, "..", "messages", `${locale}.json`), "utf-8")) as Messages;
}

/** Every text's path, such as `Verify.tries`, with its text. */
function flatten(messages: Messages, prefix = ""): Map<string, string> {
  const out = new Map<string, string>();
  for (const [key, value] of Object.entries(messages)) {
    if (typeof value === "string") {
      out.set(prefix + key, value);
    } else {
      for (const [path, text] of flatten(value, `${prefix + key}.`)) {
        out.set(path, text);
      }
    }
  }
  return out;
}

/** The names a text fills in — `{count}`, `{name, plural, …}` — but not the words inside a plural's branches. */
function placeholders(text: string): string[] {
  return [...text.matchAll(/\{\s*([A-Za-z_]\w*)\s*[,}]/g)].map((match) => match[1] ?? "").sort();
}

/** Rich-text tags such as `<strong>`, which the page turns into elements. */
function tags(text: string): string[] {
  return [...text.matchAll(/<\/?([A-Za-z]\w*)>/g)].map((match) => match[0]).sort();
}

const english = flatten(read("en"));

describe.each(LOCALES.filter((locale) => locale !== "en"))("the %s messages", (locale) => {
  const theirs = flatten(read(locale));

  it("have exactly English's texts, none empty", () => {
    expect([...theirs.keys()].sort()).toEqual([...english.keys()].sort());
    expect([...theirs].filter(([, text]) => text.trim() === "").map(([path]) => path)).toEqual([]);
  });

  it("keep every placeholder and tag, so nothing breaks or shows raw", () => {
    for (const [path, text] of english) {
      const translated = theirs.get(path) ?? "";
      expect(placeholders(translated), path).toEqual(placeholders(text));
      expect(tags(translated), path).toEqual(tags(text));
    }
  });
});

describe("the language menu", () => {
  it("names every language in its own script, the same in every file", () => {
    const names = read("en").Language as Messages;
    for (const locale of LOCALES) {
      expect(typeof names[locale], locale).toBe("string");
      expect((read(locale).Language as Messages)[locale]).toBe(names[locale]);
    }
  });
});
