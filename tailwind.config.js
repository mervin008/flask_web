/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.{html,js}"], 
  theme: {
    extend: {
      fontFamily: {
        'sans': ['Roboto', 'sans-serif'], 
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ],
}