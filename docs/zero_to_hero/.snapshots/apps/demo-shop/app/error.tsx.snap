"use client";

import { quietButton } from "@/components/ui";

export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return (
    <section className="mx-auto mt-20 max-w-xl text-center">
      <h1 className="font-serif text-4xl">The age check couldn't start</h1>
      <p className="mt-5 text-lg leading-relaxed text-stone-300">
        Our age-check provider didn't answer. Please try again in a moment.
      </p>
      <button type="button" className={`${quietButton} mt-10`} onClick={reset}>
        Try again
      </button>
    </section>
  );
}
