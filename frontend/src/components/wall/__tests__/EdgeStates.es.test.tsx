/**
 * W4 Driver B — T4.B.5/6/7/8 edge-state Spanish parity.
 *
 * 404, 500, empty, and loading edge components all consume keys from
 * the `edge.*` i18n namespace. The W1 driver locked their EN copy and
 * left ES coverage thin. This test pins the ES contract for each edge
 * state by mounting under `setLocale("es")` and asserting the
 * Spanish-language copy renders.
 *
 * 404 + 500 page-level tests already exist (`not-found.test.tsx`,
 * `error.test.tsx`); this file deliberately re-asserts them in
 * Spanish so a future driver who tweaks `edge.404.title` cannot ship
 * a regression that only the EN-only tests would have caught.
 */
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import NotFound from "@/app/not-found";
import ErrorPage from "@/app/error";
import { EmptyState } from "../EmptyState";
import { LoadingState } from "../LoadingState";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("W4 — 404 page in Spanish (T4.B.5)", () => {
  beforeEach(() => setLocale("es"));
  afterEach(() => setLocale("en"));

  it("renders the wall-metaphor 404 title in Spanish", () => {
    wrap(<NotFound />);
    expect(
      screen.getByRole("heading", { name: /no hay un camino/i }),
    ).toBeInTheDocument();
  });

  it("CTA reads 'Volver al muro' in Spanish", () => {
    wrap(<NotFound />);
    expect(
      screen.getByRole("link", { name: /volver al muro/i }),
    ).toBeInTheDocument();
  });

  it("body copy mentions 'barrera' (Spanish for barrier)", () => {
    wrap(<NotFound />);
    expect(screen.getByText(/barrera/i)).toBeInTheDocument();
  });
});

describe("W4 — 500 page in Spanish (T4.B.6)", () => {
  beforeEach(() => setLocale("es"));
  afterEach(() => setLocale("en"));

  it("renders the 'Algo se detuvo' title in Spanish", () => {
    wrap(
      <ErrorPage
        error={new Error("hidden") as Error & { digest?: string }}
        reset={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("heading", { name: /algo se detuvo/i }),
    ).toBeInTheDocument();
  });

  it("CTA reads 'Intentar de nuevo' in Spanish", () => {
    wrap(
      <ErrorPage
        error={new Error("hidden") as Error & { digest?: string }}
        reset={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: /intentar de nuevo/i }),
    ).toBeInTheDocument();
  });

  it("body copy mentions 'recalibrando' or 'registrada' (Spanish wall metaphor)", () => {
    wrap(
      <ErrorPage
        error={new Error("hidden") as Error & { digest?: string }}
        reset={vi.fn()}
      />,
    );
    const body = screen.getByText(/recalibrando|registrada/i);
    expect(body).toBeInTheDocument();
  });

  it("does NOT leak error.message in Spanish either", () => {
    const SECRET = "PII_SECRET_TOKEN_xyz_42_DO_NOT_LEAK";
    const { container } = wrap(
      <ErrorPage
        error={new Error(SECRET) as Error & { digest?: string }}
        reset={vi.fn()}
      />,
    );
    expect(container.textContent ?? "").not.toContain(SECRET);
  });
});

describe("W4 — EmptyState in Spanish (T4.B.7)", () => {
  beforeEach(() => setLocale("es"));
  afterEach(() => setLocale("en"));

  it("renders Spanish title 'Aún no hay nada que trazar'", () => {
    wrap(<EmptyState />);
    expect(
      screen.getByText(/aún no hay nada que trazar/i),
    ).toBeInTheDocument();
  });

  it("renders Spanish body about data and the path", () => {
    wrap(<EmptyState />);
    expect(screen.getByText(/datos|camino/i)).toBeInTheDocument();
  });

  it("respects custom Spanish overrides", () => {
    wrap(<EmptyState title="Sin citas" body="Programa una para empezar" />);
    expect(screen.getByText("Sin citas")).toBeInTheDocument();
    expect(screen.getByText("Programa una para empezar")).toBeInTheDocument();
  });
});

describe("W4 — LoadingState in Spanish (T4.B.8)", () => {
  beforeEach(() => setLocale("es"));
  afterEach(() => setLocale("en"));

  it("renders the Spanish branded label 'Calibrando el camino'", () => {
    wrap(<LoadingState />);
    expect(screen.getByText(/calibrando el camino/i)).toBeInTheDocument();
  });

  it("preserves the aria-busy contract in Spanish", () => {
    wrap(<LoadingState />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
  });

  it("does NOT render a spinner element in Spanish either", () => {
    const { container } = wrap(<LoadingState />);
    expect(container.querySelector('[role="progressbar"]')).toBeNull();
  });
});
