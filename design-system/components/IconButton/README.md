Square 28px button with an 8px radius for sidebar-header actions (theme switch, collapse panel).

**Provide** an inline SVG (14px, `currentColor`, 1.6px round stroke) and an `aria-label`; the glyph is never the only name.

- Border is `edge` (3:1), fill `card`; on hover the fill becomes `accent-soft` and the border and glyph go to `accent` / `accent-hover`.
- Use it for actions that change the view. Playback belongs to the dock buttons, not here.
- Do not use emoji as glyphs (the old UI used a moon emoji); draw the glyph in the same stroke as the others.
- Focus: 2px `focus` ring with 2px offset, never removed.
