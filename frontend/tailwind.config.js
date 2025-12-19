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
        sans: ['Outfit', 'system-ui', 'sans-serif'],
      },
      colors: {
        cream: '#F8F6F1',
        clay: '#E8DCC4',
        terracotta: '#C17B5C',
        sage: '#8B9D83',
        moss: '#5B6B4D',
        charcoal: '#2D3136',
      },
    },
  },
  plugins: [],
}
