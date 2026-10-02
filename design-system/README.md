Triedro is the interface of a scientific viewer for space and plane curves reconstructed from curvature κ(s) and torsion τ(s): one canvas, one sidebar of formulas and live quantities, one floating dock. Build every screen of it from the tokens, classes and rules below. Interface copy is Portuguese (pt-BR); documentation and code are English.

## Content fundamentals

- Write interface text in Portuguese, in short noun phrases: "Fórmulas intrínsecas", "Visibilidade do aparato", "Vetor normal N", "Plano osculador (T, N)". Labels never end with a period; hints are one sentence and do.
- Name mathematical objects as the textbooks do (do Carmo, Tenenblat): curvatura, torção, triedro de Frenet, círculo osculador, evoluta, involuta. Pair a name with its symbol, in that order: "Curvatura κ(s)".
- Symbols are typeset, never spelled: κ, τ, ρ, s, T, N, B in italic serif (`display` family) inside labels, in KaTeX inside formulas. Values are mono (`readout`).
- Address the user in the imperative and without "você": "Clique na curva ou arraste o controle."
- No emoji, no exclamation marks, no marketing language. A value that does not exist reads "—"; a planar torsion reads "0.000 (plana)".

## Visual foundations

**Surfaces.** The canvas is warm paper (`canvas`) in the light theme and midnight blue in the dark theme; the sidebar is `panel`, one step off the canvas. Light is the default. Both themes are first-class: set `data-theme="light"` or `"dark"` on `<html>` and nothing else changes.

**Color.** Chrome is neutral: `ink` for titles and values, `ink-body` for running text, `ink-muted` for labels (never below 11px), `edge` for any border that carries meaning, `rule` for decorative hairlines. The single interactive hue is `accent`, which is deliberately the hue of the curve itself. Every other hue is a semantic data hue and belongs to exactly one object: `curve`, `tangent`, `normal`, `binormal`, `point` (active point and osculating circle), `evolute`, `involute`. Never use a data hue for chrome, and never use two hues for one object.

**The Frenet set is color-vision safe.** T (green), N (vermilion) and B (reddish purple) differ in lightness and hue, and every one also carries a letter tag. Evolute is always dashed and involute always dotted so they are separated by form too. Planes are tinted with the hue of the vector they are perpendicular to: osculating plane `plane-osculating` (B), normal plane `plane-normal` (T), rectifying plane `plane-rectifying` (N).

**Type.** Three families: `display` (Fraunces) for the product title and for the italic symbols; `sans` (Instrument Sans) for labels and prose; `mono` (JetBrains Mono) for every live value. Section titles use `overline`: 11px, capitals, +0.08em, with an italic serif section sign in `accent` before them (§1, §2, …). Body copy is `body` (14/21) or `body-sm` (13/19). Load the three families from Google Fonts; `bundle.css` does it with one `@import`.

**Layout.** The canvas fills the viewport and nothing overlays the plot except the dock (bottom centre, 24px from the edge) and the legend (top left). The sidebar is `sidebar-width` (380px) on the right, collapsible. Spacing steps are `space-1` … `space-10` (4–40px); sidebar content is padded `space-5`, rows are `space-4` apart.

**Borders, shadows, radii.** Sidebar sections are separated by 1px `rule` hairlines, not boxes or shadows; only formula wells are boxed (`card`, `radius-sm`). Shadows exist for two layers only: `shadow-sidebar` and `shadow-dock`. Radii: `radius-xs` tags, `radius-sm` wells and icon buttons, `radius-md` panels, `radius-pill` for the dock, speed button, switch tracks and the slider rail.

**States.** Hover on a control tints it with `accent-soft` and moves its border and glyph to `accent`; pressed nudges it 1px down. Focus is a 2px solid `focus` ring with 2px offset, never removed; it holds 3:1 against canvas, panel and card in both themes. Disabled is 45% opacity with a not-allowed cursor.

**Motion.** 150ms `cubic-bezier(.4, 0, .2, 1)` for control state changes; 300ms for the sidebar slide. No decorative animation; the only moving thing is the curve's own playback. `prefers-reduced-motion` turns transitions off.

**Imagery.** None. The product is its plot: no photos, no illustrations, no gradients. 2D scenes may show a 28px dot grid in `plot-grid` behind the plot.

## Iconography

Icons are drawn inline as SVG on a 16px grid, 1.6px round strokes with `currentColor`, shown at 14px; transport glyphs (play, pause, first, prev, next, last) are solid fills. There is no icon font and no emoji (the previous interface used a moon emoji for the theme switch; draw a glyph instead). The product mark is the italic serif integral sign `∫` set as type in a 28px rounded square filled with `accent`; it is the repository's own glyph, so do not redraw it as a logo. See `assets/Plotly/` for the figure theme.

## Using the system

1. Include the compiled tokens, then `components/bundle.css`; add KaTeX 0.16.x (CSS and JS) for formulas.
2. Wrap the page in `.tf-root` and build with the `tf-*` classes documented per component: `ViewerShell` (page frame), `SidebarHeader`, `Panel`, `FormulaRow`, `ReadoutRow`, `Toggle`, `ControlDock`, `IconButton`, `Badge`, `FrameTag`.
3. Style the Plotly figure from `assets/Plotly/triedro-plotly-theme.json`, using the block of the active theme with transparent paper and plot backgrounds so `canvas` shows through; keep Plotly's native slider and updatemenus hidden, the dock is the only transport.
4. The viewer is generated by `curva_viz.py` as one HTML string with Python format fields: escape CSS braces as `{{` `}}` there, and keep element ids that the tests rely on (`hud-card`, `hud-s`, `hud-r`, `hud-kappa`, `hud-tau`, `hud-rho`).

## Not synced

This system is a redesign of the repository's viewer UI, not a transcription of it: the old palette (slate and Tailwind blue) was replaced, while object semantics, section structure, copy and element ids were kept. The components are plain HTML and CSS (the repository ships no component library), so there is no `bundle.js`, no React and no component props; consumers copy the markup and classes. Previews load Google Fonts and KaTeX from CDNs and show the TeX source until KaTeX loads. Not covered: the 3D scene chrome inside Plotly's WebGL canvas beyond the theme file, and mobile layout below 768px (collapse the sidebar and hide the dock's speed button).
