# ADR-0012: Next.js 16 + Tailwind 4 + shadcn/ui; pnpm + Turborepo monorepo

- **Status:** Accepted — 2026-10-15

## Context
The owner requires an exceptionally beautiful, modern front end. It covers four very different surfaces:

- the marketing site;
- the camera-driven verify flow;
- the data-heavy console;
- the demo shop.

These surfaces share a design system and SDKs.

## Decision
- **Framework:** Next.js 16 (App Router, React 19, Server Components, Turbopack), with TypeScript in strict mode.
- **Styling and components:**
    - Tailwind CSS 4 (CSS-first configuration, OKLCH colour tokens);
    - shadcn/ui components on accessible primitives;
    - a custom design system in `packages/ui`.
- **Motion:** Motion (formerly Framer Motion) for UI; GSAP and Lenis for scroll storytelling.
- **3D:** three.js with React Three Fiber and drei for the face-mesh hero. All motion respects `prefers-reduced-motion`.
- **Camera AI:** MediaPipe Tasks Vision in the verify flow.
- **Data and forms:** TanStack Query, Zod, React Hook Form; Recharts for the console's charts.
- **Internationalisation:** next-intl, with English and Hindi.
- **Repository:** a pnpm workspace plus Turborepo. Biome for linting and formatting.
- **Testing:** Vitest and Playwright, using Chromium's fake camera for end-to-end tests.

## Consequences
- **Good:** the largest ecosystem; first-class shadcn/ui support; server rendering for marketing and console; one design system across apps; deployable anywhere Node runs.
- **Cost:** Next.js is complex (Server versus Client components, caching semantics); the bundle needs care on the verify route (dynamic import of MediaPipe).

## Alternatives considered
SvelteKit 2 (excellent; smaller component ecosystem), React Router 7 framework mode, Nuxt 4 (Vue), Astro 5 (ideal for marketing only), SolidStart and TanStack Start (smaller ecosystems); ESLint + Prettier instead of Biome (slower, two tools).
