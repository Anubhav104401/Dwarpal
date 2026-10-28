import type { Metadata } from "next";

import { ModelView } from "./model-view";

export const metadata: Metadata = { title: "Age model · Dwarpal console" };

export default function ModelPage() {
  return <ModelView />;
}
