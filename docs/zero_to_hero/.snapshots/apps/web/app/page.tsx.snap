import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import { Mark } from "@/components/shell";
import { Badge, button, panel } from "@/components/ui";
import { publishedModel } from "@/lib/published-model";

import { Accuracy } from "./_home/accuracy";
import { Arch } from "./_home/arch";

// The one public page that should be found: the layout asks search engines to pass by every other.
export const metadata: Metadata = {
  title: "Dwarpal · Private age checks",
  description:
    "Age checks that look, decide and forget: a few seconds of camera, no photos kept, only a yes or no.",
  robots: { index: true, follow: true },
};

const apiUrl =
  process.env.DWARPAL_API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_DWARPAL_API_URL ?? "http://localhost:8000";

const STEPS = [
  {
    title: "Look",
    text: "The website opens the check over its page. You look at your camera for a few seconds and turn your head when asked, so a photo can't simply stand in for you.",
  },
  {
    title: "Decide",
    text: "An AI estimates your age from a few frames. It says yes only when it is sure you are over the website's age; when it isn't sure, it says so, and the website can offer a stronger check instead of a guess.",
  },
  {
    title: "Forget",
    text: "The frames are checked once, in memory, and gone. The website receives a signed answer for its age line — old enough, or not — and nothing else.",
  },
];

const PROMISES = [
  [
    "No photos kept",
    "Frames exist only in memory while one request is checked. No part of the system can store them.",
  ],
  ["No identity", "Dwarpal never asks who you are, and the website never learns it from Dwarpal."],
  ["No exact age", "The website learns only whether you meet its age line — not your estimated age."],
  [
    "A signed answer",
    "The answer is a token signed with Dwarpal's keys, which the website checks on its own server.",
  ],
];

const SERVER_CODE = `import { DwarpalClient } from "@dwarpal/node";

const dwarpal = new DwarpalClient({
  apiKey: process.env.DWARPAL_API_KEY!, // on your server only
  baseUrl: "https://api.dwarpal.example",
});

export async function createAgeCheck(): Promise<string> {
  const session = await dwarpal.createSession({
    policy: "uk_osa_18",
    returnUrl: "https://shop.example/age-check/complete",
  });
  return session.url;
}`;

const PAGE_CODE = `import { VerifyAgeButton } from "@dwarpal/react";

<VerifyAgeButton createSession={createAgeCheck}>
  Verify my age
</VerifyAgeButton>`;

const LAWS = [
  {
    place: "United Kingdom",
    law: "Online Safety Act 2023",
    asks: "“Highly effective” age assurance: technically accurate, robust, reliable and fair. Ofcom lists facial age estimation among the methods that can qualify, with an age line set above the legal age.",
    fit: "Lines set with a margin below them, checked against the risk budget; a live-person check; a stronger check when unsure.",
  },
  {
    place: "European Union",
    law: "Digital Services Act, Article 28",
    asks: "Age assurance that is accurate, reliable, robust, non-intrusive and non-discriminatory. The EU's age-verification blueprint proves “over N” without revealing identity.",
    fit: "Only “over N” leaves Dwarpal; errors are measured for each group; people are told what happens before the camera starts.",
  },
  {
    place: "United States",
    law: "State age-verification laws",
    asks: "Age verification for sexual content in many states, upheld by the Supreme Court in Free Speech Coalition v. Paxton (2025).",
    fit: "A signed age token that the website's server verifies itself, with each check's method and policy recorded.",
  },
  {
    place: "Australia",
    law: "Social media minimum age",
    asks: "Reasonable steps to keep under-16s off social media. The national trial recommends layers: estimation first, something more definite when uncertain.",
    fit: "That layering is Dwarpal's design: pass, fail, or a stronger check — with a line at 16.",
  },
  {
    place: "India",
    law: "DPDP Act 2023 and Rules 2025",
    asks: "Anyone under 18 is a child, whose data needs verifiable parental consent; minors shouldn't be able to fake their age.",
    fit: "An adult check that keeps no identity — usable for the consenting parent too. Aadhaar Secure QR is planned, not built.",
  },
];

