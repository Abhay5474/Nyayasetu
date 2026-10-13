/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '"Noto Sans Devanagari"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Fraunces', '"Noto Serif Devanagari"', 'ui-serif', 'Georgia', 'serif'],
        deva: ['"Noto Sans Devanagari"', 'Inter', 'sans-serif'],
      },
      colors: {
        ink: {
          50: '#f5f7fb', 100: '#e9edf6', 200: '#cfd7e8', 300: '#a5b2cf', 400: '#7787ae',
          500: '#556693', 600: '#415077', 700: '#34405f', 800: '#1f2943', 900: '#131b32', 950: '#0a1020',
        },
        saffron: {
          50: '#fff8eb', 100: '#ffedcc', 200: '#ffd88f', 300: '#ffc052', 400: '#ffa726',
          500: '#f98b0b', 600: '#dd6a06', 700: '#b74a09', 800: '#923a0e', 900: '#78310f',
        },
        paper: '#fbfaf7',
      },
      boxShadow: {
        soft: '0 1px 2px rgba(10,16,32,.04), 0 8px 24px -8px rgba(10,16,32,.10)',
        lift: '0 2px 4px rgba(10,16,32,.05), 0 18px 40px -12px rgba(10,16,32,.22)',
        glow: '0 0 0 1px rgba(249,139,11,.25), 0 12px 40px -10px rgba(249,139,11,.45)',
      },
      keyframes: {
        'fade-up': { '0%': { opacity: 0, transform: 'translateY(12px)' }, '100%': { opacity: 1, transform: 'translateY(0)' } },
        'fade-in': { '0%': { opacity: 0 }, '100%': { opacity: 1 } },
        shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
        float: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-8px)' } },
        'pulse-ring': { '0%': { transform: 'scale(.9)', opacity: 0.7 }, '100%': { transform: 'scale(1.6)', opacity: 0 } },
      },
      animation: {
        'fade-up': 'fade-up .6s cubic-bezier(.2,.7,.2,1) both',
        'fade-in': 'fade-in .4s ease both',
        shimmer: 'shimmer 2.2s linear infinite',
        float: 'float 6s ease-in-out infinite',
        'pulse-ring': 'pulse-ring 1.8s ease-out infinite',
      },
    },
  },
  plugins: [],
};
