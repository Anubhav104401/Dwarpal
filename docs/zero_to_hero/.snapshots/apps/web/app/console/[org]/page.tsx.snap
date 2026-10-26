import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { OrganisationView } from "./organisation-view";

export const metadata: Metadata = { title: "Organisation · Dwarpal console" };

const ORGANISATION_ID = /^org_[0-9A-Za-z]{26}$/;

export default async function OrganisationPage({ params }: { params: Promise<{ org: string }> }) {
  const { org } = await params;
  if (!ORGANISATION_ID.test(org)) {
    notFound();
  }
  return <OrganisationView org={org} />;
}
