The whole viewer page: a canvas that fills the viewport left of a 380px sidebar (`sidebar-width`), with the control dock floating at the bottom centre of the canvas and a legend at its top-left. Nothing else overlays the plot.

**Provide** the Plotly graph div (transparent paper and plot backgrounds, so `canvas` shows through), the sidebar sections, and the dock. Set `data-theme` on `<html>`; light is the default, and the choice is remembered by the consumer.

- Canvas: `canvas`, with a 28px dot grid in `plot-grid` behind 2D scenes. Sidebar: `panel`, a 1px `rule` on its left edge and `shadow-sidebar`.
- Sidebar order: header, §1 intrinsic formulas, §2 reconstruction and associated curves, §3 live quantities, §4 apparatus visibility, §5 theory. Collapsing slides it out in 300ms (`cubic-bezier(.4,0,.2,1)`) and shows the expand button at the top-right.
- Planar curves use an isotropic 1:1 view; objects keep the hues in the Plotly theme asset: curve `curve`, tangent `tangent`, normal `normal`, osculating circle and active point `point`, evolute `evolute` dashed, involute `involute` dotted.
- The mock above is a clothoid with κ(s) = s at s = 2: the evolute and the osculating circle (ρ = 0.5) are computed, not drawn by hand.
