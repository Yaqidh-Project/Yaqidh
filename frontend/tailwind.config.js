/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          // The new vibrant navy shade
          500: '#06217e', 
          600: '#041656', // Darker shade for hover states
          50: '#f0f3fa',  // Light tint for background accents
        },
      },
    },
  },
  plugins: [],
}