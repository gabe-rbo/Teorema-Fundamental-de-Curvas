The only floating control: a pill (`radius-pill`, `dock-glass` over a blur, `shadow-dock`) centred 24px above the canvas bottom, holding transport buttons, the arc-length scrubber, the `s` readout and a speed button.

**Provide** the frame count (slider max), `s0`/`s1` for the readout, and handlers for first/prev/play/next/last and speed (cycle 0.5×, 1×, 2×, 4×). The consumer mirrors slider value to the `.tf-fill` width and to the `s` readout.

- Play is the single filled `accent` control (42px); the other buttons are 34px circles with an `edge` ring.
- The scrubber is a 4px rail with an `accent` fill, a 16px thumb with a `canvas` gap ring, and nine small ticks under it; its accessible name is "Comprimento de arco s".
- Readout: italic serif *s*, the value in `accent`, the maximum in `ink-muted`. No percentage.
- It must stay at least 24px clear of the canvas edge and never cover the plot centre; on narrow screens hide the speed button first, then the ticks.
- The Plotly slider and updatemenus stay hidden; this dock is the only transport.
