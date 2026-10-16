import Link from "next/link";

import { button, quietButton } from "@/components/ui";

import { startAgeCheck } from "../actions";

const FALLBACK = {
  title: "Something went wrong",
  body: "We couldn't complete the age check on our side. Please try again in a moment.",
};

const MESSAGES: Record<string, { title: string; body: string }> = {
  not_confirmed: {
    title: "We couldn't confirm your age",
    body: "The age check didn't confirm that you are 18 or over, so we can't let you into the cellar.",
  },
  step_up: {
    title: "A stronger check is needed",
    body: "Your photos were too close to call. Checking with an ID document is coming soon; until then, we can't let you in.",
  },
  other_browser: {
    title: "Please finish the check where you started it",
    body: "This age check was started in a different browser, or a long time ago. Start a new one here.",
  },
  unfinished: {
    title: "The age check wasn't finished",
    body: "It may have expired. You can start a new one whenever you are ready.",
  },
  error: FALLBACK,
};

export default async function Refused({ searchParams }: { searchParams: Promise<{ reason?: string }> }) {
  const { reason } = await searchParams;
  const message = MESSAGES[reason ?? ""] ?? FALLBACK;
  return (
    <section className="mx-auto mt-20 max-w-xl text-center">
      <h1 className="font-serif text-4xl">{message.title}</h1>
      <p className="mt-5 text-lg leading-relaxed text-stone-300">{message.body}</p>
      <div className="mt-10 flex flex-wrap justify-center gap-4">
        <form action={startAgeCheck}>
          <button type="submit" className={button}>
            Try the age check again
          </button>
        </form>
        <Link href="/" className={quietButton}>
          Back to the entrance
        </Link>
      </div>
    </section>
  );
}
