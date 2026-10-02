"""Generate the example gallery: one interactive viewer per curve plus an index page.

Run from the repository root:  python3 exemplos/gerar_galeria.py
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import curva_engine  # noqa: E402
import curva_viz  # noqa: E402

OUT = Path(__file__).resolve().parent

# slug, display name, kappa(s), tau(s), s0, s1, note
CURVES: list[tuple[str, str, str, str, float, float, str]] = [
    # ---- planar: tau = 0 ---------------------------------------------------------
    ("rosacea_cinco_petalas", "Rosácea de cinco pétalas", "2+2*cos(5*s)", "0", 0, 12.5, "κ oscila entre 0 e 4: laços e pontos de inflexão."),
    ("cardioide_curvatura", "Curvatura de cardioide", "1+cos(s)", "0", 0, 25.1, "κ toca zero a cada período: a curva respira entre laços."),
    ("espiral_exponencial", "Espiral exponencial", "exp(s/3)", "0", 0, 6, "A curvatura cresce exponencialmente: enrola cada vez mais apertado."),
    ("espiral_raiz", "Espiral de raiz", "sqrt(1+s)", "0", 0, 20, "κ = √(1+s): uma espiral entre a clotoide e o círculo."),
    ("clotoide_deslocada", "Clotoide deslocada", "0.5+s", "0", 0, 6, "κ = 0,5 + s: integrais de Fresnel com parâmetro de deslocamento."),
    ("pulso_gaussiano", "Pulso gaussiano", "3*exp(-(s-4)**2)+0.2", "0", 0, 8, "Quase reta, curva-se bruscamente em s = 4 e volta."),
    ("batimento_planar", "Batimento", "1+sin(s)*cos(3*s)", "0", 0, 20, "Dois harmônicos em batimento: caminho entrelaçado."),
    ("transicao_tanh", "Transição suave", "1+tanh(s-5)", "0", 0, 10, "Reta quase reta que sofre curvatura 2 depois de s = 5, em transição suave."),
    ("espiral_inversa", "Espiral inversa", "1/(1+s**2)", "0", 0, 30, "κ decai como 1/(1+s²): espiral que se abre devagar."),
    ("laco_seno_quadrado", "Laços de sen²", "0.3+3*sin(s)**2", "0", 0, 18, "κ ≥ 0,3 com picos de 3,3: laços regulares."),
    # ---- spatial -----------------------------------------------------------------
    ("helice_conica", "Hélice cônica", "2*exp(-s/6)", "2", 0, 20, "κ decai com τ constante: a hélice afina em cone."),
    ("helice_torcao_linear", "Torção linear", "1", "s/2", 0, 14, "τ cresce linearmente: o plano osculador gira cada vez mais depressa."),
    ("torcao_oscilante", "Torção oscilante", "1.5", "3*sin(s)", 0, 20, "O sentido da hélice se inverte a cada meio período."),
    ("mola_modulada", "Mola modulada", "1+0.5*sin(s)", "0.5+cos(2*s)", 0, 25, "κ e τ oscilam em frequências 1 e 2: mola com pulsação."),
    ("transicao_destrogira", "Destrógira para levógira", "1.5", "3*tanh(s-8)", 0, 16, "τ muda de −3 a +3: uma hélice vira a hélice oposta."),
    ("batimento_espacial", "Batimento espacial", "2+sin(3*s)", "1+0.5*cos(5*s)", 0, 14, "κ e τ com frequências incomensuráveis: curva nunca se repete."),
    ("lancret_raiz", "Hélice de Lancret", "sqrt(1+s)", "2*sqrt(1+s)", 0, 14, "τ/κ = 2 constante: ângulo fixo com um eixo (teorema de Lancret)."),
    ("curvatura_alta_frequencia", "Curvatura de alta frequência", "3+2*sin(5*s)", "1", 0, 12, "κ oscila 5 vezes mais rápido que o giro: franjas na hélice."),
    ("modulo_seno", "Módulo do seno", "abs(sin(s))+0.4", "2*abs(cos(s))", 0, 18, "κ e τ nunca negativos e com cantos: segmentos de arco."),
    ("tangente_hiperbolica", "Torção que satura", "1+0.5*cos(s)", "2*tanh(s/3)", 0, 24, "τ → 2: a curva tende a uma hélice modulada."),
    ("torcao_composta", "Torção composta", "2", "sin(s)+sin(sqrt(2)*s)", 0, 30, "Soma de seno com √2·s: quase periódica."),
    ("curvatura_pulsante", "Curvatura pulsante", "1+sin(s)**2", "1+cos(s)**2", 0, 18, "Ambas oscilam com sen² e cos²: simetria de fase."),
    ("espiral_torcida", "Espiral torcida", "0.4+0.3*s", "1.5", 0, 12, "κ cresce linearmente com τ fixa: espiral que sobe enrolando."),
    ("rosa_espacial", "Rosa espacial", "2+2*cos(3*s)", "1+sin(2*s)", 0, 18, "A rosácea de três pétalas levantada pela torção."),
]


def _tex_free(expr: str) -> str:
    return html.escape(expr.replace("**", "^").replace("*", "·"))


def main() -> None:
    cards: list[str] = []
    failures: list[str] = []
    for slug, name, k, t, s0, s1, note in CURVES:
        try:
            res = curva_engine.reconstruct_curve(k, t, s0=s0, s1=s1, num_points=700)
            r = np.asarray(res.r)
            if not np.all(np.isfinite(r)):
                raise ValueError("non-finite trajectory")
            curva_viz.export_interactive_html(res, str(OUT / f"{slug}.html"), title=name)
        except Exception as exc:  # report and keep going
            failures.append(f"{slug}: {exc}")
            continue
        dim = "2D" if t.strip() == "0" else "3D"
        cards.append(
            f'<a class="card" href="{slug}.html"><div class="cardtop"><span class="tf-badge tf-badge--class">{res.classification.replace("_", " ")}</span>'
            f'<span class="tf-badge tf-badge--dim">{dim}</span></div><h2>{html.escape(name)}</h2>'
            f'<p class="fx">κ(s) = {_tex_free(k)}<br>τ(s) = {_tex_free(t)}<br><span>s ∈ [{s0:g}, {s1:g}]</span></p>'
            f"<p class=\"note\">{html.escape(note)}</p></a>"
        )
    tokens = curva_viz._read_design_asset("tokens.css")
    bundle = curva_viz._read_design_asset("components/bundle.css")
    page = f"""<!DOCTYPE html>
