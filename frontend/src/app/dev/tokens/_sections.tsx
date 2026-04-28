/**
 * Generic TokenSection rendering helper for /dev/tokens.
 * Extracted to a sibling file to keep page.tsx under arch limits.
 */
import type { ReactNode } from "react";

export interface TokenSectionProps<T> {
  title: string;
  items: T[];
  renderRow: (item: T, idx: number) => ReactNode;
}

export function TokenSection<T>({
  title,
  items,
  renderRow,
}: TokenSectionProps<T>): JSX.Element {
  return (
    <section className="mb-8">
      <h2 className="mb-3 text-xl font-bold">{title}</h2>
      <ul className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item, idx) => (
          <li
            key={idx}
            className="rounded border border-foreground/10 bg-background/50 p-3"
          >
            {renderRow(item, idx)}
          </li>
        ))}
      </ul>
    </section>
  );
}
