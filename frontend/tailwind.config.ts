import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{ts,tsx}",
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        agro: {
          primary: "#1B5E20", // Verde Floresta
          leaf: "#8BC34A", // Verde Folha
          moss: "#415A3F" // Verde Musgo
        },
        escrow: {
          primary: "#0D47A1", // Azul Oceano
          light: "#03A9F4" // Azul Escrow
        },
        alert: {
          pending: "#FBC02D", // Amarelo
          critical: "#F57C00" // Laranja
        },
        surface: {
          neutral: "#F0F4F0"
        }
      },
      borderRadius: {
        "agro-button": "14px",
        "agro-card": "32px"
      },
      boxShadow: {
        "card-soft": "0 10px 30px rgba(0,0,0,0.05)",
        "bevel": "0 4px 0 rgba(0,0,0,0.18)"
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"]
      }
    }
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")]
};

export default config;
