A full-width row that shows or hides one object of the scene: a 10px dot in the object's data hue, its Portuguese name, and a 34×20 switch on the right. The whole row is the hit area; the checkbox underneath carries state and the accessible name.

**Provide** a name, the dot hue class (`tf-dot--t`, `--n`, `--b`, `--p`, `--e`, `--i`, or none for the curve) and a change handler that sets the Plotly trace's visibility.

- On: the track fills with `accent`, the knob is `on-accent`. Off: the track is `card` with an `edge` ring and an `edge` knob, so state reads by position and fill, not colour alone.
- The dot must match the object's hue in the scene, tag and legend.
- Planar curves omit the B, binormal-plane and rectifying-plane rows rather than disabling them.
