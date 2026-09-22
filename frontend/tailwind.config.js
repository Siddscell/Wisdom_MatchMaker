/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#f2f4f1',
        surface: '#ffffff',
        ink: '#000000',
        muted: '#545b56',
        line: '#dfe4df',
        forest: '#0a3324',
        mint: '#cfeedd',
        accent: { DEFAULT: '#16734f', strong: '#0d4f36', soft: '#e2f3e8' },
        band: { strong: '#16734f', good: '#4d9a74', fair: '#a8772a' },
        danger: '#a33a2b',
      },
      fontFamily: {
        display: ['"Instrument Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        sans: ['"Instrument Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      maxWidth: { page: '76rem' },
      borderRadius: { panel: '1.75rem' },
    },
  },
  plugins: [],
};
