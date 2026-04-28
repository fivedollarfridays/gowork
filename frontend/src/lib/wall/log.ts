/**
 * Structured logger (Spotlight invention).
 *
 * Single sink for diagnostic events. Pipes warn/error through
 * `lib/error-reporter.ts` so production telemetry captures both crashes
 * and diagnostic warnings via the SAME PII-scrubbed channel. Info/debug
 * are dev-only — tree-shakeable via NODE_ENV guard, so prod bundles never
 * carry the message strings.
 *
 * `withScope(name)` returns a child logger that prefixes every message
 * with `[gowork:scope]`, giving downstream filters a clean slice
 * (audio, hooks, mapbox, chapters, …).
 */

type LogArg = unknown;

interface LoggerLike {
  debug: (...args: LogArg[]) => void;
  info: (...args: LogArg[]) => void;
  warn: (...args: LogArg[]) => void;
  error: (...args: LogArg[]) => void;
  withScope: (scope: string) => LoggerLike;
}

function isDev(): boolean {
  return process.env.NODE_ENV !== "production";
}

function makeLogger(prefix: string): LoggerLike {
  return {
    debug(...args: LogArg[]): void {
      if (!isDev()) return;
      // eslint-disable-next-line no-console
      console.debug(prefix, ...args);
    },
    info(...args: LogArg[]): void {
      if (!isDev()) return;
      // eslint-disable-next-line no-console
      console.info(prefix, ...args);
    },
    warn(...args: LogArg[]): void {
      // eslint-disable-next-line no-console
      console.warn(prefix, ...args);
    },
    error(...args: LogArg[]): void {
      // eslint-disable-next-line no-console
      console.error(prefix, ...args);
    },
    withScope(scope: string): LoggerLike {
      return makeLogger(`[gowork:${scope}]`);
    },
  };
}

export const log: LoggerLike = makeLogger("[gowork]");
