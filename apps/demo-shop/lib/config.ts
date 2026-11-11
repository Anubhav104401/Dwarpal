import { DwarpalClient } from "@dwarpal/node";

/** The shop sells alcohol, so it checks 18+ under the UK Online Safety Act preset. */
export const POLICY = "uk_osa_18";
export const MIN_AGE = 18;

const PROJECT_ID = /^prj_[0-9A-Za-z]+$/;

export interface ShopConfig {
  apiUrl: string;
  issuer: string;
  apiKey: string;
  projectId: string;
  shopUrl: string;
  secret: string;
}

/** Read the shop's settings from the environment, and refuse to run with any of them missing. */
export function shopConfig(env: NodeJS.ProcessEnv = process.env): ShopConfig {
  const apiUrl = env.DWARPAL_API_URL ?? "http://localhost:8000";
  const config: ShopConfig = {
    apiUrl,
    issuer: env.DWARPAL_ISSUER ?? apiUrl,
    apiKey: env.DWARPAL_API_KEY ?? "",
    projectId: env.DWARPAL_PROJECT_ID ?? "",
    shopUrl: (env.SHOP_URL ?? "http://localhost:3100").replace(/\/+$/, ""),
    secret: env.SHOP_SECRET ?? "",
  };
  const missing = [
    config.apiKey === "" ? "DWARPAL_API_KEY" : null,
    // The ID as the console shows it, and as pass tokens name their audience (prj_…): a raw UUID, the database's form
    // of the same ID, would let every check pass and then refuse every visitor at the door.
    PROJECT_ID.test(config.projectId) ? null : "DWARPAL_PROJECT_ID (the console's prj_… form)",
    config.secret.length < 32 ? "SHOP_SECRET (at least 32 characters)" : null,
  ].filter((name) => name !== null);
  if (missing.length > 0) {
    throw new Error(`the demo shop is missing settings: ${missing.join(", ")}`);
  }
  return config;
}

export function dwarpal(config: ShopConfig): DwarpalClient {
  return new DwarpalClient({ apiKey: config.apiKey, baseUrl: config.apiUrl });
}
