/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"IBM Plex Sans"', "system-ui", "-apple-system", "sans-serif"],
        mono: ['"IBM Plex Mono"', '"Cascadia Code"', "Consolas", "monospace"],
      },
      colors: {
        brand: {
          DEFAULT: "#009EE3",
          dark: "#0085C4",
          deeper: "#006FA3",
          muted: "rgba(0, 158, 227, 0.10)",
          glow: "rgba(0, 158, 227, 0.20)",
          border: "rgba(0, 158, 227, 0.30)",
        },
        primary: {
          50: "#e6f5fc",
          100: "#ccebfa",
          200: "#99d7f5",
          300: "#66c3ef",
          400: "#33afea",
          500: "#009EE3",
          600: "#009EE3",
          700: "#0085C4",
          800: "#006FA3",
          900: "#005882",
          950: "#003D5C",
        },
        surface: {
          DEFAULT: "#FFFFFF",
          up: "#F5F8FB",
          raised: "#FFFFFF",
          bg: "#EDF1F6",
        },
        dark: {
          bg: "#0A0C0F",
          surface: "#131720",
          elevated: "#1C2333",
          border: "rgba(255, 255, 255, 0.07)",
          "border-strong": "rgba(255, 255, 255, 0.14)",
        },
        inotec: {
          text: "#1A2535",
          body: "#374151",
          muted: "#6B7280",
          subtle: "#9CA3AF",
          success: "#00A550",
          warning: "#D97706",
          danger: "#DC2626",
          info: "#3B82F6",
        },
      },
      borderRadius: {
        sm: "3px",
        DEFAULT: "6px",
        md: "6px",
        lg: "10px",
      },
      boxShadow: {
        xs: "0 1px 2px rgba(0,0,0,0.05)",
        sm: "0 2px 8px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        md: "0 4px 16px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)",
        lg: "0 8px 32px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06)",
        xl: "0 20px 60px rgba(0,0,0,0.14), 0 4px 16px rgba(0,0,0,0.08)",
        brand: "0 4px 16px rgba(0, 158, 227, 0.28)",
      },
    },
  },
  plugins: [],
};
