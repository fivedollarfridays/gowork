"use client";

/**
 * Stylized SVG portrait for Chapter 03. Gradient (amber → rose → cyan) +
 * noise filter + dark silhouette ellipse + light highlight on the cheekbone.
 *
 * Pulled into its own file to keep Chapter03MeetCarlos.tsx under the per-file
 * function-count limit.
 */

interface CarlosPortraitSvgProps {
  alt: string;
}

export function CarlosPortraitSvg({ alt }: CarlosPortraitSvgProps) {
  return (
    <svg
      className="carlos-svg"
      viewBox="0 0 480 600"
      role="img"
      aria-label={alt}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    >
      <title>{alt}</title>
      <defs>
        <linearGradient id="cgrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.95" />
          <stop offset="50%" stopColor="#FB7185" stopOpacity="0.85" />
          <stop offset="100%" stopColor="#22D3EE" stopOpacity="0.75" />
        </linearGradient>
        <filter id="cnoise">
          <feTurbulence baseFrequency="0.9" numOctaves="2" seed="3" />
          <feColorMatrix values="0 0 0 0 0.96  0 0 0 0 0.94  0 0 0 0 0.92  0 0 0 0.06 0" />
        </filter>
      </defs>
      <rect x="0" y="0" width="480" height="600" fill="url(#cgrad)" />
      <rect x="0" y="0" width="480" height="600" filter="url(#cnoise)" />
      <g fill="rgba(10,14,26,0.78)">
        <ellipse cx="240" cy="220" rx="98" ry="118" />
        <path d="M 90 600 L 90 460 Q 90 350 240 350 Q 390 350 390 460 L 390 600 Z" />
      </g>
      <ellipse cx="200" cy="200" rx="50" ry="36" fill="rgba(245,235,210,0.18)" />
    </svg>
  );
}
