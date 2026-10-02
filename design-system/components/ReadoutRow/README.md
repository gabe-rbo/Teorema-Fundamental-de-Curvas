A label on the left and a live value on the right, joined by a dotted `rule`. Labels are `ink-muted` sans with the symbol set in italic serif (*κ*, *τ*, *ρ*, *s*); values are `readout` mono in `ink`, right-aligned with tabular figures so columns do not jitter while the slider scrubs.

**Provide** a formatted string; the viewer decides precision (3 decimals for scalars, 2 for coordinates). Vector rows (`tf-vecrow`) lead with a FrameTag and show components in `ink-body`.

- Update the text node in place on every frame; do not re-render the row.
- A value that does not exist reads "—" (for example `ρ` where κ = 0); planar torsion reads "0.000 (plana)".
- Do not colour the values; hue is reserved for objects in the scene.
