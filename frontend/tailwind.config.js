/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0f19",
        card: "#131a2c",
        border: "#1e293b",
        accent: {
          purple: "#7c3aed",
          indigo: "#4f46e5",
          pink: "#db2777"
        },
        severity: {
          low: "#10b981",    // Emerald
          med: "#f59e0b",    // Amber
          high: "#ef4444"     // Rose
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
