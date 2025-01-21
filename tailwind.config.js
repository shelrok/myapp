/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/backend/**/*.html",   // Путь к вашим HTML файлам
    "./app/backend/**/*.css",    // Путь к вашим CSS файлам, если в них используются Tailwind классы
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
