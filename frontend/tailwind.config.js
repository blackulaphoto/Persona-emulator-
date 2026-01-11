/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Crimson Pro', 'Georgia', 'serif'],
        sans: ['Outfit', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
        mono: ['SF Mono', 'Monaco', 'Menlo', 'monospace'],
      },
      colors: {
        // Splash page palette (avoid arbitrary hex classes)
        'splash-bg-1': '#0F1115',
        'splash-bg-2': '#1F2632',
        'splash-bg-3': '#101216',
        'splash-bg-4': '#0c0d0f',
        'splash-card': '#14161B',
        'splash-accent': '#6366F1',
        'splash-text': '#C7D2FE',

        // EXACT PALETTE - Warm & Earthy
        // Backgrounds
        'apple-bg': {
          primary: '#4a3242',      // RGB 74, 50, 66 - Matterhorn (dark)
          secondary: '#f6f4e2',    // RGB 246, 244, 226 - Beige (cards)
          tertiary: '#f2f8f9',     // RGB 242, 248, 249 - Catskill White (main bg)
          card: '#f6f4e2',         // RGB 246, 244, 226 - Beige
        },

        // Primary action color - Copperfield
        'apple-blue': {
          50: '#fef8f5',
          100: '#fdeee6',
          200: '#fbd4c8',
          300: '#f7b6a1',
          400: '#ec9f7d',
          500: '#d58d65',          // RGB 213, 141, 101 - Copperfield (primary)
          600: '#c17856',
          700: '#a46448',
          800: '#87523d',
          900: '#6f4434',
        },

        // Accent colors from exact palette
        'apple-teal': '#5AC8FA',
        'apple-purple': '#AF52DE',
        'apple-pink': '#FF2D55',
        'apple-green': '#34C759',
        'apple-orange': '#f0d2af',  // RGB 240, 210, 175 - Pancho
        'apple-red': '#c75e56',     // RGB 199, 94, 86 - Fuzzy Wuzzy Brown

        // Text colors
        'apple-text': {
          primary: '#4a3242',      // RGB 74, 50, 66 - Matterhorn
          secondary: '#7a6572',    // Lighter Matterhorn
          tertiary: '#a69099',     // Even lighter
          inverse: '#f2f8f9',      // RGB 242, 248, 249 - Catskill White
        },

        // Borders
        'apple-border': {
          light: 'rgba(74, 50, 66, 0.1)',
          DEFAULT: 'rgba(74, 50, 66, 0.2)',
          dark: 'rgba(74, 50, 66, 0.3)',
        },
      },

      boxShadow: {
        // Apple-style soft shadows
        'apple-sm': '0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06)',
        'apple-md': '0 4px 16px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04)',
        'apple-lg': '0 12px 40px rgba(0, 0, 0, 0.12), 0 4px 8px rgba(0, 0, 0, 0.06)',
        'apple-xl': '0 20px 60px rgba(0, 0, 0, 0.16), 0 8px 16px rgba(0, 0, 0, 0.08)',
        'apple-blue': '0 4px 12px rgba(0, 122, 255, 0.3)',
        'apple-blue-lg': '0 6px 20px rgba(0, 122, 255, 0.4)',
      },

      borderRadius: {
        'apple': '12px',      // Standard Apple radius
        'apple-lg': '16px',   // Cards
        'apple-xl': '20px',   // Large cards
      },

      backdropBlur: {
        'apple': '20px',
      },
    },
  },
  plugins: [],
}
