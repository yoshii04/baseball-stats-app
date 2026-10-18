/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        navy: {
          600: '#1a3a5c',
          700: '#122b47',
          800: '#0c1e32',
        },
      },
    },
  },
  plugins: [],
}
