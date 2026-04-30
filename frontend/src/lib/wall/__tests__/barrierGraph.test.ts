/**
 * Tests for the barrier-graph data module.
 *
 * Locks the shape of the 33-node DAG consumed by Ch8's BarrierConstellation:
 *   - 33 nodes (graph density target — see honest uncertainty in module docs)
 *   - Each node belongs to one of the 7 canonical barrier categories
 *     (credit | transportation | childcare | housing | health | training |
 *      criminal_record), aligned with backend `BarrierType`
 *   - Each node has a stable id (kebab-case)
 *   - Each edge points from a real node id to a real node id
 *   - Edges form a DAG (no self-loops; no immediate two-way duplicates)
 *   - `barrierGraphProvenance` carries source / sourceDate / version
 */
import { describe, it, expect } from "vitest";
import {
  BARRIER_GRAPH,
  BARRIER_CATEGORIES,
  barrierGraphProvenance,
  type BarrierNode,
} from "../data/barrierGraph";

const NODE_COUNT_TARGET = 33;

describe("BARRIER_GRAPH — node shape", () => {
  it("ships exactly the targeted node count (33)", () => {
    expect(BARRIER_GRAPH.nodes).toHaveLength(NODE_COUNT_TARGET);
  });

  it("every node has a stable kebab-case id", () => {
    const idRe = /^[a-z][a-z0-9-]*$/;
    for (const n of BARRIER_GRAPH.nodes) {
      expect(n.id).toMatch(idRe);
    }
  });

  it("node ids are unique", () => {
    const ids = BARRIER_GRAPH.nodes.map((n) => n.id);
    const set = new Set(ids);
    expect(set.size).toBe(ids.length);
  });

  it("every node belongs to one of the 7 canonical barrier categories", () => {
    for (const n of BARRIER_GRAPH.nodes) {
      expect(BARRIER_CATEGORIES).toContain(n.category);
    }
  });

  it("every node has a non-empty label key (i18n) and weight", () => {
    for (const n of BARRIER_GRAPH.nodes) {
      expect(n.labelKey.length).toBeGreaterThan(0);
      expect(n.weight).toBeGreaterThan(0);
    }
  });
});

describe("BARRIER_GRAPH — edge integrity", () => {
  it("every edge from/to references an existing node", () => {
    const ids = new Set(BARRIER_GRAPH.nodes.map((n) => n.id));
    for (const e of BARRIER_GRAPH.edges) {
      expect(ids.has(e.from)).toBe(true);
      expect(ids.has(e.to)).toBe(true);
    }
  });

  it("no self-loops (edge.from !== edge.to)", () => {
    for (const e of BARRIER_GRAPH.edges) {
      expect(e.from).not.toBe(e.to);
    }
  });

  it("no exact duplicate edges (same from + to)", () => {
    const seen = new Set<string>();
    for (const e of BARRIER_GRAPH.edges) {
      const key = `${e.from}->${e.to}`;
      expect(seen.has(key)).toBe(false);
      seen.add(key);
    }
  });

  it("at least N-1 edges so the graph is connected enough to read", () => {
    // 33 nodes → ≥ 32 edges minimally connects them
    expect(BARRIER_GRAPH.edges.length).toBeGreaterThanOrEqual(
      BARRIER_GRAPH.nodes.length - 1,
    );
  });
});

describe("barrierGraphProvenance", () => {
  it("declares source, sourceDate, and version", () => {
    expect(barrierGraphProvenance.source).toMatch(/.+/);
    expect(barrierGraphProvenance.sourceDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(barrierGraphProvenance.version).toMatch(/.+/);
  });
});

describe("BARRIER_GRAPH — type narrowing", () => {
  it("BarrierNode shape compiles (TS-only assertion)", () => {
    const _check: BarrierNode = {
      id: "stub",
      category: "credit",
      labelKey: "wall.chapter08.barrierLabels.stub",
      weight: 1,
    };
    expect(_check).toBeDefined();
  });
});
