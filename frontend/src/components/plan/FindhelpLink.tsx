import { ExternalLink } from "lucide-react";
import type { BarrierType } from "@/lib/types";
import { generateFindhelpUrl } from "@/lib/findhelp";

interface FindhelpLinkProps {
  barrierType: BarrierType;
  zipCode: string;
}

export function FindhelpLink({ barrierType, zipCode }: FindhelpLinkProps) {
  if (!zipCode) return null;

  const url = generateFindhelpUrl(barrierType, zipCode);
  if (!url) return null;

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline mt-2"
    >
      <ExternalLink className="h-3.5 w-3.5" />
      Find more programs on findhelp.org
    </a>
  );
}
