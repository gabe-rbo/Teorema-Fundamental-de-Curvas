A boxed well (`card` fill, 1px `rule`, `radius-sm`) with a title and a frame tag on one line, the KaTeX formula under it, and an optional one-line description.

**Provide** the TeX source and, if useful, a description in `ink-muted`; the consumer loads KaTeX (0.16.x, CSS and JS) and renders the node. Until KaTeX loads the node shows the TeX source in mono, so keep the source readable.

- The title is a Portuguese noun phrase; the tag is the object's letter (see FrameTag), the only coloured element in the row. No left-border accent stripe.
- Formula colour is `ink`; the well scrolls horizontally rather than wrapping a formula.
- Description text is `ink-muted` at 12px and may contain inline TeX.
