/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    // W1 — resolve @import "./styles/tokens/*.css" partials into globals.css
    // BEFORE Tailwind processes @layer directives. Tailwind's PostCSS plugin
    // requires that every file containing `@layer base/components/utilities`
    // also contain `@tailwind base/components/utilities`; without postcss-import
    // it scans imports independently and fails with "@layer base is used but
    // no matching @tailwind base directive is present" at colors.css:40.
    "postcss-import": {},
    tailwindcss: {},
  },
};

export default config;
