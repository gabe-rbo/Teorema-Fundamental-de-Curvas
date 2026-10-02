`triedro-plotly-theme.json` styles the Plotly figure so it matches the sidebar and dock: one block per theme (`light`, `dark`) with the trace colours, widths and dashes, and the `layout` fragments (transparent backgrounds so `canvas` shows through, grid and axis lines, hover label, modebar).

Usage rules: read the block for the active theme and apply it with `fig.update_layout` and per-trace `line` / `marker` settings; on a theme switch, relayout the same fields from the other block rather than hard-coding colours. The 2D axis fragments (`xaxis_2d`, `yaxis_2d`) lock a 1:1 isotropic scale.

Hues are semantic and fixed per object: curve, tangent, normal, binormal, active point and osculating circle, evolute (always dashed), involute (always dotted). The three planes are tinted with the hue of the vector they are perpendicular to: osculating plane with the binormal hue, normal plane with the tangent hue, rectifying plane with the normal hue.

Single file, plain JSON; it contains no ink colour of its own, so it can be loaded directly into a `<script type="application/json">` tag by the generator.
