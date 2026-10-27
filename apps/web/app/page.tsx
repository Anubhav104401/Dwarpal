import { card, Shell } from "@/components/shell";

export default function Home() {
  return (
    <Shell>
      <section className={card}>
        <h1 className="text-2xl font-semibold tracking-tight">Private age checks</h1>
        <p className="mt-3 leading-relaxed text-ink-600 dark:text-ink-400">
          Websites send you here when they need to know you are old enough. A few photos from your camera are
          checked once by an AI and then deleted. The website learns only one thing: whether you passed.
        </p>
        <p className="mt-4 leading-relaxed text-ink-600 dark:text-ink-400">
          To take an age check, open the link the website gave you.
        </p>
      </section>
    </Shell>
  );
}
