import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ProjectView } from "./project-view";

export const metadata: Metadata = { title: "Project · Dwarpal console" };

const ORGANISATION_ID = /^org_[0-9A-Za-z]{26}$/;
const PROJECT_ID = /^prj_[0-9A-Za-z]{26}$/;

export default async function ProjectPage({ params }: { params: Promise<{ org: string; project: string }> }) {
  const { org, project } = await params;
  if (!ORGANISATION_ID.test(org) || !PROJECT_ID.test(project)) {
    notFound();
  }
  return <ProjectView org={org} project={project} />;
}
