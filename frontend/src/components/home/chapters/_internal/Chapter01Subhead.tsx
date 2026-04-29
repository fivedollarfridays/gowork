"use client";

/**
 * Chapter 01 subhead — the seven-barrier paragraph with two bolded fragments.
 *
 * Translation key uses {{seven}} and {{system}} placeholders so EN/ES can
 * both bold the same logical fragments without re-encoding the whole
 * sentence. Split on placeholders, inject `<strong>` for each.
 */

export interface Chapter01SubheadProps {
  raw: string;
  seven: string;
  system: string;
}

export function Chapter01Subhead({ raw, seven, system }: Chapter01SubheadProps) {
  const [head, afterSeven] = raw.split("{{seven}}");
  const [middle, tail] = (afterSeven ?? "").split("{{system}}");
  return (
    <p
      className="ch01-sub"
      style={{
        position: "relative",
        zIndex: 2,
        maxWidth: "56rem",
        margin: "0 auto",
        fontSize: "clamp(1.05rem, 0.9rem + 0.5vw, 1.35rem)",
        lineHeight: 1.55,
        color: "var(--fg-secondary)",
        textAlign: "center",
        padding: "0 4vw",
      }}
    >
      {head}
      <strong style={{ color: "var(--fg-primary)", fontWeight: 600 }}>
        {seven}
      </strong>
      {middle}
      <strong style={{ color: "var(--fg-primary)", fontWeight: 600 }}>
        {system}
      </strong>
      {tail ?? ""}
    </p>
  );
}
