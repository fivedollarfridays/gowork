// Pure helpers for parsing Next.js build output and comparing per-route
// First Load JS sizes against a baseline. CLI driver lives in
// scripts/bundle-size-check.mjs (T13.87).

const ROUTE_LINE_RE =
  /^[│├└┌+ ]+\s*[ƒ○●λ]\s+(\S+)\s+(?:[\d.]+\s+(?:B|kB|MB))\s+([\d.]+)\s+(B|kB|MB)\s*$/;

// Routes that Next.js prints in the table but aren't actual user-facing
// pages we want to budget. _not-found is the catch-all 404, robots.txt /
// sitemap.xml are static text assets, not React routes.
const IGNORED_ROUTES = new Set([
  "/_not-found",
  "/robots.txt",
  "/sitemap.xml",
]);

function toKB(value, unit) {
  const v = Number(value);
  if (unit === "MB") return v * 1024;
  if (unit === "kB") return v;
  if (unit === "B") return v / 1024;
  return v;
}

export function parseBuildOutput(stdout) {
  const routes = {};
  for (const line of stdout.split("\n")) {
    const m = line.match(ROUTE_LINE_RE);
    if (!m) continue;
    const [, route, firstLoad, unit] = m;
    if (IGNORED_ROUTES.has(route)) continue;
    routes[route] = toKB(firstLoad, unit);
  }
  return routes;
}

export function compareToBaseline(current, baseline, thresholdPct) {
  const regressions = [];
  const missing = [];
  const unknown = [];

  for (const [route, base] of Object.entries(baseline)) {
    if (!(route in current)) {
      missing.push(route);
      continue;
    }
    if (base === 0) continue; // placeholder route — skip until baselined
    const cur = current[route];
    const deltaPct = ((cur - base) / base) * 100;
    if (deltaPct > thresholdPct) {
      regressions.push({ route, current: cur, baseline: base, deltaPct });
    }
  }
  for (const route of Object.keys(current)) {
    if (!(route in baseline)) unknown.push(route);
  }

  return {
    ok: regressions.length === 0,
    regressions,
    missing,
    unknown,
  };
}

function pad(s, n) {
  s = String(s);
  return s.length >= n ? s : s + " ".repeat(n - s.length);
}

export function formatReport(current, baseline, result, thresholdPct) {
  const lines = [];
  lines.push(
    `Bundle size check (threshold: +${thresholdPct}% per route, First Load JS):`,
  );
  lines.push("");
  lines.push(
    `  ${pad("Route", 32)} ${pad("Baseline", 10)} ${pad("Current", 10)} ${pad("Delta", 10)}`,
  );
  lines.push(`  ${"-".repeat(32)} ${"-".repeat(10)} ${"-".repeat(10)} ${"-".repeat(10)}`);
  const allRoutes = new Set([
    ...Object.keys(baseline),
    ...Object.keys(current),
  ]);
  for (const route of [...allRoutes].sort()) {
    const base = baseline[route];
    const cur = current[route];
    let delta = "";
    if (base !== undefined && cur !== undefined && base > 0) {
      const pct = ((cur - base) / base) * 100;
      const sign = pct >= 0 ? "+" : "";
      delta = `${sign}${pct.toFixed(1)}%`;
    } else if (base === undefined) {
      delta = "(new)";
    } else if (cur === undefined) {
      delta = "(missing)";
    } else if (base === 0) {
      delta = "(placeholder)";
    }
    lines.push(
      `  ${pad(route, 32)} ${pad(base ?? "-", 10)} ${pad(cur ?? "-", 10)} ${pad(delta, 10)}`,
    );
  }
  lines.push("");
  if (result.ok) {
    lines.push(`PASS - all routes within +${thresholdPct}% of baseline.`);
  } else {
    lines.push(`FAIL - ${result.regressions.length} route(s) regressed beyond +${thresholdPct}%:`);
    for (const r of result.regressions) {
      lines.push(
        `  - ${r.route}: ${r.baseline} kB -> ${r.current} kB (+${r.deltaPct.toFixed(1)}%)`,
      );
    }
  }
  if (result.missing.length > 0) {
    lines.push("");
    lines.push(`WARN - ${result.missing.length} baseline route(s) missing from build output:`);
    for (const r of result.missing) lines.push(`  - ${r}`);
  }
  if (result.unknown.length > 0) {
    lines.push("");
    lines.push(`INFO - ${result.unknown.length} new route(s) not yet in baseline:`);
    for (const r of result.unknown) lines.push(`  - ${r}`);
  }
  return lines.join("\n");
}
