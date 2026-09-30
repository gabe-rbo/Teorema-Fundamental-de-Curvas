#!/usr/bin/env python3
"""
CLI Entrypoint for the Fundamental Theorem of Curves (Teorema Fundamental de Curvas).

This tool reconstructs planar and space curves in R^3 given their curvature kappa(s)
and torsion tau(s) as functions of arc length s by integrating the Frenet-Serret
differential equations:
    T'(s) =  kappa(s) * N(s)
    N'(s) = -kappa(s) * T(s) + tau(s) * B(s)
    B'(s) =                   - tau(s) * N(s)
    r'(s) =  T(s)

The reconstructed curve is automatically classified and exported as a responsive,
full-screen interactive 3D visualization using Plotly with live Frenet apparatus,
scrubbable parameter slider, and click-to-point snapping.

Theoretical Foundations:
  - Toponogov, V. A. (2006). Differential Geometry of Curves and Surfaces. Birkhäuser.
  - Tenenblat, K. (2008). Introdução à Geometria Diferencial. Editora Blucher.
  - Alencar, H. & Santos, W. (2009). Geometria Diferencial: Curvas e Superfícies. SBM.
  - do Carmo, M. P. (2016). Differential Geometry of Curves and Surfaces. Dover.
  - Lancret, M. A. (1802). Mémoire sur les courbes à double courbure.

Usage Examples:
  # Circular Helix (kappa=1, tau=1)
  python3 teorema-fundamental-curvas.py "1" "1" -i 0 6.28

  # Plane Circle (kappa=1, tau=0 default)
  python3 teorema-fundamental-curvas.py "1" -i 0 6.28

  # Clothoid / Cornu Spiral (kappa=s, tau=0) with custom output
  python3 teorema-fundamental-curvas.py "s" "0" -i -5 5 -o clothoid.html

  # Using explicit flags
  python3 teorema-fundamental-curvas.py -k "1" -t "1" -i 0 10 -n 1000
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Ensure script directory is in sys.path for robust imports across all invocation contexts
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import sympy as sp
import curva_engine  # noqa: E402
import curva_viz  # noqa: E402


def _parse_interval_bound(val: str) -> float:
    """Safely parse an interval bound as float or symbolic constant (e.g., 'pi', '2*pi')."""
    try:
        f_val = float(val)
        if not (f_val == f_val and abs(f_val) != float("inf")):
            raise argparse.ArgumentTypeError(
                f"Valor de intervalo inválido '{val}': deve ser numérico finito."
            )
        return f_val
    except ValueError:
        pass

    try:
        parsed = curva_engine.parse_and_validate_expression(val)
        allowed_symbols = {sp.Symbol("pi"), sp.Symbol("e"), sp.Symbol("E")}
        if parsed.free_symbols - allowed_symbols:
            raise ValueError("Interval bounds must be constant expressions without free variables.")
        val_f = float(parsed.evalf())
        if not (val_f == val_f and abs(val_f) != float("inf")):  # finite check
            raise ValueError("Interval bound evaluated to non-finite value.")
        return val_f
    except Exception as e:
        raise argparse.ArgumentTypeError(
            f"Valor de intervalo inválido '{val}': deve ser numérico ou constante válida."
        ) from e



def build_argument_parser() -> argparse.ArgumentParser:
    """Build and configure the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="teorema-fundamental-curvas.py",
        description=(
            "Reconstrução e visualização interativa de curvas no R^3 a partir "
            "de sua curvatura κ(s) e torção τ(s) pelo Teorema Fundamental de Curvas."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Positional argument slots (optional to allow flag-only usage)
    parser.add_argument(
        "pos_curvatura",
        nargs="?",
        default=None,
        metavar="curvatura",
        help="Expressão para curvatura κ(s) em função de s (ou via -k/--curvatura).",
    )
    parser.add_argument(
        "pos_torcao",
        nargs="?",
        default=None,
        metavar="torcao",
        help="Expressão para torção τ(s) em função de s (padrão: '0', ou via -t/--torcao).",
    )

    # Flagged argument alternatives
    parser.add_argument(
        "-k",
        "--curvatura",
        dest="flag_curvatura",
        default=None,
        help="Expressão matemática para a curvatura κ(s).",
    )
    parser.add_argument(
        "-t",
        "--torcao",
        dest="flag_torcao",
        default=None,
        help="Expressão matemática para a torção τ(s) (padrão: '0').",
    )
    parser.add_argument(
        "-i",
        "--intervalo",
        nargs=2,
        type=_parse_interval_bound,
        default=[0.0, 6.28],
        metavar=("S0", "S1"),
        help="Intervalo de integração do comprimento de arco [s0, s1].",
    )
    parser.add_argument(
        "-n",
        "--num-pontos",
        type=int,
        default=500,
        metavar="N",
        help="Número de pontos de discretização ao longo da curva.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        metavar="ARQUIVO",
        help="Caminho do arquivo HTML de saída (se omitido, nome gerado automaticamente).",
    )

    return parser


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse and harmonize positional and flagged command-line arguments.

    Returns:
        argparse.Namespace containing resolved attributes:
          - curvatura (str)
          - torcao (str)
          - intervalo (list[float, float])
          - num_pontos (int)
          - output (str | None)
    """
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    # Collect positional arguments
    positionals = [p for p in (args.pos_curvatura, args.pos_torcao) if p is not None]

    # Resolve curvatura: flag takes precedence, then first positional
    curvatura = args.flag_curvatura
    if curvatura is None:
        if positionals:
            curvatura = positionals.pop(0)
        else:
            parser.error(
                "o argumento de curvatura κ(s) é obrigatório "
                "(forneça posicionalmente ou via -k/--curvatura)."
            )

    # Resolve torcao: flag takes precedence, then next positional, default to '0'
    torcao = args.flag_torcao
    if torcao is None:
        if positionals:
            torcao = positionals.pop(0)
        else:
            torcao = "0"

    # If extra unused positionals remain, trigger syntax error
    if positionals:
        parser.error(f"argumentos posicionais não reconhecidos: {' '.join(positionals)}")

    args.curvatura = curvatura
    args.torcao = torcao
    return args


def validate_consecutive_operators(expr: str, field_name: str = "expressão") -> str | None:
    """
    Validate that a mathematical expression does not contain consecutive operators
    such as '++' or '--' which violate standard algebraic syntax.

    Returns:
        str | None: Error message if consecutive operators are detected, else None.
    """
    if expr and re.search(r"(\+{2,}|-{2,}|\+\s*\+|-\s*-)", expr):
        return (
            f"Erro de sintaxe na expressão de {field_name} ('{expr}'): "
            "operadores consecutivos ('++' ou '--') não são permitidos."
        )
    return None


def run_pipeline(args: argparse.Namespace) -> int:
    """
    Execute the curve reconstruction and visualization pipeline.

    Returns:
        int: Exit status code (0 for success, 1 for math/validation errors).
    """
    # 0. Validation of expression syntax (reject consecutive operators ++ or --)
    for field_name, expr in (("curvatura", args.curvatura), ("torcao", args.torcao)):
        err = validate_consecutive_operators(expr, field_name)
        if err:
            sys.stderr.write(f"{err}\n")
            return 1

    s0, s1 = args.intervalo

    # 1. Validation of numerical arguments
    if s0 >= s1:
        sys.stderr.write(
            f"Erro de validação: início do intervalo s0 ({s0}) deve ser "
            f"estritamente menor que o fim s1 ({s1}).\n"
        )
        return 1

    if args.num_pontos < 2:
        sys.stderr.write(
            f"Erro de validação: o número de pontos ({args.num_pontos}) "
            "deve ser no mínimo 2.\n"
        )
        return 1

    # 2. Mathematical reconstruction & ODE integration
    try:
        curve_data = curva_engine.reconstruct_curve(
            kappa_expr_str=args.curvatura,
            tau_expr_str=args.torcao,
            s0=s0,
            s1=s1,
            num_points=args.num_pontos,
        )
    except (ValueError, ZeroDivisionError, RuntimeError, ArithmeticError) as exc:
        sys.stderr.write(f"Erro na reconstrução da curva: {exc}\n")
        return 1
    except Exception as exc:
        sys.stderr.write(f"Erro inesperado durante a integração: {exc}\n")
        return 1

    # 3. Determine output filename
    if args.output:
        output_filename = args.output
    else:
        output_filename = curva_engine.generate_output_filename(
            curve_class=curve_data.classification,
            kappa_str=args.curvatura,
            tau_str=args.torcao,
            s0=s0,
            s1=s1,
        )

    # 4. Generate and export interactive HTML visualization
    try:
        final_path = curva_viz.export_interactive_html(
            curve_data=curve_data,
            output_path=output_filename,
        )
    except Exception as exc:
        sys.stderr.write(f"Erro ao exportar visualização HTML: {exc}\n")
        return 1

    # 5. User-friendly summary report
    print("=" * 80)
    print("  TEOREMA FUNDAMENTAL DE CURVAS — RECONSTRUÇÃO FRENET-SERRET")
    print("=" * 80)
    print(f"  Classificação da Curva : {curve_data.classification}")
    print(f"  Curvatura κ(s)         : {args.curvatura}")
    print(f"  Torção τ(s)            : {args.torcao}")
    print(f"  Intervalo [s0, s1]     : [{s0:g}, {s1:g}]")
    print(f"  Pontos Discretizados   : {args.num_pontos}")
    print(f"  Arquivo HTML Gerado    : {final_path}")
    print("=" * 80)
    print(f"Visualização pronta! Abra '{final_path}' no seu navegador.")

    return 0


def main(argv: list[str] | None = None) -> None:
    """Main CLI entrypoint."""
    args = parse_arguments(argv)
    exit_code = run_pipeline(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
