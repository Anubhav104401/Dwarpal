import type { Metadata } from "next";

import { AccountView } from "./account-view";

export const metadata: Metadata = { title: "Security · Dwarpal console" };

export default function AccountPage() {
  return <AccountView />;
}
