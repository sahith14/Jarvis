/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {
    animation: { 'pulse-slow': 'pulse 3s infinite', 'glow': 'glow 2s ease-in-out infinite' },
    keyframes: { glow: { '0%,100%': { boxShadow: '0 0 20px #0ea5e9' }, '50%': { boxShadow: '0 0 40px #3b82f6' } } }
  }},
  plugins: [],
}
