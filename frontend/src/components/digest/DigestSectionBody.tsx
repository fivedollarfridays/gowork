"use client";

/**
 * Renders a plaintext digest section body as simple paragraphs/list items.
 *
 * The backend emits text in a consistent shape: header-line followed by
 * bullet lines starting with "- ". We render this as a mix of <p> and <ul>
 * blocks to preserve structure without HTML sanitization risk.
 */
interface DigestSectionBodyProps {
  body: string;
  emptyPlaceholder: string;
}

type Block =
  | { kind: "para"; text: string }
  | { kind: "list"; items: string[] };

function toBlocks(body: string): Block[] {
  const lines = body.split("\n");
  const out: Block[] = [];
  let currentList: string[] | null = null;
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      if (currentList) {
        out.push({ kind: "list", items: currentList });
        currentList = null;
      }
      continue;
    }
    const listMatch = line.match(/^\s*-\s+(.*)$/);
    if (listMatch) {
      currentList ??= [];
      currentList.push(listMatch[1]);
    } else {
      if (currentList) {
        out.push({ kind: "list", items: currentList });
        currentList = null;
      }
      out.push({ kind: "para", text: line });
    }
  }
  if (currentList) out.push({ kind: "list", items: currentList });
  return out;
}

export function DigestSectionBody({ body, emptyPlaceholder }: DigestSectionBodyProps) {
  const trimmed = body.trim();
  if (!trimmed) {
    return <p className="text-muted-foreground italic">{emptyPlaceholder}</p>;
  }
  const blocks = toBlocks(trimmed);
  return (
    <div className="space-y-2">
      {blocks.map((block, idx) =>
        block.kind === "para" ? (
          <p key={idx} className="text-foreground">
            {block.text}
          </p>
        ) : (
          <ul key={idx} className="list-disc space-y-1 pl-5">
            {block.items.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        ),
      )}
    </div>
  );
}
