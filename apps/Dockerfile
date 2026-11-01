# The two Next.js apps' container image (Phase 8): the web app (home page, verify page, console) or the demo shop,
# chosen with APP. Built from the repository's root:
#   docker build -f apps/Dockerfile --build-arg APP=web --build-arg NEXT_PUBLIC_DWARPAL_API_URL=https://api.example.org .
# Next.js writes NEXT_PUBLIC_ values into the code it builds, so the API's public address is given here, at build time.

FROM node:24.22.1-bookworm-slim AS build
ARG APP
ARG NEXT_PUBLIC_DWARPAL_API_URL
ENV NEXT_PUBLIC_DWARPAL_API_URL=$NEXT_PUBLIC_DWARPAL_API_URL NEXT_TELEMETRY_DISABLED=1
# pnpm, at the version the repository names (`packageManager` in package.json), through Node's own Corepack.
RUN corepack enable
WORKDIR /repo
COPY . .
# Exactly the lockfile's versions; then build the app and the workspace packages it uses (`...`).
RUN pnpm install --frozen-lockfile && pnpm --filter "@dwarpal/${APP}..." build
# Keep only what running needs: the app's production dependencies, its build, and its public files.
# (`deploy` copies the files Git tracks; the build and the generated public files — MediaPipe's — are copied after.)
RUN pnpm --filter "@dwarpal/${APP}" deploy --prod --legacy /out \
    && cp -r "apps/${APP}/.next" /out/.next \
    && rm -rf /out/.next/cache \
    && if [ -d "apps/${APP}/public" ]; then cp -r "apps/${APP}/public/." /out/public/; fi

FROM node:24.22.1-bookworm-slim
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
WORKDIR /app
COPY --from=build --chown=node:node /out /app
# Node's image comes with this unprivileged user.
USER node
EXPOSE 3000
CMD ["node", "node_modules/next/dist/bin/next", "start", "--port", "3000"]
