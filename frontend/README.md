# Vanguard Fitness — frontend

React 19 + Vite, Tailwind CSS v4, React Router, Lucide icons and Recharts.

## Running it

```bash
npm install
npm run dev      # http://localhost:5173
```

The dev server proxies `/api` to `http://127.0.0.1:8000`, so start the backend
first (see `../backend/README.md`). Point it elsewhere with
`VITE_API_PROXY_TARGET`, or bypass the proxy entirely with `VITE_API_BASE_URL`.

```bash
npm run build    # production bundle into dist/
npm run preview  # serve the built bundle
npm run lint
```

## Layout

```
src/
  components/   Layout (responsive nav), charts, hazard cards, UI primitives
  context/      AuthContext — JWT session, restore on load, 401 auto-logout
  hooks/        useDebounced, useReducedMotion
  lib/          api.js (fetch wrapper), macros.js (scaling + formatting)
  pages/        Dashboard, MacroTracker, Exercise*, Ped*, Calculators, Profile, Login
```

Routes are code-split with `React.lazy`, so Recharts (~400 kB) only downloads
for the pages that actually draw charts.

## Chart colours

The series palette in `src/index.css` is not chosen by eye. It is the validated
dark-surface categorical set, checked against the `#121821` chart surface for
lightness band, chroma floor, colour-blind separation, normal-vision separation
and 3:1 contrast. Changing a series colour means re-validating the set — and
identity is never carried by colour alone: every chart has a legend or direct
labels, and the progress bars are labelled with real numbers.

Recharts animates in JavaScript and ignores the CSS `prefers-reduced-motion`
rule, so `useReducedMotion` turns chart animation off explicitly.

## Hazard cards

`components/HazardCards.jsx` renders the cardiovascular, endocrine and hepatic
risk cards on every compound page. They are not collapsible and not dismissible.
Contrast is measured, not estimated: body text sits at 12.7:1, card headings at
10.0:1, and the card border at 5.1:1 against the page.
