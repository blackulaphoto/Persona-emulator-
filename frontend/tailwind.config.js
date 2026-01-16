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
        // Empathetic Modernism Typography
        display: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
        body: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
        serif: ['Plus Jakarta Sans', 'Georgia', 'serif'], // Override for display
        mono: ['SF Mono', 'Consolas', 'Monaco', 'monospace'],
      },
      colors: {
        // PRIMARY PURPLE PALETTE - Trust & Wisdom
        'deep-purple': '#6B46C1',
        'soft-purple': '#9F7AEA',
        'lavender': '#D6BCFA',
        'periwinkle': '#B794F4',

        // SUPPORTING COLORS - Emotional States
        'sage-green': '#9AE6B4',
        'muted-coral': '#FC8181',
        'warm-rose': '#FBB6CE',

        // NEUTRALS - Canvas & Text
        'warm-cream': '#FEFCF9',
        'soft-gray': '#E2E8F0',
        'light-gray': '#F7FAFC',
        'slate': '#4A5568',
        'charcoal': '#2D3748',

        // SEMANTIC MAPPINGS
        growth: '#9AE6B4',      // Sage green
        challenge: '#FC8181',    // Muted coral
        'neutral-event': '#B794F4', // Periwinkle

        // THEME TOKENS
        background: '#FEFCF9',   // Warm cream
        foreground: '#2D3748',   // Charcoal
        card: '#FFFFFF',
        'card-foreground': '#2D3748',
        popover: '#FFFFFF',
        'popover-foreground': '#2D3748',
        primary: '#6B46C1',      // Deep purple
        'primary-foreground': '#FFFFFF',
        secondary: '#D6BCFA',    // Lavender
        'secondary-foreground': '#2D3748',
        muted: '#E2E8F0',        // Soft gray
        'muted-foreground': '#4A5568', // Slate
        accent: '#D6BCFA',       // Lavender
        'accent-foreground': '#2D3748',
        destructive: '#E53E3E',
        'destructive-foreground': '#FFFFFF',
        border: '#E2E8F0',       // Soft gray
        input: '#E2E8F0',
        ring: '#6B46C1',         // Deep purple
      },

      boxShadow: {
        // Purple-tinted shadows for brand consistency
        sm: '0 1px 2px 0 rgba(107, 70, 193, 0.05)',
        DEFAULT: '0 4px 6px -1px rgba(107, 70, 193, 0.1), 0 2px 4px -1px rgba(107, 70, 193, 0.06)',
        md: '0 4px 6px -1px rgba(107, 70, 193, 0.1), 0 2px 4px -1px rgba(107, 70, 193, 0.06)',
        lg: '0 10px 15px -3px rgba(107, 70, 193, 0.1), 0 4px 6px -2px rgba(107, 70, 193, 0.05)',
        xl: '0 20px 25px -5px rgba(107, 70, 193, 0.1), 0 10px 10px -5px rgba(107, 70, 193, 0.04)',
        '2xl': '0 25px 50px -12px rgba(107, 70, 193, 0.12)',
        purple: '0 4px 14px rgba(107, 70, 193, 0.2)',
        'purple-lg': '0 8px 24px rgba(107, 70, 193, 0.25)',
      },

      borderRadius: {
        sm: '0.375rem',      // 6px
        DEFAULT: '0.5rem',   // 8px
        md: '0.5rem',        // 8px
        lg: '0.75rem',       // 12px
        xl: '1rem',          // 16px
        '2xl': '1.5rem',     // 24px
        full: '9999px',
      },

      spacing: {
        xs: '0.25rem',       // 4px
        sm: '0.5rem',        // 8px
        md: '1rem',          // 16px
        lg: '1.5rem',        // 24px
        xl: '2rem',          // 32px
        '2xl': '3rem',       // 48px
        '3xl': '4rem',       // 64px
      },

      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in-up': 'fadeInUp 0.4s ease-out',
      },

      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%': { transform: 'translateX(-20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
