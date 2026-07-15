/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#07120f",
          900: "#0c1c17",
          800: "#142922",
          700: "#1c3a30",
        },
        moss: {
          400: "#6f9b7a",
          300: "#8fb69a",
        },
        signal: {
          DEFAULT: "#d6f26a",
          soft: "#e8f7a8",
          deep: "#a8c93a",
        },
        parchment: "#e8efe6",
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 60px rgba(214, 242, 106, 0.12)",
      },
      backgroundImage: {
        terrain:
          "radial-gradient(ellipse 80% 60% at 70% 20%, rgba(111,155,122,0.28), transparent 55%), radial-gradient(ellipse 50% 40% at 15% 80%, rgba(214,242,106,0.08), transparent 50%), linear-gradient(160deg, #07120f 0%, #0c1c17 45%, #142922 100%)",
      },
    },
  },
  plugins: [],
};
