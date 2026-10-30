import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { VerifyAgeButton } from "../src/index.js";

const never = () => new Promise<string>(() => {});

describe("VerifyAgeButton", () => {
  it("is a plain button, with its own words or the default ones", () => {
    expect(renderToStaticMarkup(<VerifyAgeButton createSession={never} />)).toBe(
      '<button type="button" aria-disabled="false" aria-busy="false">Verify my age</button>',
    );
    expect(
      renderToStaticMarkup(
        <VerifyAgeButton createSession={never} className="cta">
          Enter the cellar
        </VerifyAgeButton>,
      ),
    ).toBe(
      '<button type="button" class="cta" aria-disabled="false" aria-busy="false">Enter the cellar</button>',
    );
  });
});
