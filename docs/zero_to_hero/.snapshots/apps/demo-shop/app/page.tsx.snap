import { cookies } from "next/headers";
import Link from "next/link";

import { button } from "@/components/ui";
import { MIN_AGE, shopConfig } from "@/lib/config";
import { PASS_COOKIE, readPass } from "@/lib/pass";

import { AgeCheckButton } from "./age-check-button";

export default async function Entrance() {
  const pass = readPass((await cookies()).get(PASS_COOKIE)?.value, shopConfig().secret);
  return (
    <section className="mx-auto mt-16 max-w-2xl text-center sm:mt-24">
      <p className="text-sm uppercase tracking-[0.3em] text-wine-300">Independent growers · since 2026</p>
      <h1 className="mt-5 font-serif text-5xl leading-tight sm:text-6xl">Wines worth the wait.</h1>
      <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-stone-300">
        Small-batch bottles from the slopes of the Deccan. Because we sell alcohol, everyone confirms they are{" "}
        {MIN_AGE} or over before entering the cellar.
      </p>
      <div className="mt-10">
        {pass === null ? (
          <AgeCheckButton>Verify my age to enter</AgeCheckButton>
        ) : (
          <Link href="/cellar" className={button}>
            Enter the cellar
          </Link>
        )}
      </div>
      <p className="mx-auto mt-8 max-w-md text-sm leading-relaxed text-stone-500">
        Age checks by Dwarpal: a few photos are checked once and never stored. We only learn whether you are
        old enough — never your age, your face or your name.
      </p>
    </section>
  );
}
