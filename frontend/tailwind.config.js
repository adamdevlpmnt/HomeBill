/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--color-bg)",
        surface: {
          DEFAULT: "var(--color-surface)",
          elevated: "var(--color-surface-elevated)",
        },
        border: "var(--color-border)",
        text: {
          primary: "var(--color-text-primary)",
          secondary: "var(--color-text-secondary)",
        },
        energy: {
          elec: "var(--color-elec)",
          gas: "var(--color-gas)",
          water: "var(--color-water)",
        },
        status: {
          success: "var(--color-success)",
          warning: "var(--color-warning)",
          danger: "var(--color-danger)",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Inter",
          "SF Pro Text",
          "SF Pro Display",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      boxShadow: {
        soft: "0 4px 20px -2px rgba(0, 0, 0, 0.25)",
        card: "0 2px 8px 0 rgba(0, 0, 0, 0.15)",
        floating: "0 8px 30px rgba(0, 0, 0, 0.35)",
      },
      screens: {
        xs: "375px",
        mobile: "390px",
      },
      spacing: {
        "safe-top": "env(safe-area-inset-top, 0px)",
        "safe-bottom": "env(safe-area-inset-bottom, 0px)",
        "safe-left": "env(safe-area-inset-left, 0px)",
        "safe-right": "env(safe-area-inset-right, 0px)",
      },
    },
  },
  plugins: [],
};