<html lang="pt-BR" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Triedro — Galeria de curvas</title>
<style>{bundle}</style><style>{tokens}</style>
<style>
body{{margin:0;background:var(--canvas);color:var(--ink-body);font-family:var(--font-sans)}}
header{{padding:var(--space-8) var(--space-8) var(--space-4);max-width:1200px;margin:0 auto}}
h1{{font-family:var(--font-display);font-weight:500;font-size:34px;color:var(--ink);margin:0 0 var(--space-2)}}
header p{{margin:0;color:var(--ink-muted);max-width:70ch}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:var(--space-4);padding:var(--space-4) var(--space-8) var(--space-10);max-width:1200px;margin:0 auto}}
.card{{display:flex;flex-direction:column;gap:var(--space-2);padding:var(--space-4);background:var(--card);border:1px solid var(--rule);border-radius:var(--radius-md);text-decoration:none;color:inherit;transition:border-color 150ms,background 150ms}}
.card:hover{{border-color:var(--accent);background:var(--accent-soft)}}
.card:focus-visible{{outline:2px solid var(--focus);outline-offset:2px}}
.cardtop{{display:flex;justify-content:space-between}}
.card h2{{margin:0;font-family:var(--font-display);font-weight:500;font-size:20px;color:var(--ink)}}
.fx{{margin:0;font-family:var(--font-mono);font-size:12px;line-height:18px;color:var(--ink)}}
.fx span{{color:var(--ink-muted)}}
.note{{margin:0;font-size:13px;line-height:19px;color:var(--ink-muted)}}
</style></head><body>
<header><h1>Galeria de curvas</h1>
<p>Cada curva foi reconstruída a partir de κ(s) e τ(s) pelo Teorema Fundamental das Curvas. Clique para abrir o visualizador.</p></header>
<main>{"".join(cards)}</main></body></html>"""
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"{len(cards)} curves written, {len(failures)} failed")
    for f in failures:
        print("FAILED", f)


if __name__ == "__main__":
    main()
