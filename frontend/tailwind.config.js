/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Clash Display"', 'system-ui', 'sans-serif'],
      },
      colors: {
        fs: {
          black: '#09090b',
          dark: '#0f0f11',
          panel: '#141416',
          card: '#1a1a1e',
          elevated: '#232328',
          border: '#2e2e35',
          muted: '#71717a',
          text: '#e4e4e7',
          accent: '#d4d4d8',
          highlight: '#fafafa',
        },
      },
      boxShadow: {
        glow: '0 0 24px rgba(255, 255, 255, 0.04)',
        card: '0 4px 24px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [],
}
