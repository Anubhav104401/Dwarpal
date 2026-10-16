import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { Bottle } from "@/components/ui";
import { shopConfig } from "@/lib/config";
import { PASS_COOKIE, readPass } from "@/lib/pass";

const WINES = [
  {
    name: "Kesari Ridge",
    grape: "Shiraz 2022",
    notes: "Black plum, clove and a whisper of smoke.",
    price: "₹2,400",
    colour: "#5b1424",
  },
  {
    name: "Monsoon Bloom",
    grape: "Chenin Blanc 2024",
    notes: "Green apple, honeysuckle; bright and dry.",
    price: "₹1,450",
    colour: "#c9b15a",
  },
  {
    name: "Deccan Dusk",
    grape: "Cabernet Sauvignon 2021",
    notes: "Cassis, cedar and firm, ripe tannins.",
    price: "₹3,100",
    colour: "#3d0d1a",
  },
  {
    name: "Amber Hour",
    grape: "Skin-contact Viognier 2023",
    notes: "Apricot, black tea, a gently grippy finish.",
    price: "₹2,050",
    colour: "#c77a2b",
  },
];

export default async function Cellar() {
  const pass = readPass((await cookies()).get(PASS_COOKIE)?.value, shopConfig().secret);
  if (pass === null) {
    redirect("/");
  }
  const until = pass.expiresAt.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  });
  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-4xl">The cellar</h1>
          <p className="mt-2 text-stone-400">Four bottles we are proud of this season.</p>
        </div>
        <p className="rounded-full bg-emerald-500/15 px-4 py-1.5 text-sm text-emerald-300" role="status">
          Age verified · valid until {until} UTC
        </p>
      </div>
      <ul className="mt-10 grid gap-6 sm:grid-cols-2">
        {WINES.map((wine) => (
          <li
            key={wine.name}
            className="flex items-center gap-6 rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur"
          >
            <Bottle colour={wine.colour} label={wine.name.split(" ")[0] ?? wine.name} />
            <div>
              <h2 className="font-serif text-2xl">{wine.name}</h2>
              <p className="text-sm text-wine-300">{wine.grape}</p>
              <p className="mt-3 text-stone-300">{wine.notes}</p>
              <p className="mt-4 font-medium text-amber-glow">{wine.price}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
