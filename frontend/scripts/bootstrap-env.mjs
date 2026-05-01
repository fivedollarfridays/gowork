#!/usr/bin/env node
/**
 * Bootstrap `.env.local` from `.env.local.example` if missing.
 *
 * Why: Next.js reads `.env.local` (gitignored for safety) but NOT
 * `.env.local.example`. A fresh clone has the example but no
 * `.env.local`, so the Mapbox token + API URL are missing on first
 * `npm run dev` — the map renders the static fallback and the
 * assessment route can't reach the backend. This wired-via-postinstall
 * script copies the example over once at install time so the dev box
 * is ready out of the box.
 *
 * Idempotent: only runs the copy if `.env.local` is absent. Existing
 * `.env.local` files are NEVER overwritten — local edits the dev made
 * (custom API URL, EmailJS keys, etc.) survive subsequent installs.
 *
 * Silent on success — only logs when it actually copies. CI runs see
 * nothing because they typically have `.env.local` already injected
 * by the workflow, OR they don't need it at all (most tests mock).
 */
import { existsSync, copyFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FRONTEND_ROOT = resolve(__dirname, "..");
const EXAMPLE = resolve(FRONTEND_ROOT, ".env.local.example");
const TARGET = resolve(FRONTEND_ROOT, ".env.local");

if (process.env.CI === "true" || process.env.VERCEL === "1") {
  // CI / Vercel inject env vars via workflow secrets — `.env.local`
  // would silently override those at build time. Skip the bootstrap.
  process.exit(0);
}

if (existsSync(TARGET)) {
  // Local file already present — respect dev's edits and exit.
  process.exit(0);
}

if (!existsSync(EXAMPLE)) {
  // No example to copy from — most likely a partial checkout. Don't
  // crash npm install; just exit silently and let the dev sort it.
  process.exit(0);
}

copyFileSync(EXAMPLE, TARGET);
console.log(
  "[gowork] Bootstrapped frontend/.env.local from .env.local.example. " +
    "Edit the file directly if you need a custom API URL or your own Mapbox token.",
);