const QUESTIONS = [
  [
    "Are my photos stored?",
    "No. The frames from your camera are checked in memory, during one request, and never written anywhere. What is kept is numbers about the check — scores and the outcome — for the website's retention period.",
  ],
  [
    "Does the website learn my age?",
    "No. It learns only whether you meet its age line, in a token Dwarpal signs. Not your estimated age, not a photo, not who you are.",
  ],
  [
    "I'm an adult and it wasn't sure. Why?",
    "Faces don't carry birth certificates. To keep people under the age out, the AI says yes only when it is sure, and people just over the age are the hardest to be sure about. When it isn't sure, the website can offer another way to show your age.",
  ],
  [
    "Can a photo or a video fool it?",
    "It is built not to be: you are asked to turn your head in an order chosen for that check, and a separate model looks for screens and prints. It isn't perfect, and the results of the attacks tried so far are published in its practice statement.",
  ],
  [
    "Is it fair to everyone?",
    "Its errors are measured for each age and group of people. The model now running doesn't yet meet Dwarpal's own standard for that, which is why it decides test checks only.",
  ],
  [
    "What if I can't use a camera?",
    "A website using Dwarpal should always offer another way. Checks with an ID document are being built; until then, the website's own alternative applies.",
  ],
];

const SECTIONS = [
  ["how-it-works", "How it works"],
  ["accuracy", "Accuracy"],
  ["developers", "Developers"],
  ["compliance", "Compliance"],
  ["faq", "Questions"],
];

function Section({
  id,
  title,
  lead,
  children,
}: {
  id: string;
  title: string;
  lead: string;
  children: ReactNode;
}) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="scroll-mt-20 py-14 sm:py-20">
      <h2 id={`${id}-title`} className="text-display font-semibold">
        {title}
      </h2>
      <p className="mt-3 max-w-2xl text-lg leading-relaxed text-ink-600 dark:text-ink-400">{lead}</p>
      {children}
    </section>
  );
}

