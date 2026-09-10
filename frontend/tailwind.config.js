/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Token-backed names — single source of truth is tokens.css.
        canvas: "var(--color-canvas)",
        paper: "var(--color-paper)",
        "paper-2": "var(--color-paper-2)",
        "paper-3": "var(--color-paper-3)",
        rule: "var(--color-rule)",
        "rule-2": "var(--color-rule-2)",
        muted: "var(--color-muted)",
        neutral: "var(--color-neutral)",
        "ink-2": "var(--color-ink-2)",
        ink: "var(--color-ink)",
        accent: "var(--color-accent)",
        "accent-ink": "var(--color-accent-ink)",
        "accent-text": "var(--color-accent-text)",
        graphite: "var(--color-graphite)",
        "graphite-ink": "var(--color-graphite-ink)",
        ok: "var(--color-ok-text)",
        warn: "var(--color-warn-text)",
        danger: "var(--color-danger-text)",

        // `brand` = the indigo family from the dashboard brief (accent #4f46e5,
        // interactive #6366f1). Pages not yet hand-tuned pick this up for free;
        // the blue→indigo→violet gradient (var(--gradient-brand)) carries the rest.
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "Segoe UI", "Roboto", "Arial", "sans-serif"],
        display: ["Space Grotesk", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SF Mono", "Segoe UI Mono", "Menlo", "monospace"],
      },
      borderRadius: {
        DEFAULT: "8px",
        sm: "6px",
        md: "8px",
        lg: "10px",
        xl: "14px",
        "2xl": "16px",
      },
      boxShadow: {
        sm: "var(--shadow-card)",
        DEFAULT: "var(--shadow-card)",
        md: "var(--shadow-pop)",
        lg: "var(--shadow-pop)",
      },
    },
  },
  plugins: [],
};
