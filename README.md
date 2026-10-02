# Teorema Fundamental de Curvas

> **Reconstrução de Curvas no $\mathbb{R}^3$ e $\mathbb{R}^2$, Integração de Frenet-Serret e Visualização Interativa**

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-013243.svg?logo=numpy)](https://numpy.org/)
[![SciPy](https://img.shields.io/badge/SciPy-1.10%2B-8CAAE6.svg?logo=scipy)](https://scipy.org/)
[![SymPy](https://img.shields.io/badge/SymPy-1.12%2B-3B5526.svg?logo=sympy)](https://www.sympy.org/)
[![Plotly](https://img.shields.io/badge/Plotly-5.15%2B-3F4F75.svg?logo=plotly)](https://plotly.com/)
[![Tests](https://img.shields.io/badge/Tests-262%20passed-success.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Ferramenta científica e educacional para reconstrução e exploração geométrica de curvas a partir de suas funções intrínsecas de **curvatura** $\kappa(s)$ e **torção** $\tau(s)$ parametrizadas pelo comprimento de arco $s$.

O projeto oferece **duas formas de uso complementares**:
1. **Aplicação Web Interativa (`index.html`)**: roda 100% no navegador, sem necessidade de instalar Python ou iniciar servidores.
2. **CLI em Python (`teorema-fundamental-curvas.py`)**: gera relatórios visuais autônomos em HTML interativo com Plotly e integração de alta ordem.

---

## Início Rápido

### Opção 1: No Navegador (Zero Instalação)
Basta abrir o arquivo [`index.html`](index.html) em qualquer navegador moderno.

- **Playground em tempo real:** digite expressões para $\kappa(s)$ e $\tau(s)$, ajuste parâmetros $a, b, c$ via sliders e navegue pelo comprimento de arco.
- **Galeria com 32 curvas:** inclui retas, círculos, hélices, nós toroidais, clotoides, espirais e curvas de transição com miniaturas interativas.
- **Motor JavaScript de alta precisão:** integração pelo método de Magnus de 4ª ordem (conservação exata no grupo de Lie $\mathrm{SO}(3)$) e canvas em duas camadas a 60 fps.

### Opção 2: Linha de Comando (CLI em Python)

```bash
# 1. Clonar repositório e preparar ambiente
git clone https://github.com/gabe-rbo/Teorema-Fundamental-de-Curvas.git
cd Teorema-Fundamental-de-Curvas
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Reconstruir uma curva plana (2D) - Exemplo: Círculo unitário
python3 teorema-fundamental-curvas.py "1" "0" -i 0 6.28

# 3. Reconstruir uma curva espacial (3D) - Exemplo: Hélice circular
python3 teorema-fundamental-curvas.py "1" "1" -i 0 12.56 -o helice.html
```

---

## Principais Recursos

- **Arquitetura Dual Inteligente:**
  - **Curvas Planas ($\tau \equiv 0$):** Reconstrução analítica por quadratura direta ($\theta(s) = \int \kappa\,du$ e $r(s) = \int (\cos\theta, \sin\theta)\,du$) em $< 1$ ms via regra de Simpson cumulativa com interpolação `CubicSpline`. Visualização puramente 2D cartesiana com aspecto isotrópico 1:1 (`scaleanchor="x", scaleratio=1`), impedindo deformação do círculo osculador.
  - **Curvas Espaciais ($\tau \not\equiv 0$):** Integração numérica do sistema de Frenet-Serret com `scipy.integrate.solve_ivp` (DOP853/RK45) e ortonormalização contínua de Gram-Schmidt no grupo $\mathrm{SO}(3)$. Renderização 3D WebGL completa com planos diferenciais semitransparentes e vetor de Darboux.
- **Interface e Controles Visuais:**
  - **Painel lateral retrátil (sidebar):** mantém o canvas do gráfico 100% desobstruído.
  - **Fórmulas matemáticas com KaTeX:** renderização tipográfica elegante de $\kappa(s)$, $\tau(s)$ e grandezas locais.
  - **Floating Dock:** barra flutuante no rodapé com play/pause contínuo, passo a passo e controle de velocidade.
  - **Temas Claro e Escuro:** alternância instantânea com um clique.
  - **Switches de visibilidade:** controle granular para exibir/ocultar triedro $\{T, N, B\}$, retas, planos e círculo osculador.
  - **Click-to-Point:** clique em qualquer ponto da curva para sincronizar métricas e o aparato instantaneamente.
- **Classificação Determinística:** detecção automática da curva entre 8 famílias geométricas conhecidas.
- **Segurança AST:** validação estrita de expressões matemáticas contra injeção de código arbitrário.

---

## Galeria das 8 Famílias Geométricas

O motor analisa $\kappa(s)$ e $\tau(s)$ para identificar a geometria intrínseca e gerar a visualização apropriada:

| Família | Curvatura $\kappa(s)$ | Torção $\tau(s)$ | Descrição Geométrica | Exemplo de Uso CLI |
|---|:---:|:---:|---|---|
| **Reta** | $\kappa \equiv 0$ | $\tau \equiv 0$ | Geodésica linear no $\mathbb{R}^3$ | `"0" "0"` |
| **Círculo** | $\kappa \equiv c > 0$ | $\tau \equiv 0$ | Circunferência plana de raio $R = 1/c$ | `"1" "0"` |
| **Hélice Circular** | $\kappa \equiv c_1 > 0$ | $\tau \equiv c_2 \neq 0$ | Hélice sobre cilindro reto | `"1" "1"` |
| **Hélice Cilíndrica** | $\kappa > 0$ | $\tau/\kappa \equiv c \neq 0$ | Hélice geral (**Teorema de Lancret**, 1802) | `"1 + 0.1*sin(s)" "2*(1 + 0.1*sin(s))"` |
| **Clotoide (Cornu)** | $\kappa(s) = c \cdot s$ | $\tau \equiv 0$ | Curva de transição com curvatura linear | `"s" "0"` |
| **Espiral Logarítmica** | $\kappa(s) = \frac{1}{as+b}$ | $\tau \equiv 0$ | Espiral equiangular plana | `"1/(s + 1)" "0"` |
| **Curva Plana Geral** | $\kappa(s)$ arbitrária | $\tau \equiv 0$ | Movimento restrito ao plano $\mathbb{R}^2$ | `"2 + sin(s)" "0"` |
| **Curva Espacial Geral** | $\kappa(s)$ arbitrária | $\tau \not\equiv 0$ | Curva tridimensional genérica | `"1 + 0.5*cos(s)" "0.5*s"` |

---

## Fundamentação Matemática Resumida

### Teorema Fundamental das Curvas

Dadas duas funções suaves $\kappa(s) > 0$ e $\tau(s)$ em $[s_0, s_1]$, **existe uma curva espacial** $r: [s_0, s_1] \to \mathbb{R}^3$ parametrizada pelo comprimento de arco cuja curvatura é $\kappa(s)$ e cuja torção é $\tau(s)$. Essa curva é **única a menos de movimento rígido** (isometria em $\mathrm{SE}(3)$).

Para curvas planas ($\tau \equiv 0$), a curvatura com sinal $\kappa(s)$ determina a curva de forma única a menos de isometria em $\mathrm{SE}(2)$, resolvida diretamente por duas quadraturas.

### Equações de Frenet-Serret

O triedro ortonormal móvel $\{T(s), N(s), B(s)\} \in \mathrm{SO}(3)$ evolui conforme:

$$\frac{dr}{ds} = T(s), \quad \frac{dT}{ds} = \kappa(s) N(s), \quad \frac{dN}{ds} = -\kappa(s) T(s) + \tau(s) B(s), \quad \frac{dB}{ds} = -\tau(s) N(s)$$

De forma equivalente, a rotação instantânea do triedro é dada pelo **Vetor de Darboux** $\omega(s) = \tau(s) T(s) + \kappa(s) B(s)$, tal que $\frac{dF_i}{ds} = \omega(s) \times F_i(s)$ para cada vetor da base.

### Aparato Diferencial Local

Para cada ponto $r(s)$ com $\kappa(s) > 0$, o aparato geométrico é constituído por:

- **Plano Osculador** (vetor normal $B(s)$):
  $$(X - r(s)) \cdot B(s) = 0$$
  Plano que melhor aproxima a curva na vizinhança de $r(s)$ (ordem de contato $\ge 2$). Gerado pela base $\{T(s), N(s)\}$.

- **Plano Normal** (vetor normal $T(s)$):
  $$(X - r(s)) \cdot T(s) = 0$$
  Plano ortogonal à direção de avanço $T(s)$. Gerado pela base $\{N(s), B(s)\}$.

- **Plano Retificante** (vetor normal $N(s)$):
  $$(X - r(s)) \cdot N(s) = 0$$
  Plano ortogonal à aceleração normal. Gerado pela base $\{T(s), B(s)\}$.

- **Reta Tangente**:
  $$L_T(u) = r(s) + u \, T(s), \quad u \in \mathbb{R}$$
  Direção tangencial instantânea da trajetória.

- **Círculo Osculador** (no plano osculador):
  $$\text{Centro: } c(s) = r(s) + \rho(s) N(s), \quad \text{Raio: } \rho(s) = \frac{1}{\kappa(s)}$$
  Círculo com contato de 2ª ordem com a curva em $r(s)$ (compartilha mesma posição, mesma reta tangente e mesma curvatura).

> 📖 Para deduções completas, formulação matricial em Álgebra de Lie $\mathfrak{so}(3)$, estabilização de Gram-Schmidt e referências bibliográficas (do Carmo, Tenenblat, Toponogov, Lancret), consulte [`docs/TEORIA.md`](docs/TEORIA.md).

---

## Referência da CLI

```bash
python3 teorema-fundamental-curvas.py <curvatura> [torcao] [opções]
```

| Argumento / Flag | Tipo | Padrão | Descrição |
|---|:---:|:---:|---|
| `<curvatura>`, `-k`, `--curvatura` | `str` | *Obrigatório* | Expressão de $\kappa(s)$ (ex: `"1"`, `"s"`, `"1/(s+1)"`). |
| `[torcao]`, `-t`, `--torcao` | `str` | `"0"` | Expressão de $\tau(s)$ (ex: `"0"`, `"1"`, `"0.5*s"`). |
| `-i`, `--intervalo` | `float float` | `0.0 6.28` | Limites do comprimento de arco $[s_0, s_1]$ (aceita `pi`, `-pi`). |
| `-n`, `--num-pontos` | `int` | `500` | Amostragem de pontos para discretização. |
| `-o`, `--output` | `str` | *Automático* | Nome do arquivo HTML gerado. |
| `-h`, `--help` | — | — | Ajuda com exemplos detalhados de uso. |

### Códigos de Saída (Exit Codes)
- **`0`**: Sucesso na reconstrução e arquivo HTML gerado.
- **`1`**: Erro matemático ou validação (expressão fora da whitelist, singularidade no domínio, $\kappa(s) < 0$).
- **`2`**: Erro de sintaxe nos argumentos da linha de comando.

---

## Estrutura do Repositório

```
.
├── index.html                      # Aplicação web completa (arquivo único, zero dependências)
├── teorema-fundamental-curvas.py   # Ponto de entrada da CLI em Python
├── requirements.txt                # Dependências Python (NumPy, SciPy, SymPy, Plotly, pytest)
├── src/                            # Motores matemáticos e visuais (CLI)
│   ├── curva_engine.py             # Validação AST, integração ODE/quadratura e classificação
│   └── curva_viz.py                # Visualização dual 2D/3D interativa em Plotly
├── web/                            # Código-fonte da aplicação web
│   ├── template.html               # Template do bundler
│   ├── build.py                    # Script de compilação do index.html
│   ├── css/                        # Estilos da interface web
│   └── js/                         # Motor Magnus SO(3), parser e renderizador Canvas
├── design-system/                  # Design tokens e componentes de interface
├── docs/                           # Documentação complementar
│   ├── TEORIA.md                   # Fundamentação matemática rigorosa e bibliografia
│   └── TEST_INFRA.md               # Arquitetura e matriz da suíte de testes
└── tests/                          # 262 testes automatizados (Python e Node.js)
```

Para recompilar o `index.html` após editar arquivos em `web/` ou `design-system/`:
```bash
python3 web/build.py
```

---

## Testes Automatizados

A suíte conta com **262 testes rigorosos** aprovados com 100% de sucesso, cobrindo:
- Integração de EDOs e conservação de ortonormalidade em $\mathrm{SO}(3)$.
- Quadratura planar em precisão de máquina ($|\|T\| - 1| < 10^{-15}$).
- Paridade numérica e analítica entre os motores Python e JavaScript (`test_js_engine_parity.py`).
- Validação adversarial da whitelist AST e tratamento de singularidades.

Executar os testes:
```bash
# Bateria completa em Python (inclui teste de paridade com o motor JS)
pytest -v

# Testes unitários do motor JavaScript via Node.js
node --test tests/js
```

---

## Licença

Distribuído sob a licença [MIT](LICENSE).
