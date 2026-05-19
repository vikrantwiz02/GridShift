/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        solar: "#f59e0b",
        wind: "#3b82f6",
        load: "#f97316",
        grid: "#6b7280",
        renewable: "#10b981",
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
