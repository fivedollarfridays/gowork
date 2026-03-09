import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockUseReducedMotion = vi.fn(() => false);
vi.mock("framer-motion", async () => {
  const actual = await vi.importActual("framer-motion");
  return { ...actual, useReducedMotion: () => mockUseReducedMotion() };
});

import {
  MotionProvider,
  ScrollReveal,
  StaggerContainer,
  StaggerItem,
  AnimatedCounter,
  Typewriter,
  SlideIn,
  ShimmerBar,
} from "../motion";

beforeEach(() => {
  mockUseReducedMotion.mockReturnValue(false);
});

describe("MotionProvider", () => {
  it("renders children", () => {
    render(
      <MotionProvider>
        <p>child content</p>
      </MotionProvider>,
    );
    expect(screen.getByText("child content")).toBeInTheDocument();
  });
});

describe("ScrollReveal", () => {
  it("renders children visible", () => {
    render(
      <MotionProvider>
        <ScrollReveal>
          <p>revealed</p>
        </ScrollReveal>
      </MotionProvider>,
    );
    expect(screen.getByText("revealed")).toBeInTheDocument();
  });

  it("with reduced motion renders children immediately", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { container } = render(
      <MotionProvider>
        <ScrollReveal>
          <p>static content</p>
        </ScrollReveal>
      </MotionProvider>,
    );
    expect(screen.getByText("static content")).toBeInTheDocument();
    // Should not have a framer-motion style attribute for animation
    const wrapper = container.querySelector("[style]");
    expect(wrapper).toBeNull();
  });
});

describe("StaggerContainer + StaggerItem", () => {
  it("renders children", () => {
    render(
      <MotionProvider>
        <StaggerContainer>
          <StaggerItem>
            <p>item one</p>
          </StaggerItem>
        </StaggerContainer>
      </MotionProvider>,
    );
    expect(screen.getByText("item one")).toBeInTheDocument();
  });

  it("with reduced motion renders children", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(
      <MotionProvider>
        <StaggerContainer>
          <StaggerItem>
            <p>static item</p>
          </StaggerItem>
        </StaggerContainer>
      </MotionProvider>,
    );
    expect(screen.getByText("static item")).toBeInTheDocument();
  });
});

describe("AnimatedCounter", () => {
  it("renders the target value with reduced motion", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(
      <MotionProvider>
        <AnimatedCounter from={0} to={42} prefix="$" suffix="k" />
      </MotionProvider>,
    );
    expect(screen.getByText("$42k")).toBeInTheDocument();
  });

  it("renders with motion enabled", () => {
    render(
      <MotionProvider>
        <AnimatedCounter from={0} to={100} />
      </MotionProvider>,
    );
    // The spring starts at 0, so the element should be present
    const el = screen.getByText((_content, element) => {
      return element?.tagName === "SPAN" && element?.textContent !== undefined;
    });
    expect(el).toBeInTheDocument();
  });
});

describe("Typewriter", () => {
  it("renders complete text with reduced motion", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(
      <MotionProvider>
        <Typewriter text="hello world" />
      </MotionProvider>,
    );
    expect(screen.getByText("hello world")).toBeInTheDocument();
  });

  it("renders text content when motion enabled", () => {
    render(
      <MotionProvider>
        <Typewriter text="animated text" />
      </MotionProvider>,
    );
    expect(screen.getByText(/animated/)).toBeInTheDocument();
  });
});

describe("SlideIn", () => {
  it("renders children", () => {
    render(
      <MotionProvider>
        <SlideIn>
          <p>sliding content</p>
        </SlideIn>
      </MotionProvider>,
    );
    expect(screen.getByText("sliding content")).toBeInTheDocument();
  });

  it("with reduced motion renders children", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(
      <MotionProvider>
        <SlideIn>
          <p>static slide</p>
        </SlideIn>
      </MotionProvider>,
    );
    expect(screen.getByText("static slide")).toBeInTheDocument();
  });
});

describe("ShimmerBar", () => {
  it("renders with correct dimensions", () => {
    const { container } = render(
      <MotionProvider>
        <ShimmerBar width="200px" height="1.5rem" />
      </MotionProvider>,
    );
    const bar = container.firstElementChild as HTMLElement;
    expect(bar).toBeInTheDocument();
    expect(bar.style.width).toBe("200px");
    expect(bar.style.height).toBe("1.5rem");
  });

  it("with reduced motion renders static bar", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { container } = render(
      <MotionProvider>
        <ShimmerBar width="100px" height="1rem" />
      </MotionProvider>,
    );
    const bar = container.firstElementChild as HTMLElement;
    expect(bar).toBeInTheDocument();
    // Should not contain animated inner div
    expect(bar.querySelector("[style*='translateX']")).toBeNull();
  });
});
