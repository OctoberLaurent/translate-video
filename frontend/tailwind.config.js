/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        notion: {
          bg: '#FFFFFF',
          sidebar: '#F7F6F3',
          hover: '#F1F1EF',
          border: '#E8E7E4',
          text: '#37352F',
          'text-secondary': '#787774',
          blue: '#2383E2',
          'blue-hover': '#1B6EC2',
          'blue-bg': '#E8F0FE',
          red: '#EB5757',
          green: '#4DAB6F',
        }
      },
      borderRadius: {
        'notion': '8px',
      },
      boxShadow: {
        'notion': 'rgba(15, 15, 15, 0.05) 0px 0px 0px 1px, rgba(15, 15, 15, 0.1) 0px 3px 6px',
        'notion-hover': 'rgba(15, 15, 15, 0.05) 0px 0px 0px 1px, rgba(15, 15, 15, 0.15) 0px 5px 10px, rgba(15, 15, 15, 0.1) 0px 1px 3px',
      }
    },
  },
  plugins: [],
}