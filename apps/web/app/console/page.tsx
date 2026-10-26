import type { Metadata } from "next";

import { ConsoleHome } from "./console-home";

export const metadata: Metadata = { title: "Console · Dwarpal" };

export default function ConsolePage() {
  return <ConsoleHome />;
}
