/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#f6f4ef',
        surface: '#ffffff',
        ink: '#1b1d1c',
        muted: '#5b5f5a',
        line: '#e2ded4',
        accent: { DEFAULT: '#1f6f54', strong: '#17563f', soft: '#e3efe8' },
        band: { strong: '#1f6f54', good: '#4f8a74', fair: '#a8772a' },
        danger: '#a33a2b',
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      maxWidth: { page: '72rem' },
    },
  },
  plugins: [],
};
