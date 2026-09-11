import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#F6F7F9",
        surface: "#FFFFFF",
        ink: {
          900: "#161B22",
          700: "#2B3341",
          500: "#5B6472",
          300: "#8B93A1",
        },
        border: {
          DEFAULT: "#E3E6EB",
          strong: "#CBD1DA",
        },
        brand: {
          50: "#EEF2F7",
          100: "#D8E1EC",
          400: "#345170",
          600: "#1E3A5F",
          700: "#16293F",
          900: "#0E1B2C",
        },
        status: {
          verified: "#15803D",
          verifiedBg: "#EAF5EE",
          pending: "#B45309",
          pendingBg: "#FCF1E1",
          rejected: "#B91C1C",
          rejectedBg: "#FBEAEA",
          review: "#3B5B84",
          reviewBg: "#EAF0F7",
        },
      },
      fontFamily: {
        sans: [
          "var(--font-inter)",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 1px 2px rgba(22, 27, 34, 0.04), 0 1px 0 rgba(22, 27, 34, 0.03)",
        raised: "0 4px 16px rgba(22, 27, 34, 0.08)",
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        md: "8px",
        lg: "10px",
      },
    },
  },
  plugins: [],
};

export default config;
