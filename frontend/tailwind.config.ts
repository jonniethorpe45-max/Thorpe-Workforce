import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
    "./services/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#0f172a",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8"
        },
        accent: {
          cyan: "#22d3ee",
          indigo: "#6366f1"
        }
      }
    }
  },
  plugins: []
};

export default config;
