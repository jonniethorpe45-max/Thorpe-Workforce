/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        thorpe: {
          primary: "#2563EB",
          50: "#EFF6FF",
          100: "#DBEAFE",
          200: "#BFDBFE",
          300: "#93C5FD",
          400: "#60A5FA",
          500: "#3B82F6",
          600: "#2563EB",
          700: "#1D4ED8",
          800: "#1E40AF",
          900: "#1E3A8A",
          950: "#172554",
        },
        navy: {
          DEFAULT: "#0B1220",
          light: "#111B2E",
          mid: "#1A2438",
          border: "#1E3A5F",
        },
        steel: "#64748B",
        cyber: {
          DEFAULT: "#06B6D4",
          teal: "#06B6D4",
        },
        success: "#22C55E",
        warning: "#F59E0B",
        surface: {
          DEFAULT: "#0B1220",
          raised: "#111B2E",
          overlay: "#1A2438",
          border: "#1E3A5F",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Sora", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #0B1220 0%, #111B2E 50%, #0B1220 100%)",
        "hero-glow":
          "radial-gradient(ellipse 80% 60% at 50% -20%, rgba(37, 99, 235, 0.18), transparent)",
      },
      boxShadow: {
        brand: "0 4px 24px rgba(37, 99, 235, 0.15)",
        card: "0 4px 24px rgba(0, 0, 0, 0.35)",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-in": "slideIn 0.3s ease-out",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
      },
    },
  },
  plugins: [],
};
