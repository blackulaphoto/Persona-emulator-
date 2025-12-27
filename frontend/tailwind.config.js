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
        // OLD THEME (keep for compatibility)
        cream: '#F8F6F1',
        clay: '#E8DCC4',
        terracotta: '#C17B5C',
        sage: '#8B9D83',
        moss: '#5B6B4D',
        charcoal: '#2D3136',

        // APPLE-INSPIRED THEME (new)
        // Backgrounds
        'apple-bg': {
          primary: '#1D1D1F',      // Deep almost-black (Apple dark)
          secondary: '#2C2C2E',    // Elevated surfaces
          tertiary: '#F5F5F7',     // Light background
          card: '#FFFFFF',         // White cards
        },

        // iOS System Blue (vibrant, not corporate)
        'apple-blue': {
          50: '#E5F2FF',
          100: '#CCE5FF',
          200: '#99CCFF',
          300: '#66B2FF',
          400: '#3399FF',
          500: '#007AFF',          // iOS system blue
          600: '#0051D5',
          700: '#0040AA',
          800: '#003080',
          900: '#002055',
        },

        // iOS System Colors
        'apple-teal': '#5AC8FA',
        'apple-purple': '#AF52DE',
        'apple-pink': '#FF2D55',
        'apple-green': '#34C759',
        'apple-orange': '#FF9500',
        'apple-red': '#FF3B30',

        // Text colors (high contrast)
        'apple-text': {
          primary: '#1D1D1F',      // Deep black
          secondary: '#86868B',    // Apple secondary gray
          tertiary: '#C7C7CC',     // Muted
          inverse: '#F5F5F7',      // Light on dark
        },

        // Borders
        'apple-border': {
          light: 'rgba(0, 0, 0, 0.1)',
          DEFAULT: 'rgba(0, 0, 0, 0.2)',
          dark: 'rgba(0, 0, 0, 0.3)',
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
