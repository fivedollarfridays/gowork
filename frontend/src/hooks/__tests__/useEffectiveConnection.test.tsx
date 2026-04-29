/**
 * polish-2 T58 — useEffectiveConnection tests.
 *
 * Verifies the hook reads `navigator.connection.effectiveType` and maps:
 *   - "slow-2g" / "2g"   → "slow"
 *   - "3g" / "4g"        → "fast"
 *   - undefined / API absent → "unknown"
 *
 * Driver E owns the helper; Driver A consumes it inside ChapterRailTooltip
 * to skip WebP on slow connections.
 */
import React from "react";
import { describe, it, expect, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";
import { useEffectiveConnection } from "../useEffectiveConnection";

interface MockConnection {
  effectiveType?: string;
  addEventListener?: (type: string, fn: () => void) => void;
  removeEventListener?: (type: string, fn: () => void) => void;
}

function setNavigatorConnection(conn: MockConnection | undefined) {
  Object.defineProperty(navigator, "connection", {
    value: conn,
    configurable: true,
    writable: true,
  });
}

afterEach(() => {
  cleanup();
  setNavigatorConnection(undefined);
});

function Probe({ onValue }: { onValue: (v: string) => void }): null {
  const v = useEffectiveConnection();
  React.useEffect(() => {
    onValue(v);
  }, [v, onValue]);
  return null;
}

describe("useEffectiveConnection (polish-2 T58)", () => {
  it("returns 'unknown' when navigator.connection is missing", () => {
    setNavigatorConnection(undefined);
    let value = "";
    render(<Probe onValue={(v) => (value = v)} />);
    expect(value).toBe("unknown");
  });

  it("returns 'slow' for slow-2g", () => {
    setNavigatorConnection({ effectiveType: "slow-2g" });
    let value = "";
    render(<Probe onValue={(v) => (value = v)} />);
    expect(value).toBe("slow");
  });

  it("returns 'slow' for 2g", () => {
    setNavigatorConnection({ effectiveType: "2g" });
    let value = "";
    render(<Probe onValue={(v) => (value = v)} />);
    expect(value).toBe("slow");
  });

  it("returns 'fast' for 4g", () => {
    setNavigatorConnection({ effectiveType: "4g" });
    let value = "";
    render(<Probe onValue={(v) => (value = v)} />);
    expect(value).toBe("fast");
  });

  it("returns 'fast' for 3g", () => {
    setNavigatorConnection({ effectiveType: "3g" });
    let value = "";
    render(<Probe onValue={(v) => (value = v)} />);
    expect(value).toBe("fast");
  });

  it("returns 'unknown' when effectiveType is an unrecognized string", () => {
    setNavigatorConnection({ effectiveType: "5g-future" });
    let value = "";
    render(<Probe onValue={(v) => (value = v)} />);
    expect(value).toBe("unknown");
  });
});
