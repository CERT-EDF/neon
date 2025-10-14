/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  darkMode: 'selector',
  theme: {
    extend: {},
  },
  plugins: [require('tailwindcss-primeui'), require('@tailwindcss/typography')],
};
