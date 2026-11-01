import type { Metadata } from "next";
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import type { ReactNode } from "react";

import { LanguageSwitch } from "@/components/language-switch";
import { Mark } from "@/components/shell";
import { Badge, button, panel } from "@/components/ui";
import { publishedModel } from "@/lib/published-model";

import { Accuracy } from "./_home/accuracy";
import { FaceHero } from "./_home/face-hero";

// The one public page that should be found: the layout asks search engines to pass by every other. Its title and
// description are in the visitor's language.
export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("Home");
  return { title: t("metaTitle"), description: t("metaDescription"), robots: { index: true, follow: true } };
}

const apiUrl =
  process.env.DWARPAL_API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_DWARPAL_API_URL ?? "http://localhost:8000";

// The page's words are in `messages/` (decision D2): `Home` there. These are the keys, in the order shown.
const STEPS = ["look", "decide", "forget"] as const;
const PROMISES = ["photos", "identity", "age", "signed"] as const;

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

const LAWS = ["uk", "eu", "us", "au", "in"] as const;
const QUESTIONS = ["stored", "age", "unsure", "fooled", "fair", "camera"] as const;
const SECTIONS = ["how-it-works", "accuracy", "developers", "compliance", "faq"] as const;

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
  const t = await getTranslations("Home");
  return (
    <div className="relative">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-[32rem] bg-[radial-gradient(60%_100%_at_50%_0%,color-mix(in_oklab,var(--color-brand-400)_22%,transparent),transparent_70%)]"
      />
      <header className="relative mx-auto flex max-w-5xl items-center gap-2.5 px-4 py-5">
        <Mark />
        <span className="text-[15px] font-semibold tracking-tight">Dwarpal</span>
        <nav aria-label={t("sectionsLabel")} className="ml-auto hidden gap-1 lg:flex">
          {SECTIONS.map((id) => (
            <a key={id} href={`#${id}`} className={button("quiet", "compact")}>
              {t(`nav.${id}`)}
            </a>
          ))}
        </nav>
        <span className="ml-auto lg:ml-2">
          <LanguageSwitch />
        </span>
        <Link href="/console" className={button("primary", "compact")}>
          {t("console")}
        </Link>
      </header>

      <main className="relative mx-auto max-w-5xl px-4">
        <div className="grid items-center gap-10 py-12 sm:py-20 md:grid-cols-[3fr_2fr]">
          <div>
            <Badge tone="brand">{t("badge")}</Badge>
            <h1 className="mt-5 text-5xl font-semibold tracking-tight sm:text-6xl">{t("title")}</h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-ink-600 dark:text-ink-400">
              {t("lead")}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              {shop === undefined ? null : (
                <a href={shop} className={button("accent", "small")}>
                  {t("tryShop")}
                </a>
              )}
              <a href="#developers" className={button("quiet", "small")}>
                {t("addToSite")}
              </a>
            </div>
          </div>
          <div className="flex justify-center">
            <FaceHero />
          </div>
        </div>

        <Section id="how-it-works" title={t("how.title")} lead={t("how.lead")}>
          <ol className="mt-8 grid gap-4 md:grid-cols-3">
            {STEPS.map((step, i) => (
              <li key={step} className={panel}>
                <p className="text-sm font-semibold text-brand-700 dark:text-brand-300">
                  {t("how.step", { number: i + 1 })}
                </p>
                <h3 className="mt-1 text-lg font-semibold">{t(`how.${step}.title`)}</h3>
                <p className="mt-2 leading-relaxed text-ink-600 dark:text-ink-400">{t(`how.${step}.text`)}</p>
              </li>
            ))}
          </ol>
        </Section>

        <Section id="privacy" title={t("privacy.title")} lead={t("privacy.lead")}>
          <dl className="mt-8 grid gap-4 sm:grid-cols-2">
            {PROMISES.map((promise) => (
              <div key={promise} className={panel}>
                <dt className="font-semibold">{t(`privacy.${promise}.title`)}</dt>
                <dd className="mt-1.5 leading-relaxed text-ink-600 dark:text-ink-400">
                  {t(`privacy.${promise}.text`)}
                </dd>
              </div>
            ))}
          </dl>
        </Section>

        <Section id="accuracy" title={t("accuracy.title")} lead={t("accuracy.lead")}>
          <Accuracy model={model} />
        </Section>

        <Section id="developers" title={t("developers.title")} lead={t("developers.lead")}>
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {[
              [t("developers.server"), SERVER_CODE],
              [t("developers.page"), PAGE_CODE],
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
            {t.rich("developers.guides", { code: (chunks) => <code className="font-mono">{chunks}</code> })}
          </p>
        </Section>

        <Section id="compliance" title={t("compliance.title")} lead={t("compliance.lead")}>
          <div className="mt-8 grid gap-4">
            {LAWS.map((law) => (
              <article key={law} className={`${panel} grid gap-3 md:grid-cols-[1fr_2fr_2fr]`}>
                <h3 className="font-semibold">
                  {t(`compliance.${law}.place`)}
                  <span className="block text-sm font-normal text-ink-600 dark:text-ink-400">
                    {t(`compliance.${law}.law`)}
                  </span>
                </h3>
                <div>
                  <p className="text-xs font-medium uppercase text-ink-600 dark:text-ink-400">
                    {t("compliance.asks")}
                  </p>
                  <p className="mt-1 leading-relaxed">{t(`compliance.${law}.asks`)}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-ink-600 dark:text-ink-400">
                    {t("compliance.answers")}
                  </p>
                  <p className="mt-1 leading-relaxed">{t(`compliance.${law}.fit`)}</p>
                </div>
              </article>
            ))}
          </div>
          <p className="mt-4 text-sm text-ink-600 dark:text-ink-400">{t("compliance.note")}</p>
        </Section>

        <Section id="faq" title={t("faq.title")} lead={t("faq.lead")}>
          <div className="mt-8 divide-y divide-ink-200 border-y border-ink-200 dark:divide-white/10 dark:border-white/10">
            {QUESTIONS.map((question) => (
              <details key={question} className="group py-4">
                <summary className="cursor-pointer list-none font-semibold marker:hidden">
                  {t(`faq.${question}.q`)}
                  <span
                    aria-hidden="true"
                    className="float-right text-ink-600 dark:text-ink-400 group-open:rotate-45"
                  >
                    +
                  </span>
                </summary>
                <p className="mt-2 max-w-3xl leading-relaxed text-ink-600 dark:text-ink-400">
                  {t(`faq.${question}.a`)}
                </p>
              </details>
            ))}
          </div>
        </Section>

        <section aria-labelledby="demo-title" className={`${panel} mb-16 text-center`}>
          <h2 id="demo-title" className="text-2xl font-semibold tracking-tight">
            {t("demo.title")}
          </h2>
          <p className="mx-auto mt-2 max-w-xl text-ink-600 dark:text-ink-400">{t("demo.text")}</p>
          <div className="mt-5 flex justify-center gap-3">
            {shop === undefined ? null : (
              <a href={shop} className={button("accent", "small")}>
                {t("demo.visit")}
              </a>
            )}
            <Link href="/console" className={button("quiet", "small")}>
              {t("demo.console")}
            </Link>
          </div>
        </section>
      </main>

      <footer className="relative border-t border-ink-200 py-8 text-center text-xs leading-relaxed text-ink-600 dark:text-ink-400 dark:border-white/10">
        {t("footer")}
      </footer>
    </div>
  );
}
