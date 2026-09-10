/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
        },
        ink: {
          900: "#0f172a",
          700: "#334155",
          500: "#64748b",
        },
        accent: {
          600: "#2563eb",
          700: "#1d4ed8",
        },
        status: {
          healthy: "#16a34a",
          warning: "#d97706",
          critical: "#dc2626",
          offline: "#64748b",
        },
      },
    },
  },
  plugins: [],
};