/** The home page: what Dwarpal is, for people and for the websites that use it (the design's marketing site). */
export default async function Home() {
  const model = await publishedModel(apiUrl);
  const shop = process.env.DWARPAL_DEMO_SHOP_URL;
  return (
    <div className="relative">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-[32rem] bg-[radial-gradient(60%_100%_at_50%_0%,color-mix(in_oklab,var(--color-brand-400)_22%,transparent),transparent_70%)]"
      />
      <header className="relative mx-auto flex max-w-5xl items-center gap-2.5 px-4 py-5">
        <Mark />
        <span className="text-[15px] font-semibold tracking-tight">Dwarpal</span>
        <nav aria-label="Sections" className="ml-auto hidden gap-1 md:flex">
          {SECTIONS.map(([id, label]) => (
            <a key={id} href={`#${id}`} className={button("quiet", "compact")}>
              {label}
            </a>
          ))}
        </nav>
        <Link href="/console" className={`${button("primary", "compact")} ml-auto md:ml-2`}>
          Console
        </Link>
      </header>

      <main className="relative mx-auto max-w-5xl px-4">
        <div className="grid items-center gap-10 py-12 sm:py-20 md:grid-cols-[3fr_2fr]">
          <div>
            <Badge tone="brand">In development · test checks only</Badge>
            <h1 className="mt-5 text-5xl font-semibold tracking-tight sm:text-6xl">Look. Decide. Forget.</h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-ink-600 dark:text-ink-400">
              Dwarpal tells a website whether someone is old enough, from a few seconds of camera — and keeps
              no photos. The website learns one thing: old enough, or not.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              {shop === undefined ? null : (
                <a href={shop} className={button("accent", "small")}>
                  Try it on the demo shop
                </a>
              )}
              <a href="#developers" className={button("quiet", "small")}>
                Add it to your website
              </a>
            </div>
          </div>
          <div className="flex justify-center">
            <Arch />
          </div>
        </div>

        <Section
          id="how-it-works"
          title="How it works"
          lead="Three steps, a few seconds each. The website never sees your face."
        >
          <ol className="mt-8 grid gap-4 md:grid-cols-3">
            {STEPS.map((step, i) => (
              <li key={step.title} className={panel}>
                <p className="text-sm font-semibold text-brand-700 dark:text-brand-300">Step {i + 1}</p>
                <h3 className="mt-1 text-lg font-semibold">{step.title}</h3>
                <p className="mt-2 leading-relaxed text-ink-600 dark:text-ink-400">{step.text}</p>
              </li>
            ))}
          </ol>
        </Section>

        <Section
          id="privacy"
          title="The privacy promise"
          lead="An age check shouldn't cost you your privacy. These hold for every check, by design rather than by policy."
        >
          <dl className="mt-8 grid gap-4 sm:grid-cols-2">
            {PROMISES.map(([title, text]) => (
              <div key={title} className={panel}>
                <dt className="font-semibold">{title}</dt>
                <dd className="mt-1.5 leading-relaxed text-ink-600 dark:text-ink-400">{text}</dd>
              </div>
            ))}
          </dl>
        </Section>

        <Section
          id="accuracy"
          title="Accuracy, measured"
          lead="The figures of the age model running now, read from it as this page loads. Each age line trades keeping minors out against sending adults to a stronger check."
        >
          <Accuracy model={model} />
        </Section>

        <Section
          id="developers"
          title="For developers"
          lead="Your server creates a session; your page opens the check; your server verifies the signed answer. The developer guides cover the rest."
        >
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {[
              ["On your server", SERVER_CODE],
              ["On your page", PAGE_CODE],
            ].map(([title, code]) => (
              <figure key={title} className={panel}>
                <figcaption className="text-sm font-semibold">{title}</figcaption>
                <pre className="mt-3 whitespace-pre-wrap break-words rounded-xl bg-ink-950 p-4 text-[13px] leading-relaxed text-ink-100">
                  <code>{code}</code>
                </pre>
              </figure>
            ))}
          </div>
          <p className="mt-4 text-sm text-ink-600 dark:text-ink-400">
            The guides — the browser and Node.js SDKs, and a checklist before going live — are in the
            repository's <code className="font-mono">docs/developers</code> folder, with the API's OpenAPI
            document.
          </p>
        </Section>

        <Section
          id="compliance"
          title="Where it fits"
          lead="What the main rules ask of an age check, and how Dwarpal's design answers it."
        >
          <div className="mt-8 grid gap-4">
            {LAWS.map((row) => (
              <article key={row.place} className={`${panel} grid gap-3 md:grid-cols-[1fr_2fr_2fr]`}>
                <h3 className="font-semibold">
                  {row.place}
                  <span className="block text-sm font-normal text-ink-600 dark:text-ink-400">{row.law}</span>
                </h3>
                <div>
                  <p className="text-xs font-medium uppercase text-ink-600 dark:text-ink-400">What it asks</p>
                  <p className="mt-1 leading-relaxed">{row.asks}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-ink-600 dark:text-ink-400">
                    How Dwarpal answers
                  </p>
                  <p className="mt-1 leading-relaxed">{row.fit}</p>
                </div>
              </article>
            ))}
          </div>
          <p className="mt-4 text-sm text-ink-600 dark:text-ink-400">
            A summary, not legal advice. Dwarpal is in development and hasn't been assessed under any of these
            rules.
          </p>
        </Section>

        <Section id="faq" title="Questions" lead="What people ask before they look at the camera.">
          <div className="mt-8 divide-y divide-ink-200 border-y border-ink-200 dark:divide-white/10 dark:border-white/10">
            {QUESTIONS.map(([question, answer]) => (
              <details key={question} className="group py-4">
                <summary className="cursor-pointer list-none font-semibold marker:hidden">
                  {question}
                  <span
                    aria-hidden="true"
                    className="float-right text-ink-600 dark:text-ink-400 group-open:rotate-45"
                  >
                    +
                  </span>
                </summary>
                <p className="mt-2 max-w-3xl leading-relaxed text-ink-600 dark:text-ink-400">{answer}</p>
              </details>
            ))}
          </div>
        </Section>

        <section aria-labelledby="demo-title" className={`${panel} mb-16 text-center`}>
          <h2 id="demo-title" className="text-2xl font-semibold tracking-tight">
            See it on a shop
          </h2>
          <p className="mx-auto mt-2 max-w-xl text-ink-600 dark:text-ink-400">
            Amber Cellars, a made-up wine shop, uses Dwarpal at its door, with the same few lines of code.
          </p>
          <div className="mt-5 flex justify-center gap-3">
            {shop === undefined ? null : (
              <a href={shop} className={button("accent", "small")}>
                Visit the demo shop
              </a>
            )}
            <Link href="/console" className={button("quiet", "small")}>
              Open the console
            </Link>
          </div>
        </section>
      </main>

      <footer className="relative border-t border-ink-200 py-8 text-center text-xs leading-relaxed text-ink-600 dark:text-ink-400 dark:border-white/10">
        Dwarpal — the guardian at the gate. In development, and not yet hosted for real visitors.
      </footer>
    </div>
  );
}
